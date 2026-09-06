from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from app.models.admin_configuration import AdminConfiguration
from app.services.admin.audit_service import record_audit
from app.services.ai.model_router import model_router, ModelRoute
from app.services.ai.types import AITaskType, AIProviderType

class StrictModel(BaseModel):
    model_config=ConfigDict(extra='forbid')

class SystemValues(StrictModel):
    registration_enabled:bool=True
    registration_plan:Literal['free','pro','team','enterprise']='pro'

class RouteValues(StrictModel):
    primary_provider:Literal['gemini','openai']
    primary_model:str
    fallback_provider:Literal['gemini','openai']
    fallback_model:str
    @model_validator(mode='after')
    def known_models(self):
        allowed={'gemini':{'gemini-2.5-flash','gemini-2.5-pro'},'openai':{'gpt-4o-mini','gpt-4o'}}
        if self.primary_model not in allowed[self.primary_provider] or self.fallback_model not in allowed[self.fallback_provider]:
            raise ValueError('Chọn model đã được tích hợp cho nhà cung cấp này.')
        return self

class AIValues(StrictModel):
    primary_retries:int=Field(1,ge=0,le=3)
    timeout_seconds:int=Field(120,ge=10,le=300)
    routes:dict[AITaskType,RouteValues]=Field(default_factory=dict)

SCHEMAS={'system':SystemValues,'ai':AIValues}

async def read_configuration(db,key):
    row=await db.get(AdminConfiguration,key)
    values=SCHEMAS[key].model_validate(row.values_json if row else {}).model_dump(mode='json')
    return {'revision':row.revision if row else 0,'values':values}

async def write_configuration(db,key,values,revision,actor,reason,request=None):
    try:values=SCHEMAS[key].model_validate(values).model_dump(mode='json')
    except ValidationError:
        raise HTTPException(422,'Cấu hình không hợp lệ: kiểm tra trường, giới hạn và model được hỗ trợ.')
    before=await read_configuration(db,key)
    if before['revision']!=revision:raise HTTPException(409,'Cấu hình đã thay đổi; hãy tải lại trước khi lưu.')
    try:
        if revision==0:
            db.add(AdminConfiguration(key=key,values_json=values,revision=1))
            await db.flush()
        else:
            result=await db.execute(update(AdminConfiguration).where(AdminConfiguration.key==key,AdminConfiguration.revision==revision).values(values_json=values,revision=revision+1))
            if result.rowcount!=1:raise HTTPException(409,'Cấu hình đã thay đổi; hãy tải lại trước khi lưu.')
        await record_audit(db,actor,'AI_MODEL_CHANGE' if key=='ai' else 'SYSTEM_SETTING_CHANGE','configuration',key,before['values'],values,reason,request)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409,'Cấu hình đã thay đổi; hãy tải lại trước khi lưu.')
    return {'revision':revision+1,'values':values}

async def gateway_config(db,request):
    values=(await read_configuration(db,'ai'))['values']
    route=model_router.resolve_route(request)
    override=values['routes'].get(request.task_type.value)
    if override and not (request.preferred_provider and request.preferred_model):
        route=ModelRoute(AIProviderType(override['primary_provider']),override['primary_model'],AIProviderType(override['fallback_provider']),override['fallback_model'])
    return values,route
