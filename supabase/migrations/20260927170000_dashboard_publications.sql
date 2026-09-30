-- Published, sanitized snapshots only. Raw evidence, API logs and secrets stay local.
begin;

create table public.dashboard_readers (
  user_id uuid primary key references auth.users(id),
  created_at timestamptz not null default now()
);

create table public.dashboard_reports (
  report_id text primary key check (report_id ~ '^rpt_[a-f0-9]{64}$'),
  report_type text not null check (report_type in ('daily','weekly')),
  as_of timestamptz not null,
  published_at timestamptz not null default clock_timestamp(),
  methodology_version text not null,
  config_hash text not null,
  source_config_hash text not null,
  code_hash text not null,
  score integer check (score between 1 and 100),
  supersedes text references public.dashboard_reports(report_id),
  payload jsonb not null,
  check (payload->>'contract_version' = 'dashboard-v1'),
  check (payload->>'mode' = 'live'),
  check (payload->>'report_id' = report_id),
  check (payload->>'report_type' = report_type),
  check (jsonb_typeof(payload->'incidents') = 'array'),
  check (jsonb_typeof(payload->'sources') = 'array')
);
create index dashboard_reports_latest on public.dashboard_reports(report_type, as_of desc, published_at desc, report_id desc);

create table public.dashboard_report_incidents (
  report_id text not null references public.dashboard_reports(report_id),
  incident_id text not null,
  revision_id text not null,
  category text not null,
  published_at timestamptz,
  payload jsonb not null,
  primary key (report_id, incident_id)
);
create table public.dashboard_report_sources (
  report_id text not null references public.dashboard_reports(report_id),
  source_id text not null,
  status text not null check (status in ('current','stale','partial','unavailable')),
  payload jsonb not null,
  primary key (report_id, source_id)
);

alter table public.dashboard_readers enable row level security;
alter table public.dashboard_reports enable row level security;
alter table public.dashboard_report_incidents enable row level security;
alter table public.dashboard_report_sources enable row level security;

revoke all on public.dashboard_readers, public.dashboard_reports,
  public.dashboard_report_incidents, public.dashboard_report_sources from public, anon, authenticated;
grant select on public.dashboard_readers, public.dashboard_reports,
  public.dashboard_report_incidents, public.dashboard_report_sources to authenticated;
-- There is no anonymous read policy and registration alone grants no report access.
create policy dashboard_read_self on public.dashboard_readers for select to authenticated
  using (user_id = (select auth.uid()));
create policy dashboard_read_reports on public.dashboard_reports for select to authenticated
  using (exists (select 1 from public.dashboard_readers where user_id = (select auth.uid())));
create policy dashboard_read_incidents on public.dashboard_report_incidents for select to authenticated
  using (exists (select 1 from public.dashboard_readers where user_id = (select auth.uid())));
create policy dashboard_read_sources on public.dashboard_report_sources for select to authenticated
  using (exists (select 1 from public.dashboard_readers where user_id = (select auth.uid())));

revoke all on public.dashboard_reports, public.dashboard_report_incidents,
  public.dashboard_report_sources from service_role;
grant select, insert on public.dashboard_reports, public.dashboard_report_incidents,
  public.dashboard_report_sources to service_role;
grant select on public.dashboard_readers to service_role;

create function public.dashboard_prevent_revision() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  raise exception 'Published reports are immutable; create a new report';
end;
$$;
revoke all on function public.dashboard_prevent_revision() from public, anon, authenticated;
create trigger dashboard_reports_immutable before update or delete on public.dashboard_reports
  for each row execute function public.dashboard_prevent_revision();
create trigger dashboard_incidents_immutable before update or delete on public.dashboard_report_incidents
  for each row execute function public.dashboard_prevent_revision();
create trigger dashboard_sources_immutable before update or delete on public.dashboard_report_sources
  for each row execute function public.dashboard_prevent_revision();

create function public.dashboard_publish(p_report jsonb) returns jsonb
language plpgsql security invoker set search_path = '' as $$
declare
  saved public.dashboard_reports%rowtype;
  new_id text;
  old_report public.dashboard_reports%rowtype;
begin
  if p_report->>'contract_version' is distinct from 'dashboard-v1'
     or p_report->>'mode' is distinct from 'live'
     or jsonb_typeof(p_report->'incidents') is distinct from 'array'
     or jsonb_typeof(p_report->'sources') is distinct from 'array'
     or p_report->>'report_type' not in ('daily','weekly')
     or not (p_report ?& array['report_id','report_type','as_of','window','provenance','rtb','coverage','gaps','geojson','commentary','limitations','supersedes']) then
    raise exception 'Invalid publication contract';
  end if;
  if (p_report#>>'{window,end}')::timestamptz is distinct from (p_report->>'as_of')::timestamptz
     or (p_report#>>'{window,start}')::timestamptz > (p_report->>'as_of')::timestamptz
     or (p_report->>'as_of')::timestamptz > clock_timestamp() + interval '5 minutes'
     or p_report#>>'{rtb,status}' not in ('available','insufficient_data')
     or not (p_report->'rtb' ? 'score')
     or ((p_report#>>'{rtb,score}') is null) <> ((p_report#>>'{rtb,status}') = 'insufficient_data')
     or ((p_report#>>'{rtb,score}') is not null and jsonb_typeof(p_report#>'{rtb,score}') <> 'number')
     or (p_report#>>'{rtb,confidence,percent}') is not null then
    raise exception 'Invalid score or observation time';
  end if;
  if p_report->>'supersedes' is not null then
    select * into old_report from public.dashboard_reports where report_id = p_report->>'supersedes';
    if not found or old_report.report_type <> p_report->>'report_type'
       or old_report.as_of <> (p_report->>'as_of')::timestamptz then
      raise exception 'A correction must reference the same report period and type';
    end if;
  end if;
  insert into public.dashboard_reports(report_id,report_type,as_of,methodology_version,config_hash,source_config_hash,code_hash,score,supersedes,payload)
    values (p_report->>'report_id',p_report->>'report_type',(p_report->>'as_of')::timestamptz,
            p_report#>>'{provenance,methodology_version}',p_report#>>'{provenance,config_hash}',
            p_report#>>'{provenance,source_config_hash}',p_report#>>'{provenance,code_hash}',(p_report#>>'{rtb,score}')::integer,
            p_report->>'supersedes',p_report)
    on conflict (report_id) do nothing returning report_id into new_id;
  if new_id is null then
    select * into saved from public.dashboard_reports where report_id = p_report->>'report_id';
    if saved.payload is distinct from p_report then
      raise exception 'Existing report has different content';
    end if;
    return jsonb_build_object('report_id',saved.report_id,'published_at',saved.published_at,'created',false);
  end if;
  insert into public.dashboard_report_incidents(report_id,incident_id,revision_id,category,published_at,payload)
    select new_id, x->>'id', x->>'revision_id', x->>'category', (x->>'published_at')::timestamptz, x
    from jsonb_array_elements(p_report->'incidents') x;
  insert into public.dashboard_report_sources(report_id,source_id,status,payload)
    select new_id, x->>'id', x->>'status', x from jsonb_array_elements(p_report->'sources') x;
  select * into saved from public.dashboard_reports where report_id=new_id;
  return jsonb_build_object('report_id',saved.report_id,'published_at',saved.published_at,'created',true);
end;
$$;
revoke all on function public.dashboard_publish(jsonb) from public, anon, authenticated;
grant execute on function public.dashboard_publish(jsonb) to service_role;

comment on table public.dashboard_reports is 'Immutable, sanitized RTB publications. Data API access is private by default.';
comment on function public.dashboard_publish(jsonb) is 'Atomic idempotent publication, server only. JSON Schema validation is required in the trusted publisher.';
commit;
