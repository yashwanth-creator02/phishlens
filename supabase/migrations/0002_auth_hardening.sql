-- PhishLens auth hardening migration.
-- 0001_init.sql already enables RLS and creates the child-table indexes. This migration
-- re-asserts both idempotently so a partially applied or hand-edited database converges.
-- The backend connects with the Supabase service role and must explicitly scope every query
-- to the authenticated user_id. RLS protects direct client access (e.g. via supabase-js) only.

create index if not exists ix_email_raw_analysis on email_raw (analysis_id);
create index if not exists ix_feature_values_analysis on feature_values (analysis_id);
create index if not exists ix_explanations_analysis on explanations (analysis_id, rank);

alter table analyses        enable row level security;
alter table email_raw       enable row level security;
alter table feature_values  enable row level security;
alter table explanations    enable row level security;
alter table sender_profiles enable row level security;
alter table user_aliases    enable row level security;
alter table model_versions  enable row level security;
