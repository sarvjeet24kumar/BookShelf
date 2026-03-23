# BookShelf

## 1. Project Overview

**BookShelf** is a production-ready **Multi-Tenant Library Management Backend** built using **Django + Django REST Framework (DRF)**.

It supports a **three-tier role hierarchy** — **Super Admin**, **Tenant Admin**, and **User** — with complete tenant isolation, secure JWT-based authentication, and integrated payment processing.

This project uses **`uv`** for dependency management and virtual environment handling.

---

## 2. Architecture

### Multi-Tenancy Model
- **Shared Database, Shared Schema**: All tenants share the same database with tenant isolation enforced at the application level.
- **Tenant Context**: Automatic tenant context management via middleware.
- **Data Isolation**: Tenant-aware managers ensure users only access their tenant's data.

### Role Hierarchy

| Role | Scope | Capabilities |
|------|-------|--------------|
| **Super Admin** | Platform-wide | Manage all tenants, tenant admins, platform settings |
| **Tenant Admin** | Single Tenant | Manage users, books, genres within their tenant |
| **User** | Single Tenant | Manage personal book library |

---

## 3. Key Features

### Authentication & Security
- JWT-based authentication with refresh tokens
- Email verification with OTP
- Password reset via email
- Role-based access control (RBAC)
- Tenant-aware authentication middleware

### Multi-Tenant Features
- Complete tenant data isolation
- Tenant admins can only view their own tenant details
- Soft delete with data retention
- Subscription plan management (Free/Premium)

### Book Management
- Personal book library (CRUD)
- Book request system with approval workflow
- Genre categorization
- Book status tracking (To Read, Reading, Completed)

### Payments
- Razorpay integration for subscriptions
- Secure webhook handling
- Payment verification & activation

### Background Tasks
- Celery + Redis for async processing
- Email notifications 
- Scheduled tasks with Celery Beat

---

## 4. Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.13 |
| **Framework** | Django 6.0, Django REST Framework |
| **Database** | PostgreSQL |
| **Cache & Broker** | Redis |
| **Task Queue** | Celery + Celery Beat |
| **Authentication** | JWT (Simple JWT) |
| **Payments** | Razorpay |
| **Package Manager** | uv |

---

## 5. Project Structure

```
bookshelf/
├── accounts/           # User authentication & management
│   ├── models.py       # Custom User model
│   ├── serializers/    # Auth & user serializers
│   ├── services/       # Business logic (auth, email)
│   ├── views/          # Auth & user API views
│   ├── tasks.py        # Email notification tasks
│   └── urls.py
│
├── books/              # Book & library management
│   ├── models/         # Book, Genre, UserBook, BookRequest
│   ├── serializers/    # Book-related serializers
│   ├── views/          # Book API views
│   ├── filters.py      # Search & filtering
│   ├── mixins.py       # Reusable view mixins
│   └── urls.py
│
├── tenants/            # Multi-tenancy management
│   ├── models.py       # Tenant model
│   ├── middleware.py   # Tenant context middleware
│   ├── authentication.py # Tenant-aware JWT auth
│   ├── serializers/    # Tenant serializers
│   ├── views/          # Tenant API views
│   └── urls.py
│
├── payments/           # Payment & subscription management
│   ├── models/         # Subscription, Payment, Order
│   ├── services/       # Razorpay integration
│   ├── views/          # Payment API views
│   └── urls.py
│
├── common/             # Shared utilities
│   ├── models.py       # Base models (soft delete, timestamps)
│   ├── managers.py     # Tenant-aware & soft delete managers
│   ├── permissions.py  # Custom permission classes
│   ├── middleware.py   # Request logging, exception handling
│   ├── exceptions.py   # Custom exception hierarchy
│   ├── enums.py        # Application enums
│   ├── validators.py   # Shared validators
│   └── pagination.py   # Custom pagination
│
├── config/             # Django configuration
│   ├── settings/       # Split settings (base, dev, prod)
│   ├── celery.py       # Celery configuration
│   ├── logging.py      # Logging configuration
│   └── urls.py         # Root URL configuration
│
├── manage.py
├── pyproject.toml
└── uv.lock
```

---

## 6. Environment Variables

Create a `.env` file based on `.env.example`:

```ini
# Application
ENVIRONMENT=dev
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB_NAME

# Redis & Celery
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Razorpay
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@bookshelf.com

# Super Admin (for create_superadmin command)
SUPERADMIN_USERNAME=superadmin
SUPERADMIN_EMAIL=admin@bookshelf.com
SUPERADMIN_PASSWORD=YourSecurePassword123!
SUPERADMIN_FIRST_NAME=Super
SUPERADMIN_LAST_NAME=Admin
SUPERADMIN_PHONE=0000000000
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.13+
- PostgreSQL
- Redis

### Install Dependencies

```bash
uv sync
```

### Run Migrations

```bash
uv run python manage.py migrate
```

### Create Super Admin (via Seed)
```bash
uv run python manage.py create_superadmin
```


### Start Development Server

```bash
uv run python manage.py runserver
```

### Start Celery Worker

```bash
uv run celery -A config worker -l info
```

### Start Celery Beat (Scheduler)

```bash
uv run celery -A config beat -l info
```

Application will be available at: `http://127.0.0.1:8000`

---

