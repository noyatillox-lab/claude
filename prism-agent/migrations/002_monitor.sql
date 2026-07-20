-- ============================================================
-- 002_monitor.sql — guruh monitoring topilmalari logi
--
-- Guruhda ismingiz (variantlari bilan) tilga olinganda shu jadvalga yoziladi.
-- ============================================================

create table if not exists monitor_hits (
    id              uuid        primary key default gen_random_uuid(),
    chat_id         bigint,                     -- guruh/kanal ID
    chat_title      text,                       -- guruh nomi
    sender_id       bigint,                     -- kim yozdi (ID)
    sender_name     text,                       -- kim yozdi (ism)
    message_id      bigint,                     -- xabar ID
    kind            text        not null,       -- text | voice | video | video_note | audio
    content         text,                       -- asl matn yoki transkript
    matched_variant text,                       -- qaysi ism varianti mos keldi
    match_score     integer,                    -- o'xshashlik bahosi (0..100)
    message_link    text,                       -- xabarga havola (iloji bo'lsa)
    created_at      timestamptz not null default now()
);

create index if not exists monitor_hits_chat_idx on monitor_hits (chat_id);
create index if not exists monitor_hits_created_idx on monitor_hits (created_at desc);
