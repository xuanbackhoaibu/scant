from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select
from test_admin_core import ctx, auth
from app.models.entities import User, AuthAccount
from app.services.auth.google_auth_service import GoogleTokenData, GoogleUserInfo, google_auth_service
from app.services.data.google_sheets_service import GoogleSheetsService

SCOPE = 'https://www.googleapis.com/auth/spreadsheets'

def grant(scope=SCOPE):
    return GoogleTokenData(user_info=GoogleUserInfo(google_sub='data-account',email='data@example.com',email_verified=True,name='Data'),access_token='data-token',refresh_token='refresh-data',expires_in=3600,scope=scope)

@pytest.mark.asyncio
async def test_connect_is_authenticated_and_bound_to_owner(ctx,monkeypatch):
    c,f=ctx
    exchange=AsyncMock(return_value=(True,grant(),None))
    monkeypatch.setattr(google_auth_service,'exchange_code',exchange)
    body={'code':'code','redirect_uri':'http://localhost/callback','expected_user_id':'user'}
    assert (await c.post('/api/v1/auth/google/connect',json=body)).status_code==401
    assert (await c.post('/api/v1/auth/google/connect',json=body,headers=auth('admin'))).status_code==409
    exchange.assert_not_called()
    response=await c.post('/api/v1/auth/google/connect',json=body,headers=auth('user'))
    assert response.status_code==200,response.text
    assert 'access_token' not in response.json()
    async with f() as db:
        assert (await db.get(User,'user')).google_sub is None
        account=await db.scalar(select(AuthAccount).where(AuthAccount.provider=='google_data'))
        assert account.user_id=='user'
        token,error=await GoogleSheetsService.get_valid_access_token(await db.get(User,'user'),db)
        assert (token,error)==('data-token',None)
    status=await c.get('/api/v1/auth/google/connection',headers=auth('user'))
    assert status.json()['connected'] is True
    assert (await c.get('/api/v1/auth/google/connection',headers=auth('admin'))).json()['connected'] is False

@pytest.mark.asyncio
async def test_missing_sheets_permission_does_not_save_credentials(ctx,monkeypatch):
    c,f=ctx
    monkeypatch.setattr(google_auth_service,'exchange_code',AsyncMock(return_value=(True,grant('openid email profile'),None)))
    response=await c.post('/api/v1/auth/google/connect',headers=auth('user'),json={'code':'code','redirect_uri':'http://localhost/callback','expected_user_id':'user'})
    assert response.status_code==403
    async with f() as db:assert await db.scalar(select(AuthAccount)) is None

@pytest.mark.asyncio
async def test_basic_login_preserves_existing_sheets_grant(ctx,monkeypatch):
    c,f=ctx
    async with f() as db:
        user=await db.get(User,'user');user.email='user@example.com';user.google_sub='login-account'
        db.add(AuthAccount(user_id='user',provider='google',provider_account_id='login-account',email=user.email,access_token='existing-data',refresh_token='existing-refresh',scopes=SCOPE,token_expiry=datetime.now(timezone.utc)+timedelta(hours=1)))
        await db.commit()
    data=grant('openid email profile');data.user_info=GoogleUserInfo(google_sub='login-account',email='user@example.com',email_verified=True,name='User')
    monkeypatch.setattr(google_auth_service,'exchange_code',AsyncMock(return_value=(True,data,None)))
    response=await c.post('/api/v1/auth/google/code',json={'code':'code','redirect_uri':'http://localhost/callback'})
    assert response.status_code==200,response.text
    async with f() as db:
        account=await db.scalar(select(AuthAccount).where(AuthAccount.provider=='google'))
        assert account.access_token=='existing-data'
        assert account.refresh_token=='existing-refresh'
        assert account.scopes==SCOPE

@pytest.mark.asyncio
async def test_refresh_sets_future_expiry_and_reuses_new_token(ctx,monkeypatch):
    from app.core.config import settings
    c,f=ctx
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_ID','test-client')
    monkeypatch.setattr(settings,'GOOGLE_CLIENT_SECRET','test-secret')
    class Response:
        status_code=200
        def json(self):return {'access_token':'renewed-token','expires_in':3600}
    post=AsyncMock(return_value=Response())
    monkeypatch.setattr('app.services.data.google_sheets_service.httpx.AsyncClient.post',post)
    async with f() as db:
        db.add(AuthAccount(user_id='user',provider='google_data',provider_account_id='data',email='data@example.com',scopes=SCOPE,access_token='expired',refresh_token='refresh',token_expiry=datetime.now(timezone.utc)-timedelta(hours=1)))
        await db.commit()
        user=await db.get(User,'user')
        assert await GoogleSheetsService.get_valid_access_token(user,db)==('renewed-token',None)
        assert await GoogleSheetsService.get_valid_access_token(user,db)==('renewed-token',None)
        post.assert_awaited_once()
