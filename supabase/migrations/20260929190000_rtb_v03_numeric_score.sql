begin;
alter table public.dashboard_reports alter column score type numeric using score::numeric;
create or replace function public.dashboard_publish(p_report jsonb) returns jsonb
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
            p_report#>>'{provenance,source_config_hash}',p_report#>>'{provenance,code_hash}',(p_report#>>'{rtb,score}')::numeric,
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
commit;
