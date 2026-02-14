from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
from app.main import app
from app.models.order import Order


def create_order(client, customer_name="Alice", status="pending", total_amount=10.5):
    return client.post(
        "/orders",
        json={
            "customer_name": customer_name,
            "status": status,
            "total_amount": total_amount,
        },
    )


def set_created_at(order_id: int, created_at: datetime) -> None:
    db = database.SessionLocal()
    try:
        order = db.get(Order, order_id)
        order.created_at = created_at
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_orders.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine)

    database.engine = engine
    database.SessionLocal = TestingSessionLocal
    database.init_db()

    with TestClient(app) as client:
        yield client

    database.Base.metadata.drop_all(bind=engine)


def test_create_order_success(client):
    response = create_order(client)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["customer_name"] == "Alice"
    assert data["status"] == "pending"


def test_create_order_empty_name(client):
    response = create_order(client, customer_name=" ")
    assert response.status_code == 400


def test_create_order_invalid_status(client):
    response = create_order(client, status="unknown")
    assert response.status_code == 400


def test_create_order_invalid_amount(client):
    response = create_order(client, total_amount=0)
    assert response.status_code == 422  # Pydantic validation


def test_list_orders_empty(client):
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_filter_by_status(client):
    create_order(client, customer_name="A", status="paid")
    create_order(client, customer_name="B", status="pending")

    response = client.get("/orders", params={"status": "paid"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "paid"


def test_filter_by_date_range(client):
    first = create_order(client, customer_name="A").json()
    second = create_order(client, customer_name="B").json()

    now = datetime.utcnow()
    set_created_at(first["id"], now - timedelta(days=10))
    set_created_at(second["id"], now - timedelta(days=1))

    date_from = (now - timedelta(days=3)).isoformat()
    date_to = now.isoformat()

    response = client.get(
        "/orders", params={"date_from": date_from, "date_to": date_to})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == second["id"]


def test_filter_by_amount_range(client):
    """Test filtering by min and max amount."""
    create_order(client, customer_name="A", total_amount=10)
    create_order(client, customer_name="B", total_amount=50)
    create_order(client, customer_name="C", total_amount=100)

    response = client.get(
        "/orders", params={"min_amount": 20, "max_amount": 80})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["customer_name"] == "B"


def test_filter_invalid_amount_range(client):
    response = client.get(
        "/orders", params={"min_amount": 50, "max_amount": 10})
    assert response.status_code == 400


def test_filter_invalid_date_range(client):
    response = client.get(
        "/orders",
        params={
            "date_from": "2024-02-10T00:00:00",
            "date_to": "2024-02-01T00:00:00",
        },
    )
    assert response.status_code == 400


def test_filter_invalid_status_value(client):
    """Test that invalid status value is rejected."""
    create_order(client, status="pending")
    response = client.get("/orders", params={"status": "invalid_status"})
    assert response.status_code == 400
    assert "status must be one of" in response.json()["detail"]


# ============== PAGINATION TESTS ==============


def test_pagination_defaults(client):
    """Test that default pagination values (page=1, limit=10) are applied."""
    for i in range(15):
        create_order(client, customer_name=f"Customer{i}")

    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] == 15
    assert len(data["items"]) == 10


def test_pagination_custom_page_and_limit(client):
    """Test custom page and limit together."""
    for i in range(25):
        create_order(client, customer_name=f"Customer{i}")

    response = client.get("/orders", params={"page": 3, "limit": 7})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 3
    assert data["limit"] == 7
    assert data["total"] == 25
    assert len(data["items"]) == 7


def test_pagination_limit_maximum(client):
    """Test maximum limit value (100)."""
    for i in range(105):
        create_order(client, customer_name=f"Customer{i}")

    response = client.get("/orders", params={"limit": 100})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 100
    assert data["limit"] == 100
    assert data["total"] == 105


def test_pagination_page_beyond_range(client):
    """Test requesting a page beyond available data."""
    create_order(client, customer_name="A")
    create_order(client, customer_name="B")

    response = client.get("/orders", params={"page": 10, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["page"] == 10
    assert data["total"] == 2


def test_pagination_last_page_partial(client):
    """Test last page with partial results."""
    for i in range(23):
        create_order(client, customer_name=f"Customer{i}")

    response = client.get("/orders", params={"page": 3, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 23


def test_pagination_invalid_page_zero(client):
    """Test that page=0 is rejected."""
    response = client.get("/orders", params={"page": 0})
    assert response.status_code == 422


def test_pagination_invalid_limit_exceeds_max(client):
    """Test that limit>100 is rejected."""
    response = client.get("/orders", params={"limit": 101})
    assert response.status_code == 422


# ============== COMBINED FILTERS TESTS ==============


def test_filter_status_and_amount(client):
    """Test combining status and amount filters."""
    create_order(client, customer_name="A", status="paid", total_amount=50)
    create_order(client, customer_name="B", status="paid", total_amount=150)
    create_order(client, customer_name="C", status="pending", total_amount=100)

    response = client.get(
        "/orders", params={"status": "paid", "min_amount": 100})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["customer_name"] == "B"


def test_filter_all_combined(client):
    """Test all filters combined: status, amount, date, and pagination."""
    now = datetime.utcnow()

    orders_data = [
        ("A", "paid", 50, now - timedelta(days=10)),
        ("B", "paid", 100, now - timedelta(days=5)),
        ("C", "paid", 150, now - timedelta(days=3)),
        ("D", "pending", 100, now - timedelta(days=2)),
        ("E", "shipped", 100, now - timedelta(days=1)),
    ]

    for name, status, amount, created in orders_data:
        order = create_order(client, customer_name=name,
                             status=status, total_amount=amount).json()
        set_created_at(order["id"], created)

    response = client.get("/orders", params={
        "page": 1,
        "limit": 10,
        "status": "paid",
        "min_amount": 75,
        "max_amount": 200,
        "date_from": (now - timedelta(days=7)).isoformat(),
        "date_to": now.isoformat(),
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # B and C
    assert data["total"] == 2


def test_filter_with_pagination(client):
    """Test that pagination works correctly with filters."""
    for i in range(20):
        status = "paid" if i % 2 == 0 else "pending"
        create_order(client, customer_name=f"Customer{i}", status=status)

    response = client.get("/orders", params={
        "page": 2,
        "limit": 3,
        "status": "paid",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["page"] == 2
    assert data["total"] == 10  # 10 paid orders total
    for item in data["items"]:
        assert item["status"] == "paid"
