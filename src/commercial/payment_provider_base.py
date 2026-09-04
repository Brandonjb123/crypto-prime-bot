from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    @abstractmethod
    async def create_checkout(self, chat_id: int, plan: str, price: float) -> dict:
        """Return checkout payload: url, invoice_id, dsb."""
        ...

    @abstractmethod
    async def verify_payment(self, payment_reference: str) -> bool:
        """Verifikasi status pembayaran. Return True jika sukses."""
        ...


class PaymentNotConfiguredError(Exception):
    pass