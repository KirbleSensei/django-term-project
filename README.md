# Campus Library — Django term project

A small library management app: **authors**, **books**, **physical copies**, **members** (linked to Django users), and **loans** with checkout and return. Built to align with a typical Django + network programming course rubric (CRUD, auth, search/filter, pagination, REST API, AJAX, third-party API, tests, deployment).

## Features (rubric mapping)

| Area | What is implemented |
|------|---------------------|
| Core | Full CRUD for books, authors, and copies; loan checkout/return; class-based views; templates and URL namespacing; `ModelForm` validation and `messages` for feedback. |
| Database | `ForeignKey`, `ManyToMany`, `OneToOne`; partial unique constraint so at most one **active** loan per copy; `PROTECT` on loan → copy; annotated book lists to avoid N+1. |
| UX | Bootstrap 5, responsive navbar and tables, overdue badges on loans. |
| Advanced (3+) | **Auth** (signup, login, logout); **authorization** (staff vs member for catalog edits and API writes); **search/filter** on books; **pagination** on lists; **DRF** JSON API under `/api/`; **AJAX** return on loan list; **Open Library** ISBN lookup for staff book form. |
| Docs | This README and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). |
| Tests | `python manage.py test catalog` — model rules, book list, staff create, API auth and scoping. |
| Deploy | `Procfile`, `runtime.txt`, production settings via `DJANGO_SETTINGS_MODULE=config.settings.production` (see below). |

### Issues resolved (debugging)

- **Active-loan rule**: Enforced both in `Loan.clean()` and with a conditional `UniqueConstraint` so a copy cannot have two open loans; members respect `max_active_loans`.
- **Staff vs member APIs**: Non-staff can list/create their own loans via DRF; updates/deletes restricted to staff.
- **Static files**: WhiteNoise + `collectstatic` for production hosting.

## Requirements

- Python **3.12** (see `runtime.txt`)
- pip + virtualenv

## Local setup

```powershell
cd django-term-project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ — you will be redirected to the book list. Log in as staff to manage catalog, copies, and member loans.

## REST API

With the dev server running and logged in (session cookie) or as staff for writes:

- `GET /api/books/` — list books (read-only for anonymous GET; writes staff-only).
- `GET|POST /api/loans/` — members see/create their loans; staff full access.

Pagination: `?page=2` (10 items per page, from `REST_FRAMEWORK` settings).

## Production (example: Render)

1. Create a **PostgreSQL** instance and copy its **Internal Database URL**.
2. Create a **Web Service** from this repo; build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
4. Set environment variables:

| Variable | Example |
|----------|---------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | long random string |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `your-app.onrender.com` |
| `DATABASE_URL` | from Render Postgres (internal URL) |
| `DATABASE_SSL_REQUIRE` | `true` (if your provider requires SSL) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://your-app.onrender.com` (comma-separated if several) |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` (default); set `false` only for special local HTTPS tests |

After deploy, put the public **https://…** URL in your assignment and confirm `/admin/` and the home page load.

> **Deployment URL (student): https://django-term-project.onrender.com**

## License

Educational use.
