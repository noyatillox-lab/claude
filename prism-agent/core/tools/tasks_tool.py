"""
Vazifalar tool — Supabase 'tasks' jadvaliga CRUD.

Uchta tool taqdim etadi:
  - create_task  : yangi vazifa yaratadi
  - list_tasks   : vazifalarni ko'radi/filtrlaydi
  - update_task  : status yoki boshqa maydonlarni yangilaydi

STANDART schema bilan ishlaydi (migrations/001_tasks.sql). Ustunlaringiz farq qilsa,
_COLS lug'atini yoki .env dagi SUPABASE_TASKS_TABLE ni moslashtiring.
"""

import asyncio

from core import config
from core.db import get_supabase
from core.logging_setup import get_logger
from core.tools.base import RunContext

log = get_logger("tasks_tool")

_TABLE = config.SUPABASE_TASKS_TABLE
_VALID_STATUS = {"todo", "in_progress", "done", "cancelled"}
_VALID_PRIORITY = {"low", "normal", "high", "urgent"}


# --------------------------------------------------------------------------
# Supabase amallari (sinxron — asyncio.to_thread bilan chaqiriladi)
# --------------------------------------------------------------------------
def _insert_task(row: dict) -> dict:
    resp = get_supabase().table(_TABLE).insert(row).execute()
    return (resp.data or [{}])[0]


def _select_tasks(assignee: str | None, status: str | None, limit: int) -> list[dict]:
    q = get_supabase().table(_TABLE).select("*")
    if assignee:
        q = q.ilike("assignee", f"%{assignee}%")
    if status:
        q = q.eq("status", status)
    q = q.order("created_at", desc=True).limit(limit)
    return q.execute().data or []


def _update_task(task_id: str, changes: dict) -> list[dict]:
    resp = get_supabase().table(_TABLE).update(changes).eq("id", task_id).execute()
    return resp.data or []


# --------------------------------------------------------------------------
# Handlerlar
# --------------------------------------------------------------------------
async def create_task_handler(tool_input: dict, ctx: RunContext) -> str:
    title = (tool_input.get("title") or "").strip()
    if not title:
        return "[XATO] Vazifa matni (title) bo'sh bo'lmasligi kerak."

    row: dict = {"title": title}
    if tool_input.get("assignee"):
        row["assignee"] = tool_input["assignee"].strip()
    if tool_input.get("description"):
        row["description"] = tool_input["description"]
    if tool_input.get("due_date"):
        row["due_date"] = tool_input["due_date"]
    priority = tool_input.get("priority")
    if priority in _VALID_PRIORITY:
        row["priority"] = priority

    try:
        created = await asyncio.to_thread(_insert_task, row)
    except Exception as exc:
        log.exception("Vazifa yaratishda xato")
        return f"[XATO] Vazifa yaratilmadi: {exc}"

    log.info("Vazifa yaratildi: %s -> %s", title, row.get("assignee"))
    who = row.get("assignee") or "biriktirilmagan"
    return (
        f"Vazifa yaratildi ✅\n"
        f"ID: {created.get('id', '?')}\n"
        f"Matn: {title}\n"
        f"Kim: {who}\n"
        f"Status: {created.get('status', 'todo')}"
    )


async def list_tasks_handler(tool_input: dict, ctx: RunContext) -> str:
    assignee = (tool_input.get("assignee") or "").strip() or None
    status = tool_input.get("status")
    if status and status not in _VALID_STATUS:
        status = None
    limit = int(tool_input.get("limit", 20) or 20)

    try:
        tasks = await asyncio.to_thread(_select_tasks, assignee, status, limit)
    except Exception as exc:
        log.exception("Vazifalarni o'qishda xato")
        return f"[XATO] Vazifalar o'qilmadi: {exc}"

    if not tasks:
        return "Mos vazifa topilmadi."

    lines = []
    for t in tasks:
        due = f" | muddat: {t['due_date']}" if t.get("due_date") else ""
        lines.append(
            f"- [{t.get('status', '?')}] {t.get('title', '')} "
            f"(kim: {t.get('assignee') or '-'}{due}) | ID: {t.get('id', '?')}"
        )
    return f"Topilgan vazifalar ({len(tasks)}):\n" + "\n".join(lines)


async def update_task_handler(tool_input: dict, ctx: RunContext) -> str:
    task_id = (tool_input.get("task_id") or "").strip()
    if not task_id:
        return "[XATO] Yangilash uchun task_id kerak (list_tasks orqali oling)."

    changes: dict = {}
    status = tool_input.get("status")
    if status:
        if status not in _VALID_STATUS:
            return f"[XATO] Noto'g'ri status: {status}. Ruxsat: {', '.join(_VALID_STATUS)}."
        changes["status"] = status
    if tool_input.get("assignee"):
        changes["assignee"] = tool_input["assignee"].strip()
    priority = tool_input.get("priority")
    if priority:
        if priority not in _VALID_PRIORITY:
            return f"[XATO] Noto'g'ri priority: {priority}."
        changes["priority"] = priority
    if tool_input.get("due_date"):
        changes["due_date"] = tool_input["due_date"]

    if not changes:
        return "[XATO] Yangilash uchun kamida bitta maydon bering (status/assignee/...)."

    try:
        updated = await asyncio.to_thread(_update_task, task_id, changes)
    except Exception as exc:
        log.exception("Vazifani yangilashda xato")
        return f"[XATO] Vazifa yangilanmadi: {exc}"

    if not updated:
        return f"[XATO] ID {task_id} bo'yicha vazifa topilmadi."
    log.info("Vazifa yangilandi: %s -> %s", task_id, changes)
    return f"Vazifa yangilandi ✅ (ID: {task_id}, o'zgarishlar: {changes})"


# --------------------------------------------------------------------------
# Tool schema'lari
# --------------------------------------------------------------------------
_CREATE_SPEC = {
    "name": "create_task",
    "description": (
        "Jamoa a'zosiga yangi vazifa (task) yaratadi. "
        "Foydalanuvchi 'X ga shu vazifani ber', 'buni Y qilsin' desa ishlat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Vazifa matni / sarlavhasi."},
            "assignee": {"type": "string", "description": "Kimga biriktirilgani (ism)."},
            "description": {"type": "string", "description": "Qo'shimcha tafsilot."},
            "due_date": {"type": "string", "description": "Muddat, ISO: YYYY-MM-DD."},
            "priority": {
                "type": "string",
                "enum": ["low", "normal", "high", "urgent"],
                "description": "Muhimlik darajasi.",
            },
        },
        "required": ["title"],
    },
}

_LIST_SPEC = {
    "name": "list_tasks",
    "description": (
        "Mavjud vazifalarni ko'rsatadi. Assignee (ism) yoki status bo'yicha filtrlash "
        "mumkin. 'Menda qanaqa vazifalar bor', 'X nima qilishi kerak' savollarida ishlat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "assignee": {"type": "string", "description": "Ism bo'yicha filtr (ixtiyoriy)."},
            "status": {
                "type": "string",
                "enum": ["todo", "in_progress", "done", "cancelled"],
                "description": "Status bo'yicha filtr (ixtiyoriy).",
            },
            "limit": {"type": "integer", "description": "Maksimal soni (default 20)."},
        },
    },
}

_UPDATE_SPEC = {
    "name": "update_task",
    "description": (
        "Mavjud vazifani yangilaydi (status, assignee, priority, muddat). "
        "Avval list_tasks bilan task_id ni oling. 'Buni bajarildi qil', "
        "'X vazifani Y ga ber' kabi buyruqlarda ishlat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "Yangilanadigan vazifa ID'si."},
            "status": {
                "type": "string",
                "enum": ["todo", "in_progress", "done", "cancelled"],
            },
            "assignee": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
            "due_date": {"type": "string", "description": "ISO: YYYY-MM-DD."},
        },
        "required": ["task_id"],
    },
}


def get_tools():
    """Bu modul taqdim etadigan barcha (spec, handler) juftliklari."""
    return [
        (_CREATE_SPEC, create_task_handler),
        (_LIST_SPEC, list_tasks_handler),
        (_UPDATE_SPEC, update_task_handler),
    ]
