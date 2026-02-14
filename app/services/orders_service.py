from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.order import Order
from app.schemas.order import OrderCreate

ALLOWED_STATUSES = {"pending", "paid", "shipped", "cancelled"}


def create_order(db: Session, payload: OrderCreate) -> Order:
    customer_name = payload.customer_name.strip()
    if not customer_name:
        raise ValueError("customer_name must not be empty")
    if payload.status not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise ValueError(f"status must be one of: {allowed}")
    if payload.total_amount <= 0:
        raise ValueError("total_amount must be greater than 0")

    order = Order(
        customer_name=customer_name,
        status=payload.status,
        total_amount=payload.total_amount,
    )
    try:
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Database integrity error occurred") from e
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Database error occurred") from e


def list_orders(
    db: Session,
    page: int,
    limit: int,
    status: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> tuple[list[Order], int]:
    if status is not None and status not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise ValueError(f"status must be one of: {allowed}")
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise ValueError("min_amount must be less than or equal to max_amount")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError("date_from must be earlier than or equal to date_to")

    filters = []
    if status is not None:
        filters.append(Order.status == status)
    if min_amount is not None:
        filters.append(Order.total_amount >= min_amount)
    if max_amount is not None:
        filters.append(Order.total_amount <= max_amount)
    if date_from is not None:
        filters.append(Order.created_at >= date_from)
    if date_to is not None:
        filters.append(Order.created_at <= date_to)

    offset = (page - 1) * limit
    count_stmt = select(func.count()).select_from(Order)
    query = select(Order).order_by(Order.id)
    if filters:
        count_stmt = count_stmt.where(*filters)
        query = query.where(*filters)

    try:
        total = db.scalar(count_stmt) or 0
        items = db.execute(query.offset(offset).limit(limit)).scalars().all()
        return items, total
    except SQLAlchemyError as e:
        raise ValueError(
            "Database error occurred while fetching orders") from e
