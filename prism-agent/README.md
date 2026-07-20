# Prism AI Agent

Prism Marketing agentligi uchun markazlashgan Telegram AI assistent. Bitta bot ichida:
bilim bazasi (RAG), mijozlar bilan aloqa, jamoa vazifalari, guruh monitoringi va rasm
generatsiya birlashtiriladi. Mac mini uy serverida `launchd` orqali doim ishlaydi
(bulut hosting kerak emas).

## Arxitektura

```
Telegram bot (aiogram, long polling) ─┐
Telethon userbot (guruh monitoring) ──┼──> Orkestrator (Claude API, tool use) ──> Supabase
                                       │         ├──> search_knowledge_base (RAG)
                                       │         ├──> generate_image (Replicate)
                                       │         └──> create_task (tasks jadvali)
                                       │
                                  Whisper API (ovoz/video -> matn)
```

## Struktura

```
prism-agent/
├── .env.example          # barcha API kalitlar namunasi (haqiqiylari .env'da)
├── requirements.txt
├── core/
│   ├── config.py         # .env'dan sozlamalarni o'qish (markazlashgan)
│   ├── logging_setup.py  # yagona logging
│   ├── orchestrator.py   # Claude API + tool-use routing markazi
│   └── tools/
│       ├── base.py       # RunContext (yon natijalar: rasm URL va h.k.)
│       ├── rag_tool.py       # search_knowledge_base
│       ├── image_tool.py     # generate_image
│       └── tasks_tool.py     # create_task
├── bot/telegram_bot.py       # aiogram long polling (Bosqich 2)
├── monitor/                  # Telethon guruh monitoring (Bosqich 6)
├── migrations/               # Supabase schema migration fayllari
├── logs/
└── launchd/                  # Mac mini servis shablonlari (Bosqich 7)
```

## Ishga tushirish

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # va qiymatlarni to'ldiring
```

## Bosqichlar holati

- [x] **Bosqich 1** — Orkestrator asosi (Claude API + tool-use routing, stub tool'lar)
- [x] **Bosqich 2** — Telegram bot (aiogram, long polling, xotira + ruxsat filtri)
- [x] **Bosqich 3** — RAG tool (`query_knowledge_base` importlib orqali ulandi)
- [x] **Bosqich 4** — Rasm generatsiya (Replicate, URL botga yuboriladi)
- [x] **Bosqich 5** — Vazifalar tool (Supabase `tasks`: create / list / update)
- [ ] **Bosqich 6** — Guruh monitoring (Telethon + Whisper)
- [ ] **Bosqich 7** — Mac mini deploy (`launchd`)

## Xavfsizlik

- API kalitlar faqat `.env`da — kodda hardcode YO'Q.
- Telethon userbot faqat o'qish/eslatish uchun — guruhlarga avtomatik yozish YO'Q.
- Har bir Supabase jadvali uchun alohida migration fayli.
