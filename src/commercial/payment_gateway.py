"""Payment Gateway — boundary untuk provider pembayaran."""

from src.commercial.payment_provider_base import PaymentNotConfiguredError, PaymentProvider


class PaymentGateway:
    def __init__(self, provider: PaymentProvider | None = None):
        self.provider = provider

    def create_checkout(self, chat_id: int, plan: str, price: float) -> dict:
        if not self.provider:
            raise PaymentNotConfiguredError("Payment provider belum dikonfigurasi")
        # Asumsi provider.create_checkout async, dipanggil manual nanti
        raise PaymentNotConfiguredError("Payment provider belum dikonfigurasi")

    def verify_payment(self, payment_reference: str) -> bool:
        if not self.provider:
            return False
        raise PaymentNotConfiguredError("Payment provider belum dikonfigurasi")