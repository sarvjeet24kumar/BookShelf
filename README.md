
# BookShelf

## 1. Project Overview

**BookShelf** is a real-world **Library Management Backend** built using **Django + Django REST Framework (DRF)**.
It supports two roles  **User** and **Admin**  and provides secure, role based APIs for managing personal book collections and platform administration.

This project uses **`uv`** for dependency management and virtual environment handling.



## 2. Key Features

1. JWT-based authentication (Register / Login).
2. Users can manage their own books (CRUD).
3. Strict book ownership enforcement.
4. Role-based access control (User / Admin).
5. Admin APIs for user management.
6. Admin statistics endpoint for platform insights.
7. Clean RESTful API design.



## 3. Tech Stack

* Python 3.13
* Django 6.0
* Django REST Framework
* PostgreSQL
* JWT Authentication
* **uv** (dependency & env management)
* `pyproject.toml` + `uv.lock`


## 4. Environment Variables

Create a `.env` file:

```ini
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=


# Database¸
DJANGO_DB_ENGINE=
DJANGO_DB_NAME=
DJANGO_DB_USER=
DJANGO_DB_PASSWORD=
DJANGO_DB_HOST=
DJANGO_DB_PORT=

```


## 5. Run migrations

```bash
uv run python manage.py migrate
```



## 6. Create Admin user

```bash
uv run python manage.py createsuperuser
```



## 7. Start development server

```bash
uv run python manage.py runserver
```

Application will be available at:

```
http://127.0.0.1:8000
```



## 8. API Authentication

All protected APIs require JWT access token.

```http
Authorization: Bearer <access_token>
```



## 9. Folder Structure

```bash
book_shelf
.
├── accounts
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations
│   │   ├── __init__.py
│   ├── models.py
│   ├── serializers
│   │   └── __init__.py
│   ├── tests.py
│   └── views
│       └── __init__.py
├── books
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations
│   │   ├── __init__.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── common
│   ├── __init__.py
│   ├── constants.py
│   └── enums.py
├── config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── main.py
├── manage.py
├── pyproject.toml
├── README.md
└── uv.lock
```