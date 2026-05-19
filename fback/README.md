# fback — Portfolio Contact Form Backend

FastAPI + PostgreSQL backend for your portfolio contact form.

## Project Structure

```
fback/
├── app/
│   ├── main.py          # FastAPI app, CORS, rate limiting setup
│   ├── config.py        # Settings via .env
│   ├── database.py      # Async SQLAlchemy engine + session
│   ├── models.py        # Message ORM model
│   ├── schemas.py       # Pydantic request/response schemas
│   └── routers/
│       ├── contact.py   # POST /api/v1/contact  (public)
│       └── admin.py     # /api/v1/admin/*        (JWT protected)
├── alembic/             # Database migrations
├── frontend_contact.js  # Drop-in JS for your portfolio HTML
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Clone & install

```bash
cd fback
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL, ADMIN_PASSWORD, JWT_SECRET
```

### 3. Create PostgreSQL database

```sql
CREATE DATABASE fback;
```

### 4. Run migrations

```bash
# Generate first migration
alembic revision --autogenerate -m "create messages table"

# Apply it
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Reference

### Public

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/contact` | Submit contact form |

**POST /api/v1/contact** — rate limited to 5/minute per IP
```json
{
  "name": "Priya Sharma",
  "email": "priya@company.com",
  "budget": "₹25,000 – ₹75,000",
  "message": "I need a portfolio website..."
}
```
Response:
```json
{ "success": true, "message": "Thanks! I'll get back to you within 24 hours.", "id": 1 }
```

---

### Admin (JWT required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/admin/login` | Get JWT token |
| GET | `/api/v1/admin/dashboard` | Stats overview |
| GET | `/api/v1/admin/messages` | List messages |
| GET | `/api/v1/admin/messages/{id}` | Get single message |
| PATCH | `/api/v1/admin/messages/{id}` | Update status / notes |
| DELETE | `/api/v1/admin/messages/{id}` | Delete message |

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'
```

**List messages (with token):**
```bash
curl http://localhost:8000/api/v1/admin/messages \
  -H "Authorization: Bearer <token>"
```

**Filter by status:**
```
GET /api/v1/admin/messages?status=unread&page=1&limit=20
```

**Search:**
```
GET /api/v1/admin/messages?search=priya
```

**Update status:**
```bash
curl -X PATCH http://localhost:8000/api/v1/admin/messages/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "replied", "notes": "Replied via email on 15 May"}'
```

**Message statuses:** `unread` → `read` → `replied` → `archived` / `spam`

---

## Frontend Integration

Replace `handleSend()` in your portfolio HTML with the contents of `frontend_contact.js`.
Change `API_BASE` to your deployed backend URL:

```js
const API_BASE = "https://api.yourdomain.com/api/v1";
```

---

## Deployment (Railway / Render / VPS)

1. Push to GitHub
2. Set all `.env` variables in your hosting dashboard
3. Use `DATABASE_URL` from your hosted PostgreSQL instance
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Run migrations: `alembic upgrade head`
6. Update `allow_origins` in `app/main.py` to your frontend domain

---

## Security Notes

- Change `ADMIN_PASSWORD` and `JWT_SECRET` before deploying
- Set `DEBUG=false` in production
- Add your frontend domain to `allow_origins` (remove `"*"`)
- Consider adding HTTPS-only in production via your hosting provider
