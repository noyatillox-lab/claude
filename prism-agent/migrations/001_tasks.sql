-- ============================================================
-- 001_tasks.sql — jamoa vazifalari jadvali (STANDART / keyin moslashtiriladi)
--
-- ESLATMA: bu standart schema. Agar sizda allaqachon 'tasks' jadvali bo'lsa,
-- ustun nomlarini solishtiring va kerak bo'lsa .env dagi SUPABASE_TASKS_TABLE
-- yoki tool kodidagi ustun nomlarini moslashtiring.
-- ============================================================

create table if not exists tasks (
    id          uuid        primary key default gen_random_uuid(),
    title       text        not null,                 -- vazifa matni
    description text,                                 -- qo'shimcha tafsilot (ixtiyoriy)
    assignee    text,                                 -- kimga (ism, matn ko'rinishida)
    status      text        not null default 'todo',  -- todo | in_progress | done | cancelled
    priority    text        not null default 'normal',-- low | normal | high | urgent
    due_date    date,                                 -- muddat (ixtiyoriy)
    created_by  text,                                 -- kim yaratdi (masalan Telegram nomi)
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- Status va assignee bo'yicha filtrlash tez bo'lishi uchun indekslar
create index if not exists tasks_status_idx   on tasks (status);
create index if not exists tasks_assignee_idx on tasks (assignee);

-- Qiymatlar to'g'riligini tekshirish (ixtiyoriy — kerak bo'lmasa olib tashlang)
alter table tasks
    drop constraint if exists tasks_status_check;
alter table tasks
    add constraint tasks_status_check
    check (status in ('todo', 'in_progress', 'done', 'cancelled'));

alter table tasks
    drop constraint if exists tasks_priority_check;
alter table tasks
    add constraint tasks_priority_check
    check (priority in ('low', 'normal', 'high', 'urgent'));

-- updated_at ni avtomatik yangilash uchun trigger
create or replace function set_tasks_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_tasks_updated_at on tasks;
create trigger trg_tasks_updated_at
    before update on tasks
    for each row execute function set_tasks_updated_at();
