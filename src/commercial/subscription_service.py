from datetime import UTC, datetime, timedelta

from src.commercial.subscription_models import Subscription, SubscriptionStatus

_subscriptions: dict[int, Subscription] = {}


class SubscriptionService:
    def get(self, chat_id: int) -> Subscription:
        sub = _subscriptions.get(chat_id)
        if sub is None:
            return Subscription(chat_id=chat_id, status=SubscriptionStatus.FREE)
        return sub

    def activate(self, chat_id: int, payment_reference: str) -> Subscription:
        now = datetime.now(UTC)
        sub = Subscription(
            chat_id=chat_id,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            expiry_date=now + timedelta(days=30),
            payment_reference=payment_reference,
            created_at=now,
            updated_at=now,
        )
        _subscriptions[chat_id] = sub
        return sub

    def check_and_update(self, chat_id: int) -> Subscription:
        sub = self.get(chat_id)
        if sub.status == SubscriptionStatus.ACTIVE and sub.expiry_date:
            if datetime.now(UTC) > sub.expiry_date:
                sub.status = SubscriptionStatus.EXPIRED
                sub.updated_at = datetime.now(UTC)
                _subscriptions[chat_id] = sub
        return sub