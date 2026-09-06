'use client';
import { useState } from 'react';
import { adminApi, AdminRecord } from '@/lib/adminApi';
import { ActionSpec, RecordView } from './AdminPrimitives';

const modelOptions = ['gemini-2.5-flash','gemini-2.5-pro','gpt-4o-mini','gpt-4o'];
const providerFor = (model:string) => model.startsWith('gemini') ? 'gemini' : 'openai';
export function ConfigurationEditor({kind,data,confirm}:{kind:'settings'|'ai-config';data:AdminRecord;confirm:(action:ActionSpec)=>void}) {
  const runtime=data.runtime as {revision:number;values:AdminRecord};
  const [values,setValues]=useState<AdminRecord>(runtime.values);
  const [task,setTask]=useState('SUMMARIZATION');
  const [primary,setPrimary]=useState('gemini-2.5-flash');
  const [fallback,setFallback]=useState('gpt-4o-mini');
  const routes=(values.routes || {}) as Record<string,AdminRecord>;
  const defaults=(data.routes || []) as AdminRecord[];
  const field=(key:string,value:unknown)=>setValues(current=>({...current,[key]:value}));
  return <section className="admin-panel space-y-4 p-4">
    <div><h2 className="font-semibold">Cấu hình áp dụng khi chạy</h2><p className="admin-muted mt-1 text-sm">Phiên bản {runtime.revision}. {kind==='settings'?'Chỉ ảnh hưởng đăng ký mới; gói của tài khoản hiện có được giữ nguyên.':'Áp dụng cho yêu cầu mới qua AI Gateway. Lựa chọn model cụ thể trong yêu cầu được ưu tiên; các luồng gọi provider trực tiếp chưa dùng cấu hình này.'}</p></div>
    {kind==='settings'?<div className="flex flex-wrap gap-4"><label className="grid gap-1 text-sm">Đăng ký tài khoản<select value={String(values.registration_enabled)} onChange={e=>field('registration_enabled',e.target.value==='true')}><option value="true">Cho phép</option><option value="false">Tạm dừng</option></select></label><label className="grid gap-1 text-sm">Gói khi đăng ký<select value={String(values.registration_plan)} onChange={e=>field('registration_plan',e.target.value)}>{['free','pro','team','enterprise'].map(plan=><option key={plan}>{plan}</option>)}</select></label></div>:<>
      <div className="flex flex-wrap gap-4"><label className="grid gap-1 text-sm">Số lần thử lại provider chính<input type="number" min={0} max={3} value={Number(values.primary_retries)} onChange={e=>field('primary_retries',Number(e.target.value))}/></label><label className="grid gap-1 text-sm">Timeout mỗi lần gọi (giây)<input type="number" min={10} max={300} value={Number(values.timeout_seconds)} onChange={e=>field('timeout_seconds',Number(e.target.value))}/></label></div>
      <div className="flex flex-wrap items-end gap-3"><label className="grid gap-1 text-sm">Chức năng<select value={task} onChange={e=>setTask(e.target.value)}>{defaults.filter(row=>row.task_type!=='EMBEDDING').map(row=><option key={String(row.task_type)}>{String(row.task_type)}</option>)}</select></label><label className="grid gap-1 text-sm">Model chính<select value={primary} onChange={e=>setPrimary(e.target.value)}>{modelOptions.map(model=><option key={model}>{model}</option>)}</select></label><label className="grid gap-1 text-sm">Model dự phòng<select value={fallback} onChange={e=>setFallback(e.target.value)}>{modelOptions.map(model=><option key={model}>{model}</option>)}</select></label><button onClick={()=>field('routes',{...routes,[task]:{primary_provider:providerFor(primary),primary_model:primary,fallback_provider:providerFor(fallback),fallback_model:fallback}})}>Thêm vào bản chỉnh sửa</button></div>
      {Object.entries(routes).map(([key,route])=><div key={key} className="flex flex-wrap items-center justify-between gap-2 border-t pt-3 text-sm"><span>{key}: {String(route.primary_model)} → {String(route.fallback_model)}</span><button onClick={()=>{const next={...routes};delete next[key];field('routes',next);}}>Dùng mặc định</button></div>)}
    </>}
    <button onClick={()=>confirm({title:'Lưu cấu hình',description:'Thay đổi được áp dụng cho yêu cầu mới và ghi vào nhật ký. Nếu cấu hình đã được người khác sửa, hệ thống sẽ yêu cầu tải lại.',run:({reason})=>adminApi.mutate(kind,{values,revision:runtime.revision,reason},'PATCH')})}>Xem xác nhận và lưu</button>
    <details><summary className="cursor-pointer text-sm">Giá trị sẽ lưu</summary><RecordView data={values}/></details>
  </section>;
}
