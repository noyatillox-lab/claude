-- ============================================================
-- 01_supabase_schema.sql  (REFERENCE / namuna)
-- Obsidian bilim bazasi uchun pgvector jadvali va qidiruv RPC'si.
--
-- ESLATMA: bu sizning mavjud faylingizga mos "reference" versiya.
-- Agar sizda allaqachon shu jadval bo'lsa, o'zingiznikini ishlating —
-- muhimi: match_obsidian_chunks() RPC imzosi bir xil bo'lishi kerak.
-- ============================================================

-- pgvector kengaytmasi (embeddinglar uchun)
create extension if not exists vector;

-- Obsidian yozuvlaridan chunk'lar
create table if not exists obsidian_chunks (
    id          bigint generated always as identity primary key,
    source      text        not null,               -- fayl yo'li / yozuv nomi
    chunk_index integer      not null default 0,      -- fayl ichidagi chunk tartibi
    content     text        not null,               -- chunk matni
    embedding   vector(1536),                        -- text-embedding-3-small = 1536 o'lchov
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    unique (source, chunk_index)
);

-- Cosine similarity bo'yicha tez qidiruv uchun indeks
create index if not exists obsidian_chunks_embedding_idx
    on obsidian_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- ------------------------------------------------------------
-- match_obsidian_chunks: berilgan embedding'ga eng yaqin chunk'larni qaytaradi
--   query_embedding — qidiruv vektori
--   match_count     — nechta natija
--   min_similarity  — minimal cosine similarity (0..1)
-- ------------------------------------------------------------
create or replace function match_obsidian_chunks (
    query_embedding vector(1536),
    match_count     int    default 5,
    min_similarity  float  default 0.0
)
returns table (
    id         bigint,
    source     text,
    content    text,
    similarity float
)
language sql stable
as $$
    select
        c.id,
        c.source,
        c.content,
        1 - (c.embedding <=> query_embedding) as similarity
    from obsidian_chunks c
    where c.embedding is not null
      and 1 - (c.embedding <=> query_embedding) >= min_similarity
    order by c.embedding <=> query_embedding
    limit match_count;
$$;
