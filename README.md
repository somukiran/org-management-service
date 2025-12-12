# Organization Management Service

A multi-tenant backend service for managing organizations with dynamic MongoDB collections. Built with FastAPI and Python.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [API Documentation](#api-documentation)
- [Design Choices](#design-choices)
- [Trade-offs & Scalability](#trade-offs--scalability)

---

## 🎯 Overview

This service implements a multi-tenant architecture where:
- A **Master Database** stores global metadata (organizations, admin users)
- Each organization gets its own **dynamic MongoDB collection** for isolated data storage
- **JWT-based authentication** secures admin operations
- RESTful APIs provide CRUD operations for organization management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT APPLICATIONS                             │
│                        (Web App, Mobile App, etc.)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   API Routes    │  │   Services      │  │   Core                      │  │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌─────────┐ ┌───────────┐  │  │
│  │  │ /org/*    │  │  │  │ Org       │  │  │  │ Config  │ │ Security  │  │  │
│  │  │ /admin/*  │  │  │  │ Service   │  │  │  │         │ │ (JWT/Hash)│  │  │
│  │  └───────────┘  │  │  ├───────────┤  │  │  └─────────┘ └───────────┘  │  │
│  │  ┌───────────┐  │  │  │ Auth      │  │  └─────────────────────────────┘  │
│  │  │Dependencies│  │  │  │ Service   │  │                                   │
│  │  │ (Auth)    │  │  │  └───────────┘  │                                   │
│  │  └───────────┘  │  └─────────────────┘                                   │
│  └─────────────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE MANAGER                                    │
│                     (Connection Pool & Operations)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MONGODB                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      MASTER DATABASE                                 │    │
│  │  ┌─────────────────┐        ┌─────────────────┐                     │    │
│  │  │  organizations  │        │   admin_users   │                     │    │
│  │  │  Collection     │        │   Collection    │                     │    │
│  │  │  - name         │        │  - email        │                     │    │
│  │  │  - collection   │        │  - password_hash│                     │    │
│  │  │  - admin_id     │        │  - org_id       │                     │    │
│  │  │  - created_at   │        │  - role         │                     │    │
│  │  └─────────────────┘        └─────────────────┘                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 DYNAMIC ORGANIZATION COLLECTIONS                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  org_acme    │  │  org_beta    │  │  org_gamma   │    ...        │    │
│  │  │  Collection  │  │  Collection  │  │  Collection  │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Web framework - async, high performance, auto-docs |
| **MongoDB** | NoSQL database - flexible schema, scalable |
| **Motor** | Async MongoDB driver for Python |
| **Pydantic** | Data validation and settings management |
| **python-jose** | JWT token encoding/decoding |
| **passlib + bcrypt** | Secure password hashing |
| **Docker** | Containerization |
| **pytest** | Testing framework |

---

## ✨ Features

- ✅ **Organization CRUD Operations** - Create, read, update, delete organizations
- ✅ **Dynamic Collection Creation** - Each org gets isolated MongoDB collection
- ✅ **JWT Authentication** - Secure admin login with token-based auth
- ✅ **Password Hashing** - bcrypt for secure credential storage
- ✅ **Input Validation** - Pydantic schemas with custom validators
- ✅ **Auto-generated Docs** - Swagger UI and ReDoc
- ✅ **Docker Support** - Easy deployment with docker-compose

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10+
- MongoDB 6.0+ (or Docker)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd org-management-service

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

**Access:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- MongoDB Express: http://localhost:8081 (admin/admin123)

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your MongoDB URL

# Run the application
uvicorn app.main:app --reload --port 8000
```

### Running Tests

```bash
pytest tests/ -v
```

---

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/org/create` | Create organization | No |
| `GET` | `/org/get?organization_name=` | Get organization | No |
| `PUT` | `/org/update?current_org_name=` | Update organization | Yes |
| `DELETE` | `/org/delete?organization_name=` | Delete organization | Yes |
| `POST` | `/admin/login` | Admin login | No |
| `GET` | `/admin/me` | Get current admin | Yes |

### Example Usage

**1. Create Organization:**
```bash
curl -X POST "http://localhost:8000/org/create" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme_corp",
    "email": "admin@acme.com",
    "password": "SecurePass123"
  }'
```

**2. Login:**
```bash
curl -X POST "http://localhost:8000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "SecurePass123"
  }'
```

**3. Get Organization:**
```bash
curl "http://localhost:8000/org/get?organization_name=acme_corp"
```

**4. Delete Organization (with token):**
```bash
curl -X DELETE "http://localhost:8000/org/delete?organization_name=acme_corp" \
  -H "Authorization: Bearer <your_token>"
```

---

## 🎨 Design Choices

1. **Class-Based Services** - Clean separation of business logic
2. **Async MongoDB (Motor)** - Non-blocking I/O for better performance
3. **Collection-per-Org** - Data isolation between tenants
4. **JWT Authentication** - Stateless, scalable auth
5. **Pydantic Validation** - Type safety and auto-documentation

---

## ⚖️ Trade-offs & Scalability

### Is this a good architecture?

**For small-medium scale (100-1000 orgs): Yes ✅**
- Simple and maintainable
- Good data isolation
- Easy per-org backup/restore

**For large scale (10,000+ orgs): Consider alternatives ❌**

### Current Limitations

| Issue | Impact |
|-------|--------|
| Many collections | MongoDB connection overhead |
| No cross-org queries | Analytics difficult |
| Per-collection indexes | Maintenance overhead |

### Better Alternatives for Scale

**Option A: Single Collection + Tenant ID**
```
┌──────────────────────────────────┐
│     all_organizations_data       │
│  - tenant_id (indexed)           │
│  - data                          │
└──────────────────────────────────┘
```
- Pros: Easier management, cross-tenant queries
- Cons: Less isolation, needs careful access control

**Option B: Database-per-Tenant**
```
┌────────────┐ ┌────────────┐ ┌────────────┐
│ org_acme_db│ │org_beta_db │ │org_gamma_db│
└────────────┘ └────────────┘ └────────────┘
```
- Pros: Complete isolation, independent scaling
- Cons: Higher operational cost

### Recommended Improvements

1. Add **Redis caching** for frequent queries
2. Implement **rate limiting** 
3. Add **audit logging**
4. Set up **MongoDB replica set**
5. Add **Prometheus metrics**

---

## 📁 Project Structure

```
org-management-service/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   ├── dependencies.py  # Auth dependencies
│   │   └── routes/
│   │       ├── organization.py
│   │       └── admin.py
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── security.py      # JWT & hashing
│   ├── db/
│   │   └── database.py      # MongoDB manager
│   ├── schemas/
│   │   └── schemas.py       # Pydantic models
│   └── services/
│       ├── organization_service.py
│       └── auth_service.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 📄 License

MIT License

---

**Time Spent:** ~3 hours
