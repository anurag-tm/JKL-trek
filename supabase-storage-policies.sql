-- Run in Supabase Dashboard -> SQL Editor.
-- Bucket "treks" must be PUBLIC (for reading images) with these limits:
update storage.buckets
set public = true,
    file_size_limit = 3145728,                          -- 3 MB (the app uploads ~0.5 MB JPEGs)
    allowed_mime_types = array['image/jpeg']
where id = 'treks';

-- The app uses the publishable (anon) key, so uploads cannot be tied to a
-- Firebase user here. These policies allow new JPEG uploads only, and no
-- overwrite or delete from the browser.
drop policy if exists "treks anon upload" on storage.objects;
create policy "treks anon upload" on storage.objects
  for insert to anon, authenticated
  with check (bucket_id = 'treks' and lower(storage.extension(name)) = 'jpg');

drop policy if exists "treks public read" on storage.objects;
create policy "treks public read" on storage.objects
  for select to anon, authenticated
  using (bucket_id = 'treks');
