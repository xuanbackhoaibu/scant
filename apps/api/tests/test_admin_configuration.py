import pytest
from test_admin_core import ctx, auth
from app.models.entities import AuditLog
from sqlalchemy import select

@pytest.mark.asyncio
async def test_config_permissions_revision_validation_and_audit(ctx):
    c,f=ctx
    url='/api/v1/admin/settings'
    body={'revision':0,'reason':'Disable new registrations','values':{'registration_enabled':False,'registration_plan':'pro'}}
    assert (await c.patch(url,headers=auth('admin'),json=body)).status_code==403
    initial=await c.get(url,headers=auth('root'))
    assert initial.json()['runtime']['revision']==0
    changed=await c.patch(url,headers=auth('root'),json=body)
    assert changed.status_code==200,changed.text
    assert changed.json()['revision']==1
    assert (await c.patch(url,headers=auth('root'),json=body)).status_code==409
    assert (await c.post('/api/v1/auth/register',json={'email':'new@example.com','name':'New','password':'Password123!'})).status_code==403
    bad={'revision':1,'reason':'Unsafe unknown field','values':{'api_key':'secret'}}
    assert (await c.patch(url,headers=auth('root'),json=bad)).status_code==422
    async with f() as db:
        logs=(await db.scalars(select(AuditLog).where(AuditLog.action=='SYSTEM_SETTING_CHANGE'))).all()
        assert len(logs)==1
        assert logs[0].details_json['after']['registration_enabled'] is False

@pytest.mark.asyncio
async def test_ai_configuration_is_used_by_runtime(ctx):
    from app.services.admin.configuration_service import gateway_config
    from app.services.ai.types import AIRequest, AITaskType
    c,f=ctx
    request=AIRequest(task_type=AITaskType.SUMMARIZATION,prompt='test')
    body={'revision':0,'reason':'Use approved OpenAI route','values':{'primary_retries':0,'timeout_seconds':30,'routes':{'SUMMARIZATION':{'primary_provider':'openai','primary_model':'gpt-4o-mini','fallback_provider':'gemini','fallback_model':'gemini-2.5-flash'}}}}
    saved=await c.patch('/api/v1/admin/ai-config',headers=auth('root'),json=body)
    assert saved.status_code==200,saved.text
    async with f() as db:
        config,route=await gateway_config(db,request)
        assert config['primary_retries']==0
        assert route.primary_model=='gpt-4o-mini'
    body['revision']=1
    body['values']['routes']['SUMMARIZATION']['primary_model']='unknown-model'
    assert (await c.patch('/api/v1/admin/ai-config',headers=auth('root'),json=body)).status_code==422

@pytest.mark.asyncio
async def test_gateway_records_usage_without_replaying_success(ctx,monkeypatch):
    from unittest.mock import AsyncMock
    from app.services.ai.gateway import ai_gateway
    from app.services.ai.types import AIRequest,AITaskType
    from app.models.entities import AIUsageEvent,UserQuota
    c,f=ctx
    monkeypatch.setattr('app.core.database.AsyncSessionLocal',f)
    generate=AsyncMock(return_value={'text':'verified','usage':{'prompt_tokens':120,'completion_tokens':30}})
    monkeypatch.setattr('app.services.ai.gemini_provider.GeminiProvider.generate',generate)
    result=await ai_gateway.execute(AIRequest(task_type=AITaskType.SUMMARIZATION,prompt='test',user_id='user'))
    assert result.text=='verified'
    assert generate.await_count==1
    async with f() as db:
        event=(await db.scalars(select(AIUsageEvent))).one()
        quota=(await db.scalars(select(UserQuota).where(UserQuota.user_id=='user'))).one()
        assert event.total_tokens==150
        assert quota.tokens_used_this_month==150

@pytest.mark.asyncio
async def test_offline_demo_is_not_counted_as_live_usage(ctx,monkeypatch):
    from unittest.mock import AsyncMock
    from app.services.ai.gateway import ai_gateway
    from app.services.ai.types import AIRequest,AITaskType
    from app.models.entities import AIUsageEvent
    _,f=ctx
    monkeypatch.setattr('app.core.database.AsyncSessionLocal',f)
    monkeypatch.setattr('app.services.ai.gemini_provider.GeminiProvider.generate',AsyncMock(return_value={'text':'demo','is_demo':True}))
    result=await ai_gateway.execute(AIRequest(task_type=AITaskType.SUMMARIZATION,prompt='test',user_id='user'))
    assert result.is_demo
    async with f() as db:assert not (await db.scalars(select(AIUsageEvent))).all()

def test_provider_usage_zero_and_gemini_long_context_estimates():
    from app.services.ai.gateway import ai_gateway
    from app.services.ai.types import AIRequest,AITaskType
    from app.services.ai.model_router import model_router
    request=AIRequest(task_type=AITaskType.SUMMARIZATION,prompt='nonempty')
    response=ai_gateway._build_response(request,'gemini','gemini-2.5-flash',{'text':'nonempty','usage':{'prompt_tokens':0,'completion_tokens':0}},1,False)
    assert response.usage.total_tokens==0
    assert model_router.calculate_cost('gemini-2.5-flash',1_000_000,1_000_000)==2.8
    assert model_router.calculate_cost('gemini-2.5-pro',200_000,1000)==.26
    assert model_router.calculate_cost('gemini-2.5-pro',200_001,1000)==.5150025

@pytest.mark.asyncio
async def test_authenticated_call_inherits_trusted_usage_identity(ctx,monkeypatch):
    from fastapi import FastAPI,Depends
    from httpx import AsyncClient,ASGITransport
    from unittest.mock import AsyncMock
    from app.core.database import get_db
    from app.api.deps import get_current_user
    from app.models.entities import AIUsageEvent
    from app.services.ai.gateway import ai_gateway
    from app.services.ai.types import AIRequest,AITaskType
    from app.core.usage_context import usage_user_id
    _,f=ctx
    api=FastAPI()
    async def db_dependency():
        async with f() as db:yield db
    api.dependency_overrides[get_db]=db_dependency
    @api.post('/generate')
    async def generate(user=Depends(get_current_user)):
        return await ai_gateway.execute(AIRequest(task_type=AITaskType.SUMMARIZATION,prompt='test'))
    monkeypatch.setattr('app.core.database.AsyncSessionLocal',f)
    monkeypatch.setattr('app.services.ai.gemini_provider.GeminiProvider.generate',AsyncMock(return_value={'text':'ok','usage':{'prompt_tokens':10,'completion_tokens':2}}))
    token=usage_user_id.set(None)
    try:
        async with AsyncClient(transport=ASGITransport(app=api),base_url='http://test') as c:
            assert (await c.post('/generate',headers=auth('user'))).status_code==200
        async with f() as db:
            event=(await db.scalars(select(AIUsageEvent))).one()
            assert event.user_id=='user'
    finally:usage_user_id.reset(token)

@pytest.mark.asyncio
async def test_gateway_respects_admin_quota_before_provider_call(ctx,monkeypatch):
    from unittest.mock import AsyncMock
    from app.services.ai.gateway import ai_gateway
    from app.services.ai.types import AIRequest,AITaskType
    c,f=ctx
    assert (await c.patch('/api/v1/admin/quotas/user',headers=auth('admin'),json={'monthly_token_limit':0,'reason':'Suspend AI allocation'})).status_code==200
    monkeypatch.setattr('app.core.database.AsyncSessionLocal',f)
    generate=AsyncMock()
    monkeypatch.setattr('app.services.ai.gemini_provider.GeminiProvider.generate',generate)
    with pytest.raises(RuntimeError,match='quota exceeded'):
        await ai_gateway.execute(AIRequest(task_type=AITaskType.SUMMARIZATION,prompt='test',user_id='user'))
    generate.assert_not_awaited()
