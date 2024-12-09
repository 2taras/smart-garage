from pydantic import BaseModel, constr

class LocationData(BaseModel):
    latitude: float
    longitude: float

class LoginData(BaseModel):
    password: str

class PurchaseData(BaseModel):
    card_number: constr(regex=r'^\d{16}$')