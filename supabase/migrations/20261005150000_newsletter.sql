-- Newsletter is server-only and disabled until its complete flow is accepted.
begin;
create table public.newsletter_settings (
  id boolean primary key default true check(id),
  enabled boolean not null default false,
  segment_id uuid,
  enabled_at timestamptz,
  check(not enabled or (segment_id is not null and enabled_at is not null))
);
insert into public.newsletter_settings(id) values(true);

create table public.newsletter_requests (
  email_hash text primary key check(email_hash ~ '^[a-f0-9]{64}$'),
  email text,
  token_hash text unique not null check(token_hash ~ '^[a-f0-9]{64}$'),
  consent_version text not null,
  requested_at timestamptz not null default now(),
  expires_at timestamptz not null,
  confirmed_at timestamptz,
  owner uuid,
  lease_until timestamptz,
  contact_id uuid
);
create table public.newsletter_consents (
  token_hash text primary key,
  email_hash text not null,
  consent_version text not null,
  requested_at timestamptz not null,
  confirmed_at timestamptz not null default now()
);
create index newsletter_consents_email on public.newsletter_consents(email_hash);
create table public.newsletter_rate_limits (
  bucket text primary key,
  count integer not null,
  expires_at timestamptz not null
);
create table public.newsletter_deliveries (
  report_day date primary key,
  report_id text not null unique references public.dashboard_reports(report_id),
  mail jsonb not null,
  status text not null check(status in ('creating','ready','sending','sent','needs_review','failed')),
  owner uuid not null,
  lease_until timestamptz not null,
  broadcast_id uuid unique,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  reason text
);

alter table public.newsletter_settings enable row level security;
alter table public.newsletter_requests enable row level security;
alter table public.newsletter_consents enable row level security;
alter table public.newsletter_rate_limits enable row level security;
alter table public.newsletter_deliveries enable row level security;
revoke all on public.newsletter_settings,public.newsletter_requests,public.newsletter_consents,
  public.newsletter_rate_limits,public.newsletter_deliveries from public,anon,authenticated;
grant select,insert,update,delete on public.newsletter_settings,public.newsletter_requests,
  public.newsletter_rate_limits,public.newsletter_deliveries to service_role;
grant select,insert on public.newsletter_consents to service_role;

create function public.newsletter_maintain()
returns void language sql security invoker set search_path='' as $$
  delete from public.newsletter_rate_limits where expires_at<now();
  delete from public.newsletter_requests where expires_at<now()-interval '6 days';
$$;
revoke all on function public.newsletter_maintain() from public,anon,authenticated;
grant execute on function public.newsletter_maintain() to service_role;

create function public.newsletter_request(p_email text,p_email_hash text,p_token_hash text,p_ip_hash text,p_consent_version text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare item public.newsletter_requests%rowtype; bucket text; total integer;
begin
  if not exists(select 1 from public.newsletter_settings where id and enabled) then
    return jsonb_build_object('status','disabled');
  end if;
  if p_email is null or p_email_hash is null or p_token_hash is null or p_ip_hash is null or p_consent_version is null
     or length(p_email)>254 or p_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
     or p_email_hash !~ '^[a-f0-9]{64}$' or p_token_hash !~ '^[a-f0-9]{64}$'
     or p_ip_hash !~ '^[a-f0-9]{64}$' or p_consent_version <> '2026-10-05' then
    raise exception 'invalid_request';
  end if;
  perform pg_advisory_xact_lock(hashtext(p_email_hash));
  select * into item from public.newsletter_requests where email_hash=p_email_hash;
  if found and item.requested_at>now()-interval '15 minutes' then
    return jsonb_build_object('status','accepted','send',false);
  end if;
  -- Persistent counters are shared by all Worker instances. No raw IP is stored.
  foreach bucket in array array[
    'global:'||to_char(now() at time zone 'UTC','YYYY-MM-DD'),
    'ip:'||p_ip_hash||':'||to_char(now() at time zone 'UTC','YYYY-MM-DD-HH24'),
    'email:'||p_email_hash||':'||to_char(now() at time zone 'UTC','YYYY-MM-DD')]
  loop
    insert into public.newsletter_rate_limits values(bucket,1,now()+interval '2 days')
      on conflict on constraint newsletter_rate_limits_pkey do update set count=newsletter_rate_limits.count+1
      returning count into total;
    if total>(case when bucket like 'global:%' then 100 when bucket like 'ip:%' then 5 else 3 end) then
      return jsonb_build_object('status','limited');
    end if;
  end loop;
  insert into public.newsletter_requests(email_hash,email,token_hash,consent_version,expires_at)
    values(p_email_hash,p_email,p_token_hash,p_consent_version,now()+interval '24 hours')
    on conflict(email_hash) do update set email=excluded.email,token_hash=excluded.token_hash,
      consent_version=excluded.consent_version,requested_at=now(),expires_at=excluded.expires_at,
      confirmed_at=null,owner=null,lease_until=null,contact_id=null;
  delete from public.newsletter_rate_limits where expires_at<now();
  delete from public.newsletter_requests where expires_at<now()-interval '6 days';
  return jsonb_build_object('status','accepted','send',true);
end;
$$;

create function public.newsletter_claim_confirmation(p_token_hash text,p_owner uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare item public.newsletter_requests%rowtype;
begin
  if not exists(select 1 from public.newsletter_settings where id and enabled) then
    return jsonb_build_object('status','disabled');
  end if;
  select * into item from public.newsletter_requests where token_hash=p_token_hash for update;
  if not found then return jsonb_build_object('status','expired'); end if;
  if item.confirmed_at is not null then return jsonb_build_object('status','confirmed'); end if;
  if item.expires_at<now() then return jsonb_build_object('status','expired'); end if;
  if item.lease_until>now() then return jsonb_build_object('status','busy'); end if;
  update public.newsletter_requests set owner=p_owner,lease_until=now()+interval '2 minutes' where token_hash=p_token_hash;
  return jsonb_build_object('status','claimed','email',item.email);
end;
$$;

create function public.newsletter_finish_confirmation(p_token_hash text,p_owner uuid,p_contact_id uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare item public.newsletter_requests%rowtype;
begin
  select * into item from public.newsletter_requests where token_hash=p_token_hash and owner=p_owner for update;
  if not found then raise exception 'confirmation_lease_lost'; end if;
  if p_contact_id is null then
    update public.newsletter_requests set owner=null,lease_until=null where token_hash=p_token_hash;
    return jsonb_build_object('status','pending');
  end if;
  insert into public.newsletter_consents(token_hash,email_hash,consent_version,requested_at)
    values(item.token_hash,item.email_hash,item.consent_version,item.requested_at) on conflict do nothing;
  -- Resend owns the subscriber address and unsubscribe state. Keep only consent evidence here.
  update public.newsletter_requests set email=null,confirmed_at=now(),contact_id=p_contact_id,owner=null,lease_until=null where token_hash=p_token_hash;
  return jsonb_build_object('status','confirmed');
end;
$$;

create function public.newsletter_claim_delivery(p_report_id text,p_mail jsonb,p_owner uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare report public.dashboard_reports%rowtype; job public.newsletter_deliveries%rowtype; day date; start_at timestamptz;
begin
  select enabled_at into start_at from public.newsletter_settings where id and enabled;
  if not found then return jsonb_build_object('status','disabled'); end if;
  select * into report from public.dashboard_reports where report_id=p_report_id and report_type='daily';
  if not found or report.payload->>'mode'<>'live' or report.published_at<start_at
    or (report.as_of at time zone 'Europe/Warsaw')::date<>(now() at time zone 'Europe/Warsaw')::date
    or report.as_of>now()+interval '5 minutes' then return jsonb_build_object('status','ineligible'); end if;
  if p_report_id<>(select report_id from public.dashboard_reports where report_type='daily' order by as_of desc,published_at desc,report_id desc limit 1) then
    return jsonb_build_object('status','superseded');
  end if;
  day := (report.as_of at time zone 'Europe/Warsaw')::date;
  perform pg_advisory_xact_lock(hashtext('newsletter:'||day::text));
  select * into job from public.newsletter_deliveries where report_day=day for update;
  if found then
    if job.report_id<>p_report_id or job.status in ('sent','failed','needs_review') then
      return jsonb_build_object('status','already_handled','delivery_status',job.status);
    end if;
    if job.lease_until>now() then return jsonb_build_object('status','busy'); end if;
    if job.status='creating' then
      update public.newsletter_deliveries set status='needs_review',reason='draft_outcome_unknown' where report_day=day;
      return jsonb_build_object('status','needs_review');
    end if;
    update public.newsletter_deliveries set owner=p_owner,lease_until=now()+interval '5 minutes' where report_day=day returning * into job;
  else
    if jsonb_typeof(p_mail)<>'object' or not(p_mail ?& array['html','text','subject','from','reply_to']) then raise exception 'invalid_mail'; end if;
    insert into public.newsletter_deliveries(report_day,report_id,mail,status,owner,lease_until)
      values(day,p_report_id,p_mail,'creating',p_owner,now()+interval '5 minutes') returning * into job;
  end if;
  return jsonb_build_object('status',job.status,'report_id',job.report_id,'mail',job.mail,'broadcast_id',job.broadcast_id,'report_day',job.report_day);
end;
$$;

create function public.newsletter_save_broadcast(p_report_id text,p_owner uuid,p_broadcast_id uuid)
returns void language plpgsql security invoker set search_path='' as $$
begin
  update public.newsletter_deliveries set broadcast_id=p_broadcast_id,status='ready'
    where report_id=p_report_id and owner=p_owner and status='creating' and lease_until>now();
  if not found then raise exception 'delivery_lease_lost'; end if;
end;
$$;
create function public.newsletter_begin_send(p_report_id text,p_owner uuid)
returns boolean language plpgsql security invoker set search_path='' as $$
begin
  update public.newsletter_deliveries set status='sending'
    where report_id=p_report_id and owner=p_owner and status='ready' and lease_until>now() and broadcast_id is not null;
  return found;
end;
$$;
create function public.newsletter_finish_delivery(p_report_id text,p_owner uuid,p_status text,p_reason text default null)
returns void language plpgsql security invoker set search_path='' as $$
begin
  if p_status not in ('sent','needs_review','failed') then raise exception 'invalid_status'; end if;
  update public.newsletter_deliveries set status=p_status,reason=p_reason,
    sent_at=case when p_status='sent' then now() else null end,lease_until=now()
    where report_id=p_report_id and owner=p_owner and status in ('creating','ready','sending');
  if not found then raise exception 'delivery_lease_lost'; end if;
end;
$$;

revoke all on function public.newsletter_request(text,text,text,text,text),
  public.newsletter_claim_confirmation(text,uuid),public.newsletter_finish_confirmation(text,uuid,uuid),
  public.newsletter_claim_delivery(text,jsonb,uuid),public.newsletter_save_broadcast(text,uuid,uuid),
  public.newsletter_begin_send(text,uuid),public.newsletter_finish_delivery(text,uuid,text,text) from public,anon,authenticated;
grant execute on function public.newsletter_request(text,text,text,text,text),
  public.newsletter_claim_confirmation(text,uuid),public.newsletter_finish_confirmation(text,uuid,uuid),
  public.newsletter_claim_delivery(text,jsonb,uuid),public.newsletter_save_broadcast(text,uuid,uuid),
  public.newsletter_begin_send(text,uuid),public.newsletter_finish_delivery(text,uuid,text,text) to service_role;
commit;
