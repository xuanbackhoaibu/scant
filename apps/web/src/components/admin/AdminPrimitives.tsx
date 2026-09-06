'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { AdminRecord } from '@/lib/adminApi';

export function display(value: unknown): string {
  if (value === null || value === undefined) return 'Chưa có dữ liệu';
  if (typeof value === 'boolean') return value ? 'Có' : 'Không';
  if (typeof value === 'number') return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 5 }).format(value);
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
export const labels: Record<string, string> = { average_latency_ms:'Độ trễ trung bình (ms)', success_rate:'Thành công (%)', error_rate:'Lỗi (%)', tokens_used_this_month:'Token đã dùng trong tháng', cost_usd_this_month:'Chi phí tháng (USD)', remaining_tokens:'Token còn lại', actor_name:'Người thao tác', resource_type:'Loại đối tượng', resource_id:'Đối tượng', date:'Ngày', id:'ID', name:'Tên', email:'Email', user_id:'Người dùng', user_name:'Tên người dùng', user_email:'Email', owner_email:'Chủ sở hữu', role:'Vai trò', plan:'Gói', is_active:'Hoạt động', created_at:'Ngày tạo', updated_at:'Cập nhật', last_active:'Hoạt động cuối', projects_count:'Dự án', documents_count:'Tài liệu', reports_count:'Báo cáo', jobs_count:'Jobs', total_tokens:'Tổng token', input_tokens:'Input token', output_tokens:'Output token', cost_usd:'Chi phí (USD)', estimated_cost_usd:'Chi phí ước tính (USD)', status:'Trạng thái', job_type:'Loại job', progress_percent:'Tiến độ (%)', project_id:'Dự án', title:'Tên', document_type:'Loại tài liệu', file_type:'Định dạng', file_size:'Dung lượng (byte)', storage_bytes:'Lưu trữ (byte)', is_parsed:'Đã phân tích', token_count:'Token', category:'Danh mục', visibility:'Hiển thị', version:'Phiên bản', usage_count:'Lượt dùng', is_system:'Mẫu hệ thống', is_public:'Công khai', trigger_type:'Kích hoạt', last_run_at:'Lần chạy cuối', next_run_at:'Lần chạy tiếp', amount:'Số tiền', currency:'Tiền tệ', provider:'Nhà cung cấp', model:'Mô hình', feature:'Chức năng', requests:'Yêu cầu', action:'Thao tác', target_type:'Loại đối tượng', target_id:'Đối tượng', actor_user_id:'Người thao tác', details_json:'Nội dung thay đổi', ip_address:'Địa chỉ IP', monthly_token_limit:'Giới hạn token/tháng', monthly_cost_limit_usd:'Giới hạn USD/tháng', tokens_used:'Token đã dùng', cost_used_usd:'USD đã dùng', reset_at:'Ngày đặt lại', paid_at:'Thanh toán lúc', started_at:'Bắt đầu', ended_at:'Kết thúc', provider_session_id:'Mã phiên nhà cung cấp', provider_transaction_id:'Mã giao dịch nhà cung cấp', original_name:'Tên tệp', payment_id:'Thanh toán', checkout_amount:'Giá thanh toán', checkout_currency:'Tiền tệ', provider_status:'Trạng thái nhà cung cấp', read_only_reason:'Chế độ chỉ đọc', reason:'Lý do', before:'Trước thay đổi', after:'Sau thay đổi', unavailable:'Chưa có dữ liệu', writable:'Cho phép chỉnh sửa', period:'Kỳ báo cáo', summary:'Tổng hợp', metrics:'Chỉ số', limits:'Giới hạn', features:'Tính năng', configured:'Đã cấu hình', latency_ms:'Độ trễ (ms)', checked_at:'Kiểm tra lúc', definition:'Định nghĩa', error:'Lỗi', message:'Thông tin', allowed_actions:'Thao tác khả dụng' };
export interface Column { key: string; label?: string; link?: (row: AdminRecord) => string; render?: (row: AdminRecord) => React.ReactNode }
export function DataTable({ rows, columns, actions }: { rows: AdminRecord[]; columns: Column[]; actions?: (row: AdminRecord) => React.ReactNode }) {
  if (!rows.length) return <div className="admin-panel p-8"><h2 className="font-medium">Không có bản ghi</h2><p className="admin-muted mt-1">Thử thay đổi bộ lọc hoặc khoảng thời gian.</p></div>;
  return <div className="admin-panel overflow-x-auto"><table className="w-full"><thead className="bg-muted/40"><tr>{columns.map(c => <th key={c.key} scope="col">{c.label || labels[c.key] || c.key}</th>)}{actions && <th scope="col">Thao tác</th>}</tr></thead><tbody>{rows.map((row,i) => <tr key={String(row.id || row.user_id || i)}>{columns.map(c => <td key={c.key}>{c.render ? c.render(row) : c.link ? <Link className="text-primary underline underline-offset-2" href={c.link(row)}>{display(row[c.key])}</Link> : display(row[c.key])}</td>)}{actions && <td><div className="flex flex-wrap gap-2">{actions(row)}</div></td>}</tr>)}</tbody></table></div>;
}
export function RecordView({ data }: { data: unknown }) {
  if (data == null) return <p className="admin-muted">Chưa có dữ liệu.</p>;
  if (Array.isArray(data)) {
    if (!data.length) return <p className="admin-muted">Không có bản ghi.</p>;
    if (data.every(v => v && typeof v === 'object' && !Array.isArray(v))) return <DataTable rows={data} columns={Array.from(new Set(data.flatMap(v => Object.keys(v)))).filter(k => !['allowed_actions'].includes(k)).map(key => ({key, render: row => typeof row[key] === 'object' && row[key] !== null ? <details><summary className="cursor-pointer">Xem chi tiết</summary><div className="mt-2"><RecordView data={row[key]}/></div></details> : display(row[key])}))}/>;
    return <ul className="list-disc space-y-1 pl-5">{data.map((v,i) => <li key={i}>{display(v)}</li>)}</ul>;
  }
  if (typeof data !== 'object') return <p className="break-words">{display(data)}</p>;
  return <dl className="divide-y rounded-md border">{Object.entries(data as AdminRecord).filter(([key]) => key !== 'allowed_actions').map(([key,value]) => <div key={key} className="grid gap-2 p-3 sm:grid-cols-[180px_minmax(0,1fr)]"><dt className="admin-muted text-xs">{labels[key] || key}</dt><dd className="min-w-0">{typeof value === 'object' && value !== null ? <RecordView data={value}/> : <span className="break-words">{display(value)}</span>}</dd></div>)}</dl>;
}
export function Filters({ fields = [], dates = true, search = true, order = true }: { fields?: string[]; dates?: boolean; search?: boolean; order?: boolean }) {
  const params = useSearchParams() ?? new URLSearchParams(); const router = useRouter(); const pathname = usePathname() ?? "/admin";
  return <form key={params.toString()} className="flex flex-wrap items-end gap-3" onSubmit={e => {e.preventDefault();const query = new URLSearchParams(params.toString()); new FormData(e.currentTarget).forEach((value,key) => { if (String(value).trim()) query.set(key,String(value).trim()); else query.delete(key); }); query.set('page','1');router.push(`${pathname}?${query}`);}}>
    {search && <label className="grid gap-1 text-xs">Tìm kiếm<input name="search" defaultValue={params.get('search') || ''} placeholder="Tên, email hoặc ID"/></label>}
    {dates && <><label className="grid gap-1 text-xs">Từ ngày<input type="date" name="from" defaultValue={params.get('from')?.slice(0,10) || ''}/></label><label className="grid gap-1 text-xs">Đến ngày (không gồm)<input type="date" name="to" defaultValue={params.get('to')?.slice(0,10) || ''}/></label></>}
    {fields.map(field => <label key={field} className="grid gap-1 text-xs">{labels[field] || field}<input name={field} className="w-32" defaultValue={params.get(field) || ''}/></label>)}
    {order && <label className="grid gap-1 text-xs">Thứ tự<select name="order" defaultValue={params.get('order') || 'desc'}><option value="desc">Giảm dần</option><option value="asc">Tăng dần</option></select></label>}<button type="submit">Áp dụng</button><Link href={pathname} className="px-2 py-2 text-xs underline">Xóa lọc</Link>
  </form>;
}
export function Pagination({ total, page, size, sorts = [] }: { total: number; page: number; size: number; sorts?: string[] }) {
  const params = useSearchParams() ?? new URLSearchParams();const pathname = usePathname() ?? "/admin";const router = useRouter();
  const change = (key: string,value: string) => {const q = new URLSearchParams(params.toString());q.set(key,value);if(key !== 'page')q.set('page','1');router.push(`${pathname}?${q}`);};
  return <div className="flex flex-wrap items-center gap-3 text-xs"><span className="admin-muted">{display(total)} bản ghi · Trang {page}/{Math.max(1,Math.ceil(total/size))}</span><label>Số dòng <select value={size} onChange={e => change('page_size',e.target.value)}>{[25,50,100].map(n => <option key={n}>{n}</option>)}</select></label>{sorts.length > 0 && <label>Sắp xếp <select value={params.get('sort') || 'created_at'} onChange={e => change('sort',e.target.value)}>{sorts.map(s => <option key={s} value={s}>{labels[s] || s}</option>)}</select></label>}<div className="ml-auto flex gap-2"><button disabled={page <= 1} onClick={() => change('page',String(page-1))}>Trước</button><button disabled={page*size >= total} onClick={() => change('page',String(page+1))}>Sau</button></div></div>;
}
export function Trend({ title, rows, series }: { title: string; rows: AdminRecord[]; series: { key: string; label: string }[] }) {
  const colors = ['#3b82f6','#10b981','#a855f7'];
  const values = rows.flatMap(row => series.map(s => Number(row[s.key] || 0)));
  const max = Math.max(...values,1);
  return <section className="admin-panel p-4"><h2 className="mb-3 font-medium">{title}</h2>{rows.length ? <><svg viewBox="0 0 600 180" role="img" aria-label={`${title}: ${rows.length} mốc thời gian, giá trị cao nhất ${display(Math.max(...values))}`} className="w-full"><text x="0" y="12" fill="currentColor" fontSize="10">{display(Math.max(...values))}</text><line x1="0" y1="158" x2="600" y2="158" stroke="currentColor" opacity=".2"/>{series.map((s,i) => <polyline key={s.key} fill="none" stroke={colors[i]} strokeWidth="2" points={rows.map((row,j) => `${rows.length === 1 ? 300 : j/(rows.length-1)*600},${158-Number(row[s.key] || 0)/max*130}`).join(' ')}/>)}{rows.length === 1 && series.map((s,i) => <circle key={s.key} cx="300" cy={158-Number(rows[0][s.key] || 0)/max*130} r="3" fill={colors[i]}/>)}</svg><div className="admin-muted flex justify-between text-xs"><span>{display(rows[0].date)}</span><span>{display(rows.at(-1)?.date)}</span></div><div className="mt-3 flex gap-3 text-xs">{series.map((s,i) => <span key={s.key} style={{color:colors[i]}}>{s.label}</span>)}</div><details className="mt-3 text-xs"><summary className="cursor-pointer">Dữ liệu biểu đồ</summary><DataTable rows={rows} columns={[{key:'date',label:'Ngày'},...series.map(s => ({key:s.key,label:s.label}))]}/></details></> : <p className="admin-muted py-10">Không có dữ liệu trong kỳ đã chọn.</p>}</section>;
}
export interface ActionSpec { title: string; description: string; fields?: { key: string; label: string; type?: string; value?: string; options?: string[] }[]; run: (values: AdminRecord) => Promise<unknown> }
export function ActionDialog({ action, close, done }: { action: ActionSpec | null; close: () => void; done: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [pending,setPending] = useState(false);
  const [error,setError] = useState('');
  useEffect(() => {
    if(action) ref.current?.showModal(); else ref.current?.close();
  },[action]);
  return <dialog ref={ref} onCancel={e => {if(pending)e.preventDefault();else close();}} aria-labelledby="action-title">
    <form onSubmit={async e => {
      e.preventDefault();
      if(!action || pending)return;
      const values = Object.fromEntries(new FormData(e.currentTarget));
      setPending(true);setError('');
      try { await action.run(values);done();close(); }
      catch(error) { setError(error instanceof Error ? error.message : 'Thao tác thất bại'); }
      finally { setPending(false); }
    }}>
      <h2 id="action-title" className="text-lg font-semibold">{action?.title}</h2>
      <p className="admin-muted my-3">{action?.description}</p>
      {action?.fields?.map(field => <label key={field.key} className="my-3 grid gap-1">{field.label}
        {field.options ? <select name={field.key} defaultValue={field.value}>{field.options.map(value => <option key={value}>{value}</option>)}</select> : <input name={field.key} type={field.type || 'text'} defaultValue={field.value} required min={field.type === 'number' ? 0 : undefined} step={field.type === 'number' ? 'any' : undefined}/>}
      </label>)}
      <label className="grid gap-1">Lý do (bắt buộc)<textarea name="reason" required minLength={3} maxLength={1000} rows={3}/></label>
      {error && <p role="alert" className="mt-3 text-destructive">{error}</p>}
      <div className="mt-5 flex justify-end gap-2"><button type="button" disabled={pending} onClick={close}>Hủy</button><button disabled={pending} type="submit">{pending ? 'Đang xử lý…' : 'Xác nhận'}</button></div>
    </form>
  </dialog>;
}
