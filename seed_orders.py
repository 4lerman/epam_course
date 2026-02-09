"""Script to seed the database with 50 sample orders."""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import SessionLocal, init_db
from app.models.order import Order

CUSTOMER_NAMES = [
    "Alice Johnson",
    "Bob Smith",
    "Charlie Brown",
    "Diana Prince",
    "Eve Adams",
    "Frank Miller",
    "Grace Lee",
    "Henry Zhang",
    "Iris Wang",
    "Jack Wilson",
]

STATUSES = ["pending", "paid", "shipped", "cancelled"]


def create_sample_orders(count: int = 50):
    """Create sample orders with varied data."""
    init_db()
    db = SessionLocal()

    try:
        now = datetime.utcnow()
        orders = []

        for i in range(count):
            # Random data
            customer_name = random.choice(CUSTOMER_NAMES)
            status = random.choice(STATUSES)
            total_amount = Decimal(str(round(random.uniform(5.0, 500.0), 2)))
            created_at = now - timedelta(days=random.randint(0, 90))

            order = Order(
                customer_name=customer_name,
                status=status,
                total_amount=total_amount,
                created_at=created_at,
            )
            orders.append(order)

        db.add_all(orders)
        db.commit()
        print(f"✓ Created {count} sample orders successfully!")

    except Exception as e:
        db.rollback()
        print(f"✗ Error creating orders: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_orders(50)
