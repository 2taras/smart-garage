import os
import uuid
from dataclasses import dataclass
import aiohttp

@dataclass
class PaymentRequest:
    amount: float
    card_number: str
    description: str
    transaction_id: str = None

    @classmethod
    def create(cls, amount: float, card_number: str, description: str):
        return cls(
            transaction_id=str(uuid.uuid4()),
            amount=amount,
            card_number=card_number,
            description=description
        )

@dataclass
class PaymentResponse:
    status: str
    transaction_id: str
    amount: float = None
    error_message: str = None

class AsyncBankClient:
    def __init__(self):
        self.api_url = os.getenv("BANK_API_URL", "").rstrip('/')
        self.api_key = os.getenv("BANK_API_KEY")
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.api_key}"
        }
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def process_payment(self, payment: PaymentRequest) -> PaymentResponse:
        if not self._session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
            
        try:
            async with self._session.post(
                f"{self.api_url}/api/payment/process",
                headers=self.headers,
                json={
                    "transaction_id": payment.transaction_id,
                    "amount": payment.amount,
                    "card_number": payment.card_number,
                    "description": payment.description
                }
            ) as response:
                data = await response.json()
                if response.status == 200:
                    return PaymentResponse(
                        status="success",
                        transaction_id=payment.transaction_id,
                        amount=payment.amount
                    )
                else:
                    return PaymentResponse(
                        status="failed",
                        transaction_id=payment.transaction_id,
                        error_message=data.get('error_message', 'Unknown error')
                    )
        except Exception as e:
            return PaymentResponse(
                status="failed",
                transaction_id=payment.transaction_id,
                error_message=str(e)
            )