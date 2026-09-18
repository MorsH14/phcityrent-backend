# PHCityRent — Backend Engineer Take-Home Assessment

## Overview

A small rental-platform API built with Django and Django REST Framework, backed by PostgreSQL. It covers tenant/landlord authentication, property listing with filtering, a tenant application workflow with role-based approval, automatic lease creation on approval, and a mock payment flow with an idempotent webhook and commission calculation.

**Author's note on background:** I'm primarily a frontend/Node developer (NestJS, Prisma, Express) and this was my first time working with Django, DRF, or Python. I used AI assistance (Claude) throughout — for translating my existing backend concepts (auth, ORMs, REST design, transactions) into Django/DRF syntax, and for working through debugging sessions — while I drove the architecture decisions, tested every endpoint myself, and made sure I could explain each piece before moving on. Specific instances of that process are called out in "Development process & AI disclosure" below.

---

## Tech stack

- Python 3.11, Django 5.2, Django REST Framework
- PostgreSQL 15
- `djangorestframework-simplejwt` for JWT auth
- `django-filter` for query-param filtering

---

## Setup instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (running locally or reachable)

### 1. Clone and enter the project
```bash
git clone <your-repo-url>
cd phcityrent-backend
```

### 2. Create and activate a virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate      # macOS/Linux
```

### 3. Install dependencies
```bash
pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary django-filter
```

### 4. Create the database
```bash
createdb phcityrent
```

### 5. Configure environment / settings
`config/settings.py` currently points at a local PostgreSQL instance:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'phcityrent',
        'USER': '<your-db-user>',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```
> In a production setting these values (and `SECRET_KEY`) would move to environment variables rather than being committed in `settings.py`. Flagged here as a known limitation — see below.

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Create a superuser (optional, for the Django admin panel)
```bash
python manage.py createsuperuser
```

### 8. Run the server
```bash
python manage.py runserver
```
API is now available at `http://127.0.0.1:8000/`.

---

## Running the tests

```bash
python manage.py test
```

**Actual output from this project:**
```
Found 19 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...................
----------------------------------------------------------------------
Ran 19 tests in 25.786s

OK
Destroying test database for alias 'default'...
```

Breakdown (19 tests total):
- `accounts` (4): registration succeeds and hashes correctly, duplicate usernames rejected, login returns JWT tokens, wrong password rejected.
- `properties` (5): list returns all available properties, filtering by location matches, filtering by location excludes non-matches, filtering by min price excludes cheaper properties, empty result set returns cleanly.
- `applications` (6): tenant can create an application, **tenant cannot approve their own application** (403), landlord can approve, a landlord who does not own the property cannot decide on it (403), an already-approved application cannot be approved again (400), a tenant only sees their own applications.
- `payments` (4): payment initiation returns a `PENDING` payment with the correct amount, a webhook confirms a payment and creates a matching commission, **a duplicate webhook delivery does not create a second commission**, an unknown payment reference returns 404.

---

## API endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/accounts/register/` | none | Register a new user (tenant or landlord) |
| POST | `/api/token/` | none | Log in, returns `access` + `refresh` JWT tokens |
| POST | `/api/token/refresh/` | none | Exchange a refresh token for a new access token |
| GET | `/api/properties/` | none | List properties (paginated, filterable) |
| GET | `/api/properties/<id>/` | none | Property detail |
| POST | `/api/applications/` | tenant (any authenticated user) | Submit an application for a property |
| GET | `/api/applications/mine/` | authenticated | List the current user's own applications |
| POST | `/api/applications/<id>/decision/` | property's landlord only | Approve or reject an application |
| POST | `/api/payments/` | authenticated | Initiate a payment for a lease |
| POST | `/api/payments/webhook/` | none (mock provider) | Confirm a payment (idempotent) |

### Property filters (query params on `GET /api/properties/`)
- `location` — case-insensitive partial match
- `min_price` / `max_price` — numeric range
- `is_available` — boolean
- Results are paginated (10 per page) and ordered newest-first.

### Example requests

Register:
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant1", "email": "t1@example.com", "password": "password123", "role": "TENANT"}'
```

Log in:
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant1", "password": "password123"}'
```

Apply for a property:
```bash
curl -X POST http://127.0.0.1:8000/api/applications/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"property": 1, "message": "Interested in this property"}'
```

Landlord approves (also creates the lease):
```bash
curl -X POST http://127.0.0.1:8000/api/applications/1/decision/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <landlord_access_token>" \
  -d '{"status": "APPROVED", "start_date": "2026-10-01", "end_date": "2027-09-30"}'
```

Initiate a payment:
```bash
curl -X POST http://127.0.0.1:8000/api/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <tenant_access_token>" \
  -d '{"lease": 1}'
```

Simulate the payment provider's webhook:
```bash
curl -X POST http://127.0.0.1:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"reference": "<payment_reference>", "event": "payment.success"}'
```

---

## Architecture & design decisions

### Custom User model with roles
Django's default `User` model has no concept of tenant vs. landlord, and Django requires deciding on a custom user model before the first migration. `accounts.User` extends `AbstractUser` with a `role` field (`TENANT` / `LANDLORD`), set as `AUTH_USER_MODEL` from the very first migration.

### Authentication vs. authorization, explicitly separated
JWT (`djangorestframework-simplejwt`) handles **authentication** — proving who a user is. A separate custom permission class, `IsPropertyLandlord`, handles **authorization** — whether that authenticated user is allowed to approve/reject a *specific* application (only the landlord who owns the property in question, never the tenant, and never a different landlord). This split is exercised directly by three tests: a tenant is blocked from approving their own application, a landlord who doesn't own the property is blocked, and the correct landlord succeeds.

### Application state machine
`Application.status` moves `PENDING → APPROVED` or `PENDING → REJECTED` only. Transitions are validated against an explicit `ALLOWED_TRANSITIONS` map in the view, so an already-`APPROVED` application cannot be approved again — this is tested directly.

### Lease creation rule
**A `Lease` is created automatically, in the same request and the same database transaction, the moment an `Application` transitions to `APPROVED`.** This was a deliberate choice to avoid a window where an application is `APPROVED` but no lease exists yet. It's implemented with `django.db.transaction.atomic()` wrapping both the status update and the lease creation, so either both succeed or neither does. `Lease` has a `OneToOneField` to `Application`, enforcing at the database level that an application can never have more than one lease.

### Payments: never trust the client, only the webhook
A payment starts `PENDING` when a tenant initiates it (amount is taken from the lease server-side, never from client input). It only becomes `SUCCESSFUL` when the mock payment webhook confirms it — the client-side "I paid" step never marks anything as successful.

### Idempotent webhook handling
Each `Payment` gets a random `UUID` `reference` at creation (`unique=True` at the database level). The webhook:
1. Checks the reference exists (`404` if not) with a lightweight, lock-free lookup.
2. Inside a `transaction.atomic()` block, re-fetches the payment with `select_for_update()` — a row-level database lock — so two near-simultaneous webhook deliveries for the same payment can't both read `PENDING` and both process.
3. If the payment is already `SUCCESSFUL`, returns `200 "Already processed."` without doing anything further (a payment provider expects a success response even for a duplicate delivery, so it stops retrying).
4. Otherwise, marks it `SUCCESSFUL`, stamps `confirmed_at`, and creates the matching `Commission` — all in the same transaction.

This is verified with an automated test that sends the identical webhook payload twice and asserts only one `Commission` row exists afterward.

### Commission rule
Flat **10%** of the payment amount (`COMMISSION_RATE = 10` in `payments/models.py`), calculated with `Decimal` arithmetic (never floats, to avoid rounding errors with money) and rounded to 2 decimal places. Both the calculated `amount` and the `rate` used are stored on the `Commission` record, so the record is self-explanatory later even if the rate constant changes going forward.

### Money and dates
All monetary fields use `DecimalField`, never `FloatField`, throughout the project.

---

## Known limitations / what I'd improve with more time

- **Webhook authenticity is not verified.** A real integration would verify a signature header from the payment provider before trusting the webhook body. Out of scope here since the brief specifies a mock provider, but I'd add it before this touched real payments.
- **Secrets are not externalized.** `SECRET_KEY` and database credentials currently live in `settings.py` rather than environment variables — fine for a local take-home, not for production.
- **No refund/failed-payment path.** `Payment.Status.FAILED` exists on the model but there's no endpoint that transitions a payment there yet.
- **No rate limiting** on the public endpoints (registration, webhook).
- **Test coverage is deep on the highest-risk paths (permissions, state transitions, idempotency) rather than exhaustive everywhere** — I prioritized the areas the brief calls out as automatic red flags over broad shallow coverage.

---

## Development process & AI disclosure

I used Claude (Anthropic) throughout this project as a learning and pairing tool, given this was my first time working with Django/DRF/Python — my background is NestJS/Prisma/TypeScript. Specifically:

- Claude explained Django/DRF/Python concepts by mapping them to their NestJS/Prisma equivalents I already knew (e.g., serializers ↔ DTOs, permission classes ↔ Guards, migrations ↔ Prisma migrate, `transaction.atomic()` ↔ `$transaction()`).
- I typed and ran every command myself, and tested every endpoint by hand with `curl` before considering it done.
- Several real bugs came up during development and were diagnosed and fixed, not just patched by re-generating code:
  - A `DEFAULT_FILTER_BACKENDS` setting was missing, so property filters were silently ignored — traced by testing the filter class directly in the Django shell, isolating it from the view layer, before finding the missing setting.
  - A stale `runserver` process was serving old code after an edit — diagnosed by using Django's shell/test client to prove the underlying code was correct before concluding the issue was environmental, then confirmed by killing all running server processes and starting fresh.
  - `select_for_update()` was initially called outside of a transaction in the webhook handler, which Postgres/Django correctly rejects — fixed by moving the row lock inside the `transaction.atomic()` block, exactly where locking is valid.
- I asked Claude to explain each fix rather than just apply it, specifically so I could defend the code and its edge cases in a live discussion.

---

## Postman / API collection

A collection matching the endpoints above (with example bodies) can be exported from the `curl` commands in this README. *(If a Postman/Bruno export file is included in this submission, reference it here.)*