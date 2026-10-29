-- PhishLens initial schema for Supabase (PostgreSQL). Mirrors backend/app/db/models.py (SQLAlchemy).
-- The backend currently creates tables itself (Base.metadata.create_all) and talks to Postgres with the
-- service connection, so these Row-Level-Security policies protect DIRECT access from the web client
-- (e.g. supabase-js) and document the intended ownership model. user_id = auth.uid()::text.

create table if not exists analyses (
  id              varchar(32) primary key,
  user_id         varchar(64) not null,
  created_at      timestamp   not null default now(),
  sender_address  varchar(320) not null default '',
  sender_name     varchar(320) not null default '',
  subject         text        not null default '',
  scope           varchar(32) not null default 'direct',
  forwarded_by    varchar(320) not null default '',
  probability     double precision not null,
  risk_score      integer     not null,
  risk_band       varchar(8)  not null,
  model_version   varchar(64) not null,
  auth            jsonb       not null default '{}',
  evidence        jsonb       not null default '{}'
);
create index if not exists ix_analyses_user on analyses (user_id, created_at desc);

create table if not exists email_raw (
  analysis_id  varchar(32) primary key references analyses(id) on delete cascade,
  storage_path varchar(512) not null,
  sha256       varchar(64)  not null,
  headers      jsonb not null default '{}',
  text_preview text  not null default '',
  links        jsonb not null default '[]',
  attachments  jsonb not null default '[]'
);

create table if not exists feature_values (
  id          bigserial primary key,
  analysis_id varchar(32) not null references analyses(id) on delete cascade,
  name        varchar(64) not null,
  "group"     varchar(16) not null,
  value       double precision not null,
  contribution double precision not null default 0
);
create index if not exists ix_feature_values_analysis on feature_values (analysis_id);

create table if not exists explanations (
  id          bigserial primary key,
  analysis_id varchar(32) not null references analyses(id) on delete cascade,
  rank        integer not null,
  rule_key    varchar(48) not null,
  "group"     varchar(16) not null,
  contribution double precision not null,
  sentence    text not null
);
create index if not exists ix_explanations_analysis on explanations (analysis_id, rank);

create table if not exists model_versions (
  id          varchar(32) primary key,
  algorithm   varchar(32) not null,
  version_tag varchar(64) not null unique,
  f1_macro    double precision not null default 0,
  roc_auc     double precision not null default 0,
  meta        jsonb not null default '{}',
  trained_at  timestamp not null default now(),
  is_active   boolean not null default false
);

create table if not exists sender_profiles (
  id             bigserial primary key,
  user_id        varchar(64) not null,
  sender_address varchar(320) not null,
  message_count  integer not null default 0,
  first_seen     timestamp,
  last_seen      timestamp,
  stats          jsonb not null default '{}',
  updated_at     timestamp not null default now(),
  constraint uq_profile_user_sender unique (user_id, sender_address)
);

create table if not exists user_aliases (
  user_id    varchar(64) primary key,
  token      varchar(16) not null unique,
  created_at timestamp not null default now()
);

-- Row-Level Security: a signed-in user can only see their own rows through the Supabase client API.
alter table analyses        enable row level security;
alter table email_raw       enable row level security;
alter table feature_values  enable row level security;
alter table explanations    enable row level security;
alter table sender_profiles enable row level security;
alter table user_aliases    enable row level security;
alter table model_versions  enable row level security;

create policy analyses_owner on analyses for select using (user_id = auth.uid()::text);
create policy email_raw_owner on email_raw for select
  using (exists (select 1 from analyses a where a.id = analysis_id and a.user_id = auth.uid()::text));
create policy feature_values_owner on feature_values for select
  using (exists (select 1 from analyses a where a.id = analysis_id and a.user_id = auth.uid()::text));
create policy explanations_owner on explanations for select
  using (exists (select 1 from analyses a where a.id = analysis_id and a.user_id = auth.uid()::text));
create policy sender_profiles_owner on sender_profiles for select using (user_id = auth.uid()::text);
create policy user_aliases_owner on user_aliases for select using (user_id = auth.uid()::text);
create policy model_versions_read on model_versions for select using (true);
-- No insert/update/delete policies: only the backend (service role / direct connection) writes.
