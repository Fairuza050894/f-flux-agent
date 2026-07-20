import os
from typing import Dict, List, Any


def get_int_env(name: str, default: int = 0) -> int:
    value = os.getenv(name, str(default))

    try:
        return int(value)
    except ValueError:
        return default


def split_telegram_message(text: str, limit: int = 3900) -> List[str]:
    """
    Telegram punya limit panjang pesan.
    Kita split supaya report panjang tidak gagal dikirim.
    """
    chunks = []

    if not text:
        return ["-"]

    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)

        if split_at == -1:
            split_at = limit

        chunks.append(text[:split_at])
        text = text[split_at:].strip()

    if text:
        chunks.append(text)

    return chunks


async def send_qa_result_to_topics(update, context, result: Dict[str, Any]) -> None:
    """
    Mengirim hasil QA ke dua topic:
    1. testing_summary ke topic tempat command dikirim
    2. documentation_report ke topic Documentation
    """
    chat_id = update.effective_chat.id
    testing_thread_id = update.effective_message.message_thread_id

    documentation_thread_id = get_int_env("TELEGRAM_DOCUMENTATION_THREAD_ID", 0)

    testing_summary = result.get("testing_summary", "-")
    documentation_report = result.get("documentation_report", "-")

    # 1. Kirim ringkasan ke topic Testing / topic asal command
    for chunk in split_telegram_message(testing_summary):
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=testing_thread_id,
            text=chunk,
        )

    # 2. Kirim dokumentasi lengkap ke topic Documentation
    if documentation_thread_id:
        for chunk in split_telegram_message(documentation_report):
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=documentation_thread_id,
                text=chunk,
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=testing_thread_id,
            text=(
                "⚠️ TELEGRAM_DOCUMENTATION_THREAD_ID belum ditemukan di .env. "
                "Dokumentasi QA belum bisa dikirim otomatis ke topic Documentation."
            ),
        )