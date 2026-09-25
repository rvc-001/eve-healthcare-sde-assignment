# EVE Healthcare — Diagnostic Test Booking API

A REST API backend for browsing diagnostic centres, booking tests, and processing payments via an idempotent webhook. Built as the EVE Healthcare SDE Intern assignment.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [API Endpoints](#api-endpoints)
4. [Architecture Decisions](#architecture-decisions)
5. [Database Schema](#database-schema)
6. [Getting Started — Local Setup](#getting-started--local-setup)
7. [Getting Started — Docker](#getting-started--docker)
8. [Testing](#testing)
9. [Environment Variables](#environment-variables)

---

## Tech Stack

| Layer              | Technology                      |
|--------------------|---------------------------------|
| Framework          | FastAPI (Python 3.12)           |
| Database           | PostgreSQL (Supabase)           |
| ORM                | SQLAlchemy 2.0                  |
| Migrations         | Alembic                         |
| Auth               | JWT (python-jose) + Bcrypt      |
| Caching            | Redis via fastapi-cache2        |
| Testing            | Pytest + HTTPX (in-memory SQLite) |
| Containerization   | Docker + Docker Compose         |

---

## Project Structure

```
EVE SDE PROJECT/
│
├── app/                             # Core application package
│   ├── models/                      # SQLAlchemy table definitions (Database layer)
│   │   ├── user.py                  # User table
│   │   ├── centre.py                # DiagnosticCentre and DiagnosticTest tables
│   │   ├── booking.py               # Booking table (with price snapshot)
│   │   ├── payment.py               # Payment table (with idempotency_key UNIQUE constraint)
│   │   ├── enums.py                 # Shared Enums: BookingStatus, PaymentStatus
│   │   └── common.py                # Shared column helpers (created_at, updated_at)
│   │
│   ├── routers/                     # HTTP transport layer (Controllers)
│   │   ├── auth.py                  # POST /signup, POST /login, GET /me
│   │   ├── centres.py               # GET /centres/, GET /centres/{id}, GET /tests/{id}
│   │   ├── bookings.py              # POST /bookings/, GET /bookings/, PATCH /bookings/{id}/cancel
│   │   └── payments.py              # POST /payments/, POST /payments/webhook
│   │
│   ├── services/                    # Business logic layer (decoupled from HTTP)
│   │   ├── auth_service.py          # Signup, login, JWT creation/verification
│   │   ├── centre_service.py        # Centre and test data access
│   │   ├── booking_service.py       # Create booking, cancel booking, list by user
│   │   └── payment_service.py       # Payment simulation + idempotent webhook processor
│   │
│   ├── schemas/                     # Pydantic request/response models (Validation layer)
│   │   ├── auth.py                  # SignupRequest, LoginRequest, UserResponse, TokenResponse
│   │   ├── centre.py                # DiagnosticCentreResponse, CentreWithTestsResponse
│   │   ├── booking.py               # BookingCreateRequest, BookingResponse
│   │   └── payment.py               # PaymentSimulateRequest, PaymentWebhookRequest
│   │
│   ├── utils/
│   │   ├── response.py              # Unified send_response() envelope helper
│   │   └── security.py             # hash_password(), verify_password()
│   │
│   ├── config.py                    # Settings loaded from .env via pydantic-settings
│   ├── database.py                  # SQLAlchemy engine, session factory, get_db dependency
│   ├── dependencies.py              # get_current_user() JWT auth dependency
│   └── main.py                      # FastAPI app instance, middleware, router registration
│
├── alembic/                         # Database migration engine (do not delete)
│   ├── versions/                    # Auto-generated migration scripts
│   │   └── f6656b2cbb3c_initial_migration.py
│   ├── env.py                       # Alembic runtime environment (reads DATABASE_URL)
│   └── script.py.mako               # Template for generating new migration files
│
├── tests/                           # Pytest test suite
│   ├── conftest.py                  # Fixtures: isolated in-memory DB, client, test_user, auth_headers
│   ├── test_auth.py                 # Signup, login, duplicate email, wrong password, /me
│   ├── test_bookings.py             # Create, list, cancel, edge cases (invalid ID, 403, 400)
│   └── test_payments.py             # Payment simulation, webhook, idempotency deduplication
│
├── .env                             # Local secrets (git-ignored)
├── .env.example                     # Template for required environment variables
├── .gitignore                       # Excludes .env, __pycache__, .pytest_cache
├── alembic.ini                      # Alembic CLI configuration
├── docker-compose.yml               # Starts: API + PostgreSQL + Redis
├── Dockerfile                       # Multi-step image build for the FastAPI app
├── generate_test_report.py          # End-to-end integration tester → writes test_results.csv
├── requirements.txt                 # Pinned Python dependencies
├── seed.py                          # Seeds diagnostic centres + tests into a fresh DB
└── test_results.csv                 # Auto-generated CSV report from generate_test_report.py
```

---

## API Endpoints

### Authentication
| Method | Endpoint        | Auth Required | Description                            |
|--------|-----------------|:-------------:|----------------------------------------|
| POST   | /v1/auth/signup | No            | Register a new user account            |
| POST   | /v1/auth/login  | No            | Login and receive a JWT access token   |
| GET    | /v1/auth/me     | Yes           | Get the currently authenticated user   |

### Diagnostic Centres
| Method | Endpoint                 | Auth Required | Description                                      |
|--------|--------------------------|:-------------:|--------------------------------------------------|
| GET    | /v1/centres/             | No            | List all diagnostic centres (cached 60s)         |
| GET    | /v1/centres/{id}         | No            | Get a centre with all its offered tests          |
| GET    | /v1/centres/tests/{id}   | No            | Get details and price of a specific test         |

### Bookings
| Method | Endpoint                     | Auth Required | Description                                            |
|--------|------------------------------|:-------------:|--------------------------------------------------------|
| POST   | /v1/bookings/                | Yes           | Book a test (snapshots price, status starts PENDING)   |
| GET    | /v1/bookings/                | Yes           | List all bookings for the logged-in user               |
| PATCH  | /v1/bookings/{id}/cancel     | Yes           | Cancel a PENDING booking (403 if not owner)            |

### Payments
| Method | Endpoint               | Auth Required | Description                                                 |
|--------|------------------------|:-------------:|-------------------------------------------------------------|
| POST   | /v1/payments/          | No            | Simulate payment gateway (80% SUCCESS / 20% FAILED)        |
| POST   | /v1/payments/webhook   | No            | Receive payment result and update booking status (idempotent)|

---

## Architecture Decisions

### 1. 3-Layer Architecture
The codebase is separated into three layers:

```
Request → Router (Transport) → Service (Business Logic) → Model (Database)
```

The Router layer has zero business logic. The Service layer has zero HTTP knowledge. This makes each layer independently testable and replaceable.

### 2. Idempotent Webhook
Payment providers like Stripe guarantee **at-least-once delivery** — the same webhook can fire multiple times on network failure. Our implementation handles this using a two-layer defence:

- **Layer 1 (Application):** On receiving a webhook, we query the `payments` table for the incoming `idempotency_key`. If found, we return `200 OK` immediately without touching the database.
- **Layer 2 (Database):** The `idempotency_key` column has a `UNIQUE` constraint. If two concurrent requests somehow bypass the application check simultaneously, PostgreSQL rejects the second `INSERT` with an `IntegrityError`. We catch this explicitly and roll back cleanly.

This guarantees exactly-once processing even under race conditions.

### 3. Price Snapshot on Booking
When a booking is created, the test's current price is copied into the `bookings.amount` column. This is not a foreign key reference to the live price — it is a snapshot. If a centre updates their test price tomorrow, no existing booking record is affected. This is the correct e-commerce pattern for financial data.

### 4. Caching
The `GET /v1/centres/` endpoint uses `@cache(expire=60)` from `fastapi-cache2`. On startup, the application attempts to connect to a Redis backend. If Redis is unavailable (e.g., running locally without Docker), it uses an `InMemoryBackend`. This means the caching code works in both environments.

### 5. Response Envelope
Every API endpoint returns the same JSON shape:
```json
{
  "success": true | false,
  "message": "Human-readable description",
  "data": { ... } | null
}
```
This predictability is critical for frontend teams and API consumers.

---

## Database Schema

```
users
  id (PK, UUID)
  email (UNIQUE)
  hashed_password
  full_name
  created_at, updated_at

diagnostic_centres
  id (PK, UUID)
  name, location
  created_at, updated_at

diagnostic_tests
  id (PK, UUID)
  centre_id (FK -> diagnostic_centres.id)
  name, description
  price (NUMERIC 10,2)
  created_at, updated_at

bookings
  id (PK, UUID)
  user_id (FK -> users.id ON DELETE CASCADE)
  test_id (FK -> diagnostic_tests.id ON DELETE RESTRICT)
  centre_id (FK -> diagnostic_centres.id ON DELETE RESTRICT)
  appointment_datetime
  amount (NUMERIC 10,2)   ← price snapshot at time of booking
  status (ENUM: PENDING | CONFIRMED | CANCELLED | FAILED)
  created_at, updated_at

payments
  id (PK, UUID)
  booking_id (FK -> bookings.id ON DELETE CASCADE)
  status (ENUM: SUCCESS | FAILED)
  idempotency_key (UNIQUE)  ← deduplication constraint
  provider_payment_id
  created_at, updated_at
```

---

## Getting Started — Local Setup

### Prerequisites
- Python 3.12+
- A running PostgreSQL instance (Supabase)

### Installation
```bash
pip install -r requirements.txt
```

### Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql://user:password@host:5432/eve_healthcare
JWT_SECRET=your_secret_key_here
CORS_ORIGINS=http://localhost:3000
```

### Run Migrations
```bash
alembic upgrade head
```

### Seed the Database
Populates diagnostic centres in Raipur, Bhilai, and Durg with test data:
```bash
python seed.py
```

### Start the Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Getting Started — Docker

Runs the full stack (API + PostgreSQL + Redis) with a single command. Migrations and seeding run automatically on startup.

```bash
docker-compose up --build
```

The API will be available at **http://localhost:8000**.

---

## Testing

### Unit Tests (Isolated In-Memory Database)
The pytest suite uses an in-memory SQLite database that is created fresh before every test and destroyed after. Your production database is never touched.

```bash
python -m pytest tests/ -v
```

**Test coverage:**
- Auth: signup success, duplicate email (409), login success, wrong password (401), protected route
- Bookings: create, list, cancel, invalid test ID (404), cancel already-cancelled (400), cancel other user's booking (403)
- Payments: simulate gateway, webhook processing, idempotency deduplication

### End-to-End Integration Reporter
Hits the live running server and writes a full pass/fail CSV report:

```bash
# Start server first, then:
python generate_test_report.py
```

Output is saved to `test_results.csv` with columns: Test Name, Input, Expected, Actual, Status.
