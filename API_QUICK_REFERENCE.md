# Orders API - Quick Reference

## Base URL
```
http://localhost:8000
```

## Endpoints

### GET /orders - List Orders
```bash
curl "http://localhost:8000/orders?page=1&limit=10&status=paid&min_amount=50&max_amount=200"
```

**Query Parameters:**
- `page` (int, default: 1, min: 1)
- `limit` (int, default: 10, range: 1-100)
- `status` (string): `pending` | `paid` | `shipped` | `cancelled`
- `min_amount` (decimal, min: 0)
- `max_amount` (decimal, min: 0)
- `date_from` (ISO 8601 datetime)
- `date_to` (ISO 8601 datetime)

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "customer_name": "Alice Johnson",
      "status": "paid",
      "total_amount": "149.99",
      "created_at": "2026-02-14T10:30:00"
    }
  ],
  "page": 1,
  "limit": 10,
  "total": 42
}
```

---

### POST /orders - Create Order
```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Alice","status":"pending","total_amount":99.99}'
```

**Request Body:**
```json
{
  "customer_name": "Alice Johnson",
  "status": "pending",
  "total_amount": 99.99
}
```

**Validation:**
- `customer_name`: required, 1-100 chars, non-empty
- `status`: optional (default: "pending"), must be: pending | paid | shipped | cancelled
- `total_amount`: required, > 0

**Response (201):**
```json
{
  "id": 1,
  "customer_name": "Alice Johnson",
  "status": "pending",
  "total_amount": "99.99",
  "created_at": "2026-02-14T15:30:45.123456"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET) |
| 201 | Created (POST) |
| 400 | Bad Request (business logic error) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

---

## Common Errors

**Invalid Status:**
```json
{"detail": "status must be one of: cancelled, paid, pending, shipped"}
```

**Invalid Amount Range:**
```json
{"detail": "min_amount must be less than or equal to max_amount"}
```

**Invalid Date Range:**
```json
{"detail": "date_from must be earlier than or equal to date_to"}
```

**Empty Customer Name:**
```json
{"detail": "customer_name must not be empty"}
```

---

## Quick Examples

### Get all paid orders
```bash
curl "http://localhost:8000/orders?status=paid"
```

### Get orders over $100
```bash
curl "http://localhost:8000/orders?min_amount=100"
```

### Get page 3 with 20 items
```bash
curl "http://localhost:8000/orders?page=3&limit=20"
```

### Get orders from last month
```bash
curl "http://localhost:8000/orders?date_from=2026-01-01T00:00:00&date_to=2026-01-31T23:59:59"
```

### Create new order
```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Bob Smith","total_amount":149.99}'
```

---

## Python Client Example

```python
import requests

# List orders
response = requests.get("http://localhost:8000/orders", params={
    "page": 1,
    "limit": 10,
    "status": "paid",
    "min_amount": 50
})
orders = response.json()
print(f"Total: {orders['total']}")
for order in orders['items']:
    print(f"#{order['id']}: {order['customer_name']} - ${order['total_amount']}")

# Create order
response = requests.post("http://localhost:8000/orders", json={
    "customer_name": "Alice Johnson",
    "status": "pending",
    "total_amount": 99.99
})
new_order = response.json()
print(f"Created order #{new_order['id']}")
```

---

## Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

For detailed documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
