from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel, Field, ConfigDict, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.admin_access import require_admin, require_super_admin, admin_role
from app.models.entities import User
from app.services.admin import query_service as queries, core_service as core

router=APIRouter(prefix='/admin',tags=['admin'])
verify_admin_access=require_admin

class Reason(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    reason:str=Field(min_length=3,max_length=1000)

class UserUpdateRequest(Reason):
    is_active:Optional[bool]=None
    plan:Optional[Literal['free','pro','team','enterprise']]=None
    plan_tier:Optional[Literal['free','pro','team','enterprise']]=None
    role:Optional[Literal['user','admin','super_admin']]=None
    @model_validator(mode='after')
    def changes(self):
        if self.plan and self.plan_tier and self.plan!=self.plan_tier:raise ValueError('Conflicting plans')
        if not any(x is not None for x in [self.is_active,self.plan,self.plan_tier,self.role]):raise ValueError('No changes')
        return self

class QuotaUpdate(Reason):
    monthly_token_limit:Optional[int]=Field(default=None,ge=0,le=10**12)
    monthly_cost_limit_usd:Optional[float]=Field(default=None,ge=0,le=10**7,allow_inf_nan=False)
    reset:bool=False
    @model_validator(mode='after')
    def changes(self):
        if not self.reset and self.monthly_token_limit is None and self.monthly_cost_limit_usd is None:raise ValueError('No changes')
        return self

@router.get('/session')
async def session(user:User=Depends(require_admin)):
    return queries.user_dict(user)|{'permissions':['read','users','quota','jobs','audit']+(['configuration','roles','billing'] if user.is_superuser else [])}

@router.get('/overview')
@router.get('/dashboard')
async def overview(start:Optional[str]=Query(None,alias='from'),end:Optional[str]=Query(None,alias='to'),user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await queries.overview(db,start,end)

@router.get('/users')
async def users(search:Optional[str]=Query(None,max_length=200),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),role:Optional[str]=None,plan:Optional[str]=None,status:Optional[str]=None,start:Optional[str]=Query(None,alias='from'),end:Optional[str]=Query(None,alias='to'),sort:str='created_at',order:Literal['asc','desc']='desc',user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await queries.list_users(db,search,page,page_size,role,plan,status,start,end,sort,order)

@router.get('/users/{user_id}')
async def user_detail(user_id:str,start:Optional[str]=Query(None,alias='from'),end:Optional[str]=Query(None,alias='to'),user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await core.user_detail(db,user_id,start,end)

@router.patch('/users/{user_id}')
async def update_user(user_id:str,body:UserUpdateRequest,request:Request,user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    changes=body.model_dump(exclude_none=True,exclude={'reason','plan_tier'})
    if body.plan_tier:changes['plan']=body.plan_tier
    return await core.update_user(db,user,user_id,changes,body.reason,request)

@router.get('/usage')
async def usage(start:Optional[str]=Query(None,alias='from'),end:Optional[str]=Query(None,alias='to'),provider:Optional[str]=None,model:Optional[str]=None,feature:Optional[str]=None,user_id:Optional[str]=None,page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await queries.usage(db,start,end,provider,model,feature,user_id,page,page_size)

@router.get('/quotas')
async def quotas(search:Optional[str]=Query(None,max_length=200),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),plan:Optional[str]=None,status:Optional[str]=None,user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await core.list_quotas(db,search,page,page_size,plan,status)

@router.patch('/quotas/{user_id}')
async def quota_update(user_id:str,body:QuotaUpdate,request:Request,user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await core.update_quota(db,user,user_id,body.model_dump(exclude_none=True,exclude={'reason'}),body.reason,request)

@router.get('/jobs')
async def jobs(search:Optional[str]=Query(None,max_length=200),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),status:Optional[str]=None,job_type:Optional[str]=None,user_id:Optional[str]=None,start:Optional[str]=Query(None,alias='from'),end:Optional[str]=Query(None,alias='to'),sort:str='created_at',order:Literal['asc','desc']='desc',user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await queries.list_jobs(db,search,page,page_size,status,job_type,user_id,start,end,sort,order)

@router.get('/jobs/{job_id}')
async def job_detail(job_id:str,user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await core.job_detail(db,job_id)

@router.post('/jobs/{job_id}/{action}')
async def job_action(job_id:str,action:Literal['cancel','retry'],body:Reason,request:Request,user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await core.job_action(db,user,job_id,action,body.reason,request)

@router.get('/audit-logs')
async def audit_logs(search:Optional[str]=Query(None,max_length=200),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),action:Optional[str]=None,actor:Optional[str]=None,target:Optional[str]=None,start:Optional[str]=Query(None,alias='from'),end:Optional[str]=Query(None,alias='to'),user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await queries.list_audit(db,search,page,page_size,action,actor,target,start,end)

@router.get('/search')
async def search(q:str=Query(min_length=2,max_length=100),user:User=Depends(require_admin),db:AsyncSession=Depends(get_db)):
    return await core.search(db,q)

from app.api.v1.admin_operations import router as operations_router
from app.api.v1.admin_billing import router as billing_router
router.include_router(operations_router)
router.include_router(billing_router)
