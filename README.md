# Aventus HR Backend

Backend API for the Aventus HR Contractor Management System built with FastAPI, PostgreSQL (Supabase), and Resend for email.

## Features

- **Contractor Onboarding Flow**
  - Step 1: Admin creates contractor profile and sends contract for signing
  - Step 2: Contractor reviews and signs contract electronically
  - Step 3: Admin completes CDS form
  - Step 4: Admin activates account and system sends login credentials

- **Authentication & Authorization**
  - JWT-based authentication
  - Role-based access control (Super Admin, Admin, Manager, Contractor)
  - Password reset functionality

- **Email Notifications**
  - Contract signing invitations
  - Account activation with credentials
  - Password reset emails

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **Email**: Resend
- **Password Hashing**: Passlib with bcrypt

## Project Structure

```
aventus-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   └── contractor.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── auth.py
│   │   └── contractor.py
│   ├── routes/              # API endpoints
│   │   ├── auth.py
│   │   └── contractors.py
│   └── utils/               # Utilities
│       ├── auth.py          # JWT & password handling
│       ├── email.py         # Email service
│       └── contract_template.py
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── seed_db.py              # Database seeding script
├── run.py                  # Development server
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- PostgreSQL database (Supabase account)
- Resend account (for email)

### 2. Clone and Install

```bash
# Navigate to backend directory
cd "Aventus Backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and configure:

#### Supabase Database

1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Go to Settings > Database
4. Copy the connection string
5. Update `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

#### Resend Email Service

1. Go to [Resend](https://resend.com)
2. Sign up for free account (3,000 emails/month)
3. Create an API key
4. Update in `.env`:

```env
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=onboarding@resend.dev  # Use this for testing
```

#### JWT Secret Key

Generate a secure secret key:

```bash
# On Mac/Linux:
openssl rand -hex 32

# On Windows (PowerShell):
python -c "import secrets; print(secrets.token_hex(32))"
```

Update `SECRET_KEY` in `.env`

#### Frontend URLs

```env
FRONTEND_URL=http://localhost:3000
CONTRACT_SIGNING_URL=http://localhost:3000/contract/sign
PASSWORD_RESET_URL=http://localhost:3000/reset-password
```

### 4. Initialize Database

Run the seed script to create tables and test users:

```bash
python seed_db.py
```

This creates three test users:
- **Super Admin**: superadmin@aventus.com / superadmin123
- **Admin**: admin@aventus.com / admin123
- **Manager**: manager@aventus.com / manager123

### 5. Run Development Server

```bash
python run.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

#### POST `/api/v1/auth/login`
Login with OAuth2 form data
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@aventus.com&password=admin123"
```

#### POST `/api/v1/auth/login-json`
Login with JSON body
```json
{
  "email": "admin@aventus.com",
  "password": "admin123"
}
```

#### GET `/api/v1/auth/me`
Get current user info (requires authentication)

#### POST `/api/v1/auth/reset-password`
Reset password (requires authentication)
```json
{
  "current_password": "admin123",
  "new_password": "newpassword123"
}
```

### Contractor Management

#### POST `/api/v1/contractors/`
**Create contractor (Step 1)** - Admin only
```json
{
  "first_name": "John",
  "surname": "Doe",
  "gender": "Male",
  "nationality": "American",
  "home_address": "123 Main St",
  "phone": "+1234567890",
  "email": "john.doe@example.com",
  "dob": "1990-01-01",
  "role": "Software Engineer",
  "client_name": "Tech Corp",
  "location": "New York",
  "currency": "USD",
  "start_date": "2024-02-01",
  "end_date": "2024-12-31",
  "duration": "11 months"
}
```

**Response**: Contractor created, contract email sent

#### GET `/api/v1/contractors/`
List all contractors (with optional status filter)
```bash
GET /api/v1/contractors/?status_filter=pending_signature
```

#### GET `/api/v1/contractors/{contractor_id}`
Get contractor details by ID (requires auth)

#### GET `/api/v1/contractors/token/{token}`
Get contractor details by token (no auth - for signing portal)

#### POST `/api/v1/contractors/sign/{token}`
**Sign contract** - No auth required
```json
{
  "signature_type": "typed",  // or "drawn"
  "signature_data": "John Doe"  // or base64 image
}
```

#### PUT `/api/v1/contractors/{contractor_id}/cds-form`
**Submit CDS form (Step 2)** - Admin only
```json
{
  "data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

#### POST `/api/v1/contractors/{contractor_id}/activate`
**Activate contractor account (Step 3)** - Admin only

**Response**: Account created, credentials email sent

#### DELETE `/api/v1/contractors/{contractor_id}`
Delete contractor - Admin only

## Contractor Onboarding Workflow

### Flow Diagram

```
┌─────────────┐
│   ADMIN     │
│  Dashboard  │
└──────┬──────┘
       │
       │ 1. Fill Step 1 form
       │    POST /contractors/
       ▼
┌─────────────────────┐
│  Status: PENDING    │ ───────┐
│   SIGNATURE         │        │ 2. Email sent with
└─────────────────────┘        │    contract link
                                │
                                ▼
                       ┌──────────────┐
                       │ CONTRACTOR   │
                       │ Receives     │
                       │ Email        │
                       └──────┬───────┘
                              │
                              │ 3. Click link
                              │    GET /contractors/token/{token}
                              ▼
                       ┌──────────────┐
                       │ Review       │
                       │ Contract     │
                       └──────┬───────┘
                              │
                              │ 4. Sign contract
                              │    POST /contractors/sign/{token}
                              ▼
                       ┌──────────────┐
                       │ Status:      │
                       │ SIGNED       │
                       └──────┬───────┘
                              │
                              │ 5. Admin notified
                              ▼
                       ┌──────────────┐
                       │ ADMIN        │
                       │ Dashboard    │
                       └──────┬───────┘
                              │
                              │ 6. Fill Step 2: CDS form
                              │    PUT /contractors/{id}/cds-form
                              ▼
                       ┌──────────────┐
                       │ Submit       │
                       │ CDS Form     │
                       └──────┬───────┘
                              │
                              │ 7. Click Activate
                              │    POST /contractors/{id}/activate
                              ▼
                       ┌──────────────┐
                       │ Status:      │
                       │ ACTIVE       │
                       └──────┬───────┘
                              │
                              │ 8. Account created
                              │    Credentials email sent
                              ▼
                       ┌──────────────┐
                       │ CONTRACTOR   │
                       │ Can login    │
                       └──────────────┘
```

## Database Models

### User
- Authentication and authorization
- Roles: superadmin, admin, manager, contractor
- JWT token-based authentication

### Contractor
- Complete contractor information
- Contract status tracking
- Electronic signature storage
- CDS form data (JSON)
- Generated contract content

## Status Flow

```
DRAFT → PENDING_SIGNATURE → SIGNED → ACTIVE → SUSPENDED
```

- **DRAFT**: Initial creation (unused in current flow)
- **PENDING_SIGNATURE**: Contract sent, awaiting signature
- **SIGNED**: Contract signed, awaiting CDS form + activation
- **ACTIVE**: Account activated, contractor can login
- **SUSPENDED**: Account suspended

## Testing

### Using FastAPI Docs (Recommended)

1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Login with test credentials
4. Test endpoints interactively

### Using curl

```bash
# Login
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aventus.com","password":"admin123"}' \
  | jq -r '.access_token')

# Create contractor
curl -X POST "http://localhost:8000/api/v1/contractors/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","surname":"Doe",...}'

# List contractors
curl -X GET "http://localhost:8000/api/v1/contractors/" \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Check your `DATABASE_URL` in `.env` and ensure Supabase project is active

### Email Not Sending

```
Failed to send contract email: ...
```

**Solutions**:
1. Verify `RESEND_API_KEY` is correct
2. Check `FROM_EMAIL` is verified in Resend
3. For testing, use `onboarding@resend.dev`

### Import Errors

```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Ensure you're in the correct directory and virtual environment is activated

### JWT Token Expired

```
401 Unauthorized: Could not validate credentials
```

**Solution**: Login again to get a new token. Default expiry is 30 minutes.

## Production Deployment

### Environment Variables

Update these for production:
- `DEBUG=False`
- Use strong `SECRET_KEY`
- Update `FRONTEND_URL` to production domain
- Configure proper `FROM_EMAIL` domain

### Security Checklist

- [ ] Use HTTPS only
- [ ] Set strong SECRET_KEY
- [ ] Enable database SSL
- [ ] Configure CORS properly
- [ ] Use environment variables (never commit .env)
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Enable logging and monitoring

## Contributing

This is a project for Aventus HR system. For questions or issues, contact the development team.

## License

Proprietary - Aventus HR System
