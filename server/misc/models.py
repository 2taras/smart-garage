from pydantic import BaseModel, constr
from typing import Annotated

class LocationData(BaseModel):
    latitude: float
    longitude: float

class LoginData(BaseModel):
    password: str

ConstrainedCardNumber = Annotated[str, {"pattern": r"^\d{16}$"}]

class PurchaseData(BaseModel):
    card_number: ConstrainedCardNumber