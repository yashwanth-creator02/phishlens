-- PhishLens storage bucket for raw forwarded/uploaded emails.
-- Creates a private bucket 'raw_emails' with a 10 MB size cap.
-- Object path convention: <user_id>/<analysis_id>.eml
-- RLS policies enforce tenant isolation so authenticated users can only access their own objects.
-- The backend connecting with the service role automatically bypasses RLS.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'raw_emails',
  'raw_emails',
  false,
  10485760,
  array['message/rfc822', 'text/plain', 'application/octet-stream']
)
on conflict (id) do update set
  public = false,
  file_size_limit = 10485760,
  allowed_mime_types = array['message/rfc822', 'text/plain', 'application/octet-stream'];

-- Policy on buckets: Allow authenticated users to view raw_emails bucket metadata
drop policy if exists "Allow authenticated to view buckets" on storage.buckets;
create policy "Allow authenticated to view buckets"
on storage.buckets for select
to authenticated
using (id = 'raw_emails');

-- Policy 1: Users can select (download) their own raw emails
drop policy if exists "Users can read own raw emails" on storage.objects;
create policy "Users can read own raw emails"
on storage.objects for select
to authenticated
using (
  bucket_id = 'raw_emails' and
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy 2: Users can insert their own raw emails
drop policy if exists "Users can insert own raw emails" on storage.objects;
create policy "Users can insert own raw emails"
on storage.objects for insert
to authenticated
with check (
  bucket_id = 'raw_emails' and
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy 3: Users can update their own raw emails
drop policy if exists "Users can update own raw emails" on storage.objects;
create policy "Users can update own raw emails"
on storage.objects for update
to authenticated
using (
  bucket_id = 'raw_emails' and
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy 4: Users can delete their own raw emails
drop policy if exists "Users can delete own raw emails" on storage.objects;
create policy "Users can delete own raw emails"
on storage.objects for delete
to authenticated
using (
  bucket_id = 'raw_emails' and
  (storage.foldername(name))[1] = auth.uid()::text
);
