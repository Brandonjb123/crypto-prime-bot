"""Telegram Notifier — mengirim notifikasi via TelegramService."""

from src.core.models.notification import NotificationMessage
from src.notification.base_notifier import BaseNotifier


class TelegramNotifier(BaseNotifier):
    def __init__(self, telegram_service) -> None:
        self.service = telegram_service

    def notify(self, message: NotificationMessage) -> None:
        # Asumsikan chat_id disimpan di konteks atau environment
        # Untuk sekarang, kirim ke admin (ADMIN_CHAT_ID dari config)
        from config.constants import ADMIN_CHAT_ID
        chat_id = ADMIN_CHAT_ID
        text = f"{message.title}\n{message.body}"
        # Jadwalkan send_message karena notify() adalah sync
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.service.send_message(chat_id, text))
        except RuntimeError:
            # Tidak ada event loop — skip (testing)
            pass