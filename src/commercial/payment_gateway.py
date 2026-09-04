from src.commercial.payment_provider_base import PaymentNotConfiguredError, PaymentProvider


class PaymentGateway:
    def __init__(self, provider: PaymentProvider | None = None):
        self.provider = provider

    async def create_checkout(self, chat_id: int, plan: str, price: float) -> dict:
        if not self.provider:
            raise PaymentNotConfiguredError("Payment provider belum dikonfigurasi")
        return await self.provider.create_checkout(chat_id, plan, price)

    async def verify_payment(self, payment_reference: str) -> bool:
        if not self.provider:
            return False
        return await self.provider.verify_payment(payment_reference)