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
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


def test_list_orders_pagination_page1(client):
    create_order(client, customer_name="A")
    create_order(client, customer_name="B")
    create_order(client, customer_name="C")

    response = client.get("/orders", params={"page": 1, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


def test_list_orders_pagination_page2(client):
    create_order(client, customer_name="A")
    create_order(client, customer_name="B")
    create_order(client, customer_name="C")

    response = client.get("/orders", params={"page": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 3


def test_list_orders_page_validation(client):
    response = client.get("/orders", params={"page": 0})
    assert response.status_code == 422


def test_filter_by_status(client):
    create_order(client, customer_name="A", status="paid")
    create_order(client, customer_name="B", status="pending")

    response = client.get("/orders", params={"status": "paid"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "paid"


def test_filter_by_min_amount(client):
    create_order(client, customer_name="A", total_amount=10)
    create_order(client, customer_name="B", total_amount=50)

    response = client.get("/orders", params={"min_amount": 20})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


def test_filter_by_max_amount(client):
    create_order(client, customer_name="A", total_amount=10)
    create_order(client, customer_name="B", total_amount=50)

    response = client.get("/orders", params={"max_amount": 20})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


def test_filter_by_date_range(client):
    first = create_order(client, customer_name="A").json()
    second = create_order(client, customer_name="B").json()

    now = datetime.utcnow()
    set_created_at(first["id"], now - timedelta(days=10))
    set_created_at(second["id"], now - timedelta(days=1))

    date_from = (now - timedelta(days=3)).isoformat()
    date_to = now.isoformat()

    response = client.get("/orders", params={"date_from": date_from, "date_to": date_to})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == second["id"]


def test_filter_invalid_amount_range(client):
    response = client.get("/orders", params={"min_amount": 50, "max_amount": 10})
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
