from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    status: str = Field(default="pending", min_length=1, max_length=30)
    total_amount: Decimal = Field(gt=0)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    status: str
    total_amount: Decimal
    created_at: datetime


class OrdersPage(BaseModel):
    items: list[OrderRead]
    page: int
    limit: int
    total: int
