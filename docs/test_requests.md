# API Test Requests

Base URL: `http://localhost:8000/api`

---

## 1. User Registration

### Success

```bash
curl -s -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "strongpass123",
    "password_repeat": "strongpass123",
    "first_name": "Alice",
    "last_name": "Smith"
  }' | python3 -m json.tool
```

**Expected:** 201 Created, user JSON with `id`, `email`, `first_name`, `last_name`.

### Password Mismatch

```bash
curl -s -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "strongpass123",
    "password_repeat": "different",
    "first_name": "Alice",
    "last_name": "Smith"
  }' | python3 -m json.tool
```

**Expected:** 400 Bad Request, `{"password_repeat": ["Passwords do not match."]}`.


---

## 2. Get User Detail

```bash
curl -s -X GET http://localhost:8000/api/users/1/ | python3 -m json.tool
```

**Expected:** 200 OK, user JSON with `id`, `email`, `first_name`, `last_name`, `email_verified`, `date_joined`.

---

## 3. Verify Email

First, grab a token value from your test user's `email_verification_tokens` table:

```bash
# If psql is available:
docker compose exec postgres psql -U admin -d drf_celery_tutorial \
  -c "SELECT token FROM users_emailverificationtoken WHERE user_id=1 LIMIT 1;"
```

### Success

```bash
curl -s -X POST http://localhost:8000/api/verify-email/<UUID>/ | python3 -m json.tool
```

**Expected:** 200 OK, `{"detail": "Email was successfully verified."}`.

### Invalid or Expired Token

```bash
curl -s -X POST http://localhost:8000/api/verify-email/00000000-0000-0000-0000-000000000000/ | python3 -m json.tool
```

**Expected:** 404 Not Found, `{"detail": "Invalid or expired token."}`.

### Malformed UUID

```bash
curl -s -X POST http://localhost:8000/api/verify-email/not-a-uuid/ | python3 -m json.tool
```

**Expected:** 404 Not Found.
