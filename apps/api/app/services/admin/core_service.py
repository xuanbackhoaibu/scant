from datetime import datetime, timezone
from sqlalchemy import select, func, update, or_
from fastapi import HTTPException
from app.models.entities import User, Project, Document, Job, UserQuota, AuditLog, AIUsageEvent
from app.core.admin_access import admin_role
from app.services.admin.audit_service import record_audit, safe_value
from app.services.admin.plan_service import change_user_plan, next_month
from app.services.admin.query_service import user_dict, job_dict, usage, list_jobs, list_audit, page_result, utc
from app.services.billing.plan_definitions import PLANS


async def get_user(db,user_id):
    user=await db.get(User,user_id)
    if not user: raise HTTPException(404,'Không tìm thấy tài khoản.')
    return user


async def update_user(db,actor,user_id,changes,reason,request=None):
    # Serialize authorization transitions across administrators on both PostgreSQL
    # (row locks) and SQLite (writer lock), before loading either target or actor.
    await db.execute(update(User).where(User.is_superuser.is_(True)).values(is_superuser=User.is_superuser,updated_at=User.updated_at).execution_options(synchronize_session=False))
    await db.refresh(actor)
    if not actor.is_active or admin_role(actor)=='user':raise HTTPException(403,'Quyền quản trị đã thay đổi; hãy tải lại phiên.')
    user=(await db.execute(select(User).where(User.id==user_id).with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()
    if not user:raise HTTPException(404,'Không tìm thấy tài khoản.')
    if admin_role(actor)!='super_admin' and (admin_role(user)!='user' or 'role' in changes):
        raise HTTPException(403,'Chỉ Super Admin được thay đổi tài khoản quản trị hoặc phân quyền.')
    if user.id==actor.id and (changes.get('is_active') is False or ('role' in changes and changes['role']!=admin_role(actor))):
        raise HTTPException(409,'Không thể tự khóa hoặc thay đổi quyền tài khoản đang đăng nhập.')
    if 'plan' in changes:
        await change_user_plan(db,user,changes.pop('plan'),actor,reason,request)
    if 'role' in changes:
        value=changes.pop('role');old={'role':admin_role(user)}
        # Never allow deleting the final super administrator, even across stale requests.
        if user.is_superuser and value!='super_admin':
            others=await db.scalar(select(func.count()).select_from(User).where(User.is_superuser.is_(True),User.is_active.is_(True),User.id!=user.id))
            if not others:raise HTTPException(409,'Cần giữ ít nhất một Super Admin hoạt động.')
        user.role='admin' if value in ['admin','super_admin'] else 'user'
        user.is_superuser=value=='super_admin'
        await record_audit(db,actor,'ROLE_CHANGE','user',user.id,old,{'role':admin_role(user)},reason,request)
    if 'is_active' in changes:
        value=changes['is_active']
        if user.is_superuser and not value:
            others=await db.scalar(select(func.count()).select_from(User).where(User.is_superuser.is_(True),User.is_active.is_(True),User.id!=user.id))
            if not others:raise HTTPException(409,'Cần giữ ít nhất một Super Admin hoạt động.')
        before={'is_active':user.is_active};user.is_active=value
        await record_audit(db,actor,'USER_UNLOCK' if value else 'USER_LOCK','user',user.id,before,{'is_active':value},reason,request)
    await db.flush()
    return user_dict(user)


def quota_dict(q,user):
    limit=q.monthly_token_limit;used=q.tokens_used_this_month
    ratio=max(used/limit if limit else (1 if used else 0),q.cost_usd_this_month/q.monthly_cost_limit_usd if q.monthly_cost_limit_usd else (1 if q.cost_usd_this_month else 0))
    return {'id':q.id,'user_id':user.id,'user_name':user.name,'email':user.email,'plan':user.plan,
        'monthly_token_limit':limit,'monthly_cost_limit_usd':q.monthly_cost_limit_usd,
        'tokens_used_this_month':used,'cost_usd_this_month':q.cost_usd_this_month,
        'remaining_tokens':max(0,limit-used),'reset_at':utc(q.reset_at),
        'status':'exceeded' if ratio>=1 else 'near_limit' if ratio>=.8 else 'normal'}


async def list_quotas(db,search=None,page=1,page_size=25,plan=None,status=None):
    q=select(UserQuota,User).join(User,UserQuota.user_id==User.id)
    f=[]
    if search:f.append(or_(User.email.ilike(f'%{search}%'),User.name.ilike(f'%{search}%')))
    if plan:f.append(User.plan==plan)
    exceeded=or_(UserQuota.tokens_used_this_month>=UserQuota.monthly_token_limit,UserQuota.cost_usd_this_month>=UserQuota.monthly_cost_limit_usd)
    near=or_(UserQuota.tokens_used_this_month>=UserQuota.monthly_token_limit*.8,UserQuota.cost_usd_this_month>=UserQuota.monthly_cost_limit_usd*.8)
    if status=='exceeded':f.append(exceeded)
    elif status=='near_limit':f.extend([near,~exceeded])
    elif status=='normal':f.append(~near)
    q=q.where(*f)
    total=await db.scalar(select(func.count()).select_from(q.subquery()))
    rows=(await db.execute(q.order_by(UserQuota.updated_at.desc(),UserQuota.id).offset((page-1)*page_size).limit(page_size))).all()
    return page_result([quota_dict(quota,user) for quota,user in rows],total,page,page_size)


async def update_quota(db,actor,user_id,changes,reason,request=None):
    user=await get_user(db,user_id)
    if admin_role(actor)!='super_admin' and admin_role(user)!='user':raise HTTPException(403,'Chỉ Super Admin được chỉnh hạn mức quản trị viên.')
    q=(await db.execute(select(UserQuota).where(UserQuota.user_id==user_id).with_for_update())).scalar_one_or_none()
    if not q:
        p=PLANS.get(user.plan,PLANS['free']);q=UserQuota(user_id=user_id,monthly_token_limit=p.monthly_tokens_limit,monthly_cost_limit_usd=p.monthly_ai_budget_usd,tokens_used_this_month=0,cost_usd_this_month=0,reset_at=next_month());db.add(q);await db.flush()
    before=quota_dict(q,user)
    for key in ['monthly_token_limit','monthly_cost_limit_usd']:
        if key in changes:setattr(q,key,changes[key])
    if changes.get('reset'):
        q.tokens_used_this_month=0;q.cost_usd_this_month=0;q.reset_at=next_month()
    after=quota_dict(q,user)
    await record_audit(db,actor,'QUOTA_CHANGE','user',user.id,before,after,reason,request)
    return after


async def user_detail(db,user_id,start=None,end=None):
    user=await get_user(db,user_id)
    q=(await db.execute(select(UserQuota).where(UserQuota.user_id==user_id))).scalar_one_or_none()
    projects=(await db.execute(select(Project.id,Project.name,Project.type,Project.created_at).where(Project.user_id==user_id).order_by(Project.created_at.desc()).limit(25))).mappings().all()
    docs=(await db.execute(select(Document.id,Document.project_id,Document.document_type,Document.token_count,Document.created_at).join(Project,Document.project_id==Project.id).where(Project.user_id==user_id).order_by(Document.created_at.desc()).limit(25))).mappings().all()
    usage_data=await usage(db,start,end,user_id=user_id,page_size=10)
    jobs=await list_jobs(db,user_id=user_id,page_size=25)
    audit=await list_audit(db,target=user_id,page_size=25)
    from app.models.admin_billing import Payment
    payment_columns = [c for c in Payment.__table__.columns if c.name != 'order_code']
    payments = (await db.execute(select(*payment_columns).where(Payment.user_id==user_id).order_by(Payment.created_at.desc()).limit(25))).mappings().all()
    return {'user':user_dict(user),'quota':quota_dict(q,user) if q else None,'usage':usage_data,
        'projects':safe_value([dict(p) for p in projects]),'documents':safe_value([dict(d) for d in docs]),
        'jobs':jobs['items'],'payments':safe_value([dict(p) for p in payments]),'audit_logs':audit['items'],
        'limits':{'projects':25,'documents':25,'jobs':25,'audit_logs':25},
        'billing_href':f'/admin/payments?user_id={user_id}'}


def job_actions(job):
    report_id=(job.metadata_json or {}).get('report_id') or (job.payload_json or {}).get('report_id')
    supported=bool(report_id and job.project_id)
    return {'cancel':supported and job.status in ['pending','queued','running','paused','retrying'],
        'retry':False,'reason':'Chạy lại chưa khả dụng: worker hiện chưa có cơ chế replay bảo đảm không tạo nội dung trùng.','cancellation':'Yêu cầu hủy được kiểm tra tại checkpoint, không ngắt ngay lời gọi AI đang chạy.'}


async def job_detail(db,job_id):
    job=await db.get(Job,job_id)
    if not job:raise HTTPException(404,'Không tìm thấy tác vụ.')
    result=job_dict(job)
    result['actions']=job_actions(job)
    result['timeline']=[{'status':'created','time':utc(job.created_at)},{'status':job.status,'time':utc(job.updated_at)}]
    result['unavailable']=['Job chưa liên kết usage events nên model, token, chi phí và thời lượng chính xác chưa khả dụng.','Chỉ hiển thị metadata; payload và nội dung tài liệu không được trả về.']
    return result


async def job_action(db,actor,job_id,action,reason,request=None):
    job=await db.get(Job,job_id)
    if not job:raise HTTPException(404,'Không tìm thấy tác vụ.')
    if action not in ['cancel','retry'] or not job_actions(job).get(action):raise HTTPException(409,job_actions(job)['reason'] if action=='retry' else 'Trạng thái hoặc loại tác vụ không hỗ trợ thao tác này.')
    before=job_dict(job)
    result=await db.execute(update(Job).where(Job.id==job_id,Job.status==job.status).values(status='cancelled',status_message='Admin requested cancellation',updated_at=datetime.now(timezone.utc)).execution_options(synchronize_session=False))
    if result.rowcount!=1:raise HTTPException(409,'Tác vụ đã đổi trạng thái; vui lòng tải lại.')
    await record_audit(db,actor,'JOB_CANCEL','job',job.id,before,{'status':'cancelled'},reason,request)
    return {'id':job_id,'status':'cancelled','message':'Đã yêu cầu hủy tại checkpoint tiếp theo.'}


async def search(db,query):
    needle=f'%{query}%'
    users=(await db.execute(select(User.id,User.name,User.email).where(or_(User.name.ilike(needle),User.email.ilike(needle))).limit(6))).mappings().all()
    projects=(await db.execute(select(Project.id,Project.name).where(Project.name.ilike(needle)).limit(6))).mappings().all()
    jobs=(await db.execute(select(Job.id,Job.job_type,Job.status).where(Job.id.ilike(needle)).limit(6))).mappings().all()
    from app.models.admin_billing import Payment
    payments=(await db.execute(select(Payment.id,Payment.user_id,Payment.plan,Payment.status).where(or_(Payment.id.ilike(needle),Payment.user_id.ilike(needle),Payment.provider_transaction_id.ilike(needle))).limit(6))).mappings().all()
    return {'users':[dict(r) for r in users],'projects':[dict(r) for r in projects],'jobs':[dict(r) for r in jobs],'payments':[dict(r) for r in payments]}
