"""Explicit data consent, separate from Google sign-in credentials."""
from datetime import datetime,timezone,timedelta
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,case,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User,AuthAccount
from app.services.auth.google_auth_service import google_auth_service

router=APIRouter()
SHEETS_SCOPE='https://www.googleapis.com/auth/spreadsheets'

class ConnectRequest(BaseModel):
    code:str=Field(min_length=1,max_length=4096)
    redirect_uri:str
    expected_user_id:str

@router.get('/google/connection')
async def connection_status(user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    accounts=(await db.scalars(select(AuthAccount).where(AuthAccount.user_id==user.id,AuthAccount.provider.in_(['google_data','google'])).order_by(case((AuthAccount.provider=='google_data',0),else_=1)))).all()
    for account in accounts:
        if SHEETS_SCOPE not in (account.scopes or '').split():continue
        expiry=account.token_expiry
        valid=not expiry or expiry.replace(tzinfo=expiry.tzinfo or timezone.utc)>datetime.now(timezone.utc)
        if account.refresh_token or (account.access_token and valid):
            return {'connected':True,'email':account.email,'scope':'sheets','source':'dedicated' if account.provider=='google_data' else 'existing'}
    return {'connected':False,'email':None,'scope':'sheets'}

@router.post('/google/connect')
async def connect(body:ConnectRequest,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    if body.expected_user_id!=user.id:raise HTTPException(409,'Tài khoản đã thay đổi. Hãy bắt đầu kết nối lại.')
    valid,data,error=await google_auth_service.exchange_code(body.code,body.redirect_uri)
    if not valid or not data or not data.user_info or not data.user_info.email_verified:
        raise HTTPException(400,'Không xác minh được tài khoản Google. Hãy thử kết nối lại.')
    if SHEETS_SCOPE not in (data.scope or '').split() or not data.access_token:
        raise HTTPException(403,'Bạn chưa cấp quyền Google Sheets. Đăng nhập ứng dụng vẫn được giữ nguyên.')
    # Serialize creation/reconnection for this owner without changing login identity.
    await db.execute(update(User).where(User.id==user.id).values(id=User.id))
    account=await db.scalar(select(AuthAccount).where(AuthAccount.user_id==user.id,AuthAccount.provider=='google_data'))
    if not account:
        account=AuthAccount(user_id=user.id,provider='google_data',provider_account_id=data.user_info.google_sub,email=data.user_info.email)
        db.add(account)
    elif account.provider_account_id!=data.user_info.google_sub:
        account.refresh_token=None
    account.provider_account_id=data.user_info.google_sub
    account.email=data.user_info.email
    account.access_token=data.access_token
    if data.refresh_token:account.refresh_token=data.refresh_token
    account.token_expiry=datetime.now(timezone.utc)+timedelta(seconds=data.expires_in or 3600)
    account.scopes=data.scope
    await db.flush()
    return {'connected':True,'email':account.email,'scope':'sheets'}
