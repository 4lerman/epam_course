# Orders API with Pagination

A RESTful API built with FastAPI for managing orders with comprehensive pagination, filtering, and validation capabilities. Uses SQLite for data persistence and SQLAlchemy for ORM.

## Features

- ✅ Create and list orders
- ✅ Pagination support with customizable page size
- ✅ Advanced filtering by:
  - Status (pending, paid, shipped, cancelled)
  - Amount range (min/max)
  - Date range (created_at)
- ✅ Input validation with detailed error messages
- ✅ SQLite database with SQLAlchemy ORM
- ✅ Service layer architecture
- ✅ Comprehensive test suite (14 tests)
- ✅ Database seeding script

## Project Structure

```
mod7_p3/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app with uvicorn runner
│   ├── database.py             # Database configuration and session
│   ├── models/
│   │   ├── __init__.py
│   │   └── order.py           # Order SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── order.py           # Pydantic schemas (request/response)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── orders.py          # Orders endpoints
│   └── services/
│       ├── __init__.py
│       └── orders_service.py  # Business logic layer
├── tests/
│   ├── __init__.py
│   └── test_orders.py         # Test suite
├── seed_orders.py             # Database seeding script
├── requirements.txt
├── pytest.ini
└── README.md
```

## Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Start the server:
```bash
python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **Alternative docs (ReDoc)**: http://localhost:8000/redoc

### Seed sample data (optional):
```bash
python seed_orders.py
```
This creates 50 sample orders with varied data.

## API Endpoints

### POST /orders
Create a new order.

**Request body:**
```json
{
  "customer_name": "Alice Johnson",
  "status": "pending",
  "total_amount": 42.50
}
```

**Response (201):**
```json
{
  "id": 1,
  "customer_name": "Alice Johnson",
  "status": "pending",
  "total_amount": 42.50,
  "created_at": "2026-02-09T10:30:00"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Alice","status":"paid","total_amount":99.99}'
```

### GET /orders
List orders with pagination and filtering.

**Query parameters:**
- `page` (int, default: 1) - Page number (≥1)
- `limit` (int, default: 10) - Items per page (1-100)
- `status` (str, optional) - Filter by status: pending, paid, shipped, cancelled
- `min_amount` (decimal, optional) - Minimum order amount
- `max_amount` (decimal, optional) - Maximum order amount
- `date_from` (datetime, optional) - Filter from date (ISO 8601)
- `date_to` (datetime, optional) - Filter to date (ISO 8601)

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "customer_name": "Alice Johnson",
      "status": "paid",
      "total_amount": 99.99,
      "created_at": "2026-02-09T10:30:00"
    }
  ],
  "page": 1,
  "limit": 10,
  "total": 1
}
```

**Examples:**
```bash
# Basic pagination
curl "http://localhost:8000/orders?page=1&limit=20"

# Filter by status
curl "http://localhost:8000/orders?status=paid"

# Filter by amount range
curl "http://localhost:8000/orders?min_amount=50&max_amount=200"

# Filter by date range
curl "http://localhost:8000/orders?date_from=2026-01-01T00:00:00&date_to=2026-12-31T23:59:59"

# Combined filters
curl "http://localhost:8000/orders?page=1&limit=10&status=paid&min_amount=100"
```

## Validation Rules

### Order creation:
- `customer_name`: Required, non-empty after trimming (max 100 chars)
- `status`: Must be one of: pending, paid, shipped, cancelled
- `total_amount`: Must be greater than 0

### Filtering:
- `min_amount` ≤ `max_amount` (if both provided)
- `date_from` ≤ `date_to` (if both provided)

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

**Test coverage:**
- ✅ CRUD operations
- ✅ Pagination (page 1, page 2, validation)
- ✅ Filtering (status, amount range, date range)
- ✅ Edge cases (empty results, invalid ranges)
- ✅ Input validation (empty names, invalid status, invalid amounts)

## Technologies

- **FastAPI** - Modern web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Embedded database
- **Pydantic** - Data validation using Python type annotations
- **Pytest** - Testing framework
- **Uvicorn** - ASGI server

## License

MIT
