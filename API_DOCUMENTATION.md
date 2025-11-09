# Aventus HR API Documentation

Complete API reference for the Aventus HR Backend system.

## Base URL

```
Local Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Get Token

**POST** `/api/v1/auth/login-json`

**Request Body:**
```json
{
  "email": "admin@aventus.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Contractor Onboarding API

### Step 1: Create Contractor & Send Contract

**POST** `/api/v1/contractors/`

**Authentication:** Required (Admin/SuperAdmin)

**Description:** Admin creates contractor profile, generates contract, and sends email with signing link.

**Request Body:**
```json
{
  "first_name": "John",
  "surname": "Doe",
  "gender": "Male",
  "nationality": "American",
  "home_address": "123 Main Street",
  "address_line3": "Apartment 4B",
  "phone": "+1-555-0123",
  "email": "john.doe@example.com",
  "dob": "1990-05-15",

  "umbrella_company_name": "ABC Management Ltd",
  "company_name": "ABC Management",
  "company_reg_no": "123456789",

  "client_name": "Tech Corp International",
  "role": "Senior Software Engineer",
  "start_date": "2024-03-01",
  "end_date": "2024-12-31",
  "location": "New York, USA",
  "duration": "10 months",
  "currency": "USD",
  "client_charge_rate": "12000",
  "candidate_pay_rate": "10000"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending_signature",
  "first_name": "John",
  "surname": "Doe",
  "email": "john.doe@example.com",
  "contract_token": "abc123xyz789...",
  "sent_date": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**What happens:**
1. ✅ Contractor record created
2. ✅ Contract generated from template
3. ✅ Unique signing token created (expires in 72 hours)
4. ✅ Email sent to contractor with signing link
5. ✅ Status set to `pending_signature`

---

### Step 2: Get Contract for Signing (Contractor Portal)

**GET** `/api/v1/contractors/token/{token}`

**Authentication:** Not required (public endpoint)

**Description:** Contractor accesses this via email link to view contract before signing.

**Example:**
```
GET /api/v1/contractors/token/abc123xyz789...
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending_signature",
  "first_name": "John",
  "surname": "Doe",
  "email": "john.doe@example.com",
  "generated_contract": "# EMPLOYMENT AGREEMENT\n\n**This Employment Agreement**...",
  "token_expiry": "2024-01-18T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Cases:**
- `404`: Token not found
- `400`: Token expired or contract already processed

---

### Step 3: Sign Contract

**POST** `/api/v1/contractors/sign/{token}`

**Authentication:** Not required (token-based)

**Description:** Contractor submits their signature.

**Request Body:**
```json
{
  "signature_type": "typed",
  "signature_data": "John Doe"
}
```

OR for drawn signature:

```json
{
  "signature_type": "drawn",
  "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Contract signed successfully",
  "contractor_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "signed"
}
```

**What happens:**
1. ✅ Signature stored
2. ✅ Signed date recorded
3. ✅ Status changed to `signed`
4. ✅ Admin dashboard automatically updates

---

### Step 4: Submit CDS Form

**PUT** `/api/v1/contractors/{contractor_id}/cds-form`

**Authentication:** Required (Admin/SuperAdmin)

**Description:** Admin submits CDS form data (Step 2 in admin flow).

**Request Body:**
```json
{
  "data": {
    "passport_number": "AB1234567",
    "passport_expiry": "2028-05-15",
    "visa_type": "Employment Visa",
    "visa_number": "V123456",
    "iqama_number": "2123456789",
    "work_permit": "WP2024001",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+1-555-0199",
    "emergency_contact_relationship": "Spouse",
    "bank_name": "ABC Bank",
    "bank_account": "1234567890",
    "bank_swift": "ABCBUS33XXX"
  }
}
```

**Response:** `200 OK`
```json
{
  "message": "CDS form submitted successfully",
  "contractor_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Requirements:**
- Contract must be in `signed` status

---

### Step 5: Activate Contractor Account

**POST** `/api/v1/contractors/{contractor_id}/activate`

**Authentication:** Required (Admin/SuperAdmin)

**Description:** Creates user account and sends login credentials to contractor.

**Request:** No body required

**Response:** `200 OK`
```json
{
  "message": "Contractor account activated successfully",
  "contractor_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660f9511-f39c-52e5-b827-557766551111",
  "status": "active",
  "email_sent": true
}
```

**What happens:**
1. ✅ User account created with contractor role
2. ✅ Temporary password generated
3. ✅ Status changed to `active`
4. ✅ Email sent with login credentials
5. ✅ Contractor can now login

**Requirements:**
- Contract must be in `signed` status
- User account must not already exist

---

## Contractor Management APIs

### List All Contractors

**GET** `/api/v1/contractors/`

**Authentication:** Required

**Query Parameters:**
- `status_filter` (optional): Filter by status

**Examples:**
```
GET /api/v1/contractors/
GET /api/v1/contractors/?status_filter=pending_signature
GET /api/v1/contractors/?status_filter=active
```

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "first_name": "John",
    "surname": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "nationality": "American",
    "role": "Senior Software Engineer",
    "client_name": "Tech Corp International",
    "start_date": "2024-03-01",
    "signed_date": "2024-01-15T14:20:00Z",
    "activated_date": "2024-01-15T15:30:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Get Contractor Details

**GET** `/api/v1/contractors/{contractor_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "first_name": "John",
  "surname": "Doe",
  "gender": "Male",
  "nationality": "American",
  "home_address": "123 Main Street",
  "phone": "+1-555-0123",
  "email": "john.doe@example.com",
  "dob": "1990-05-15",
  "client_name": "Tech Corp International",
  "role": "Senior Software Engineer",
  "location": "New York, USA",
  "currency": "USD",
  "contract_token": "abc123...",
  "signature_type": "typed",
  "signature_data": "John Doe",
  "generated_contract": "# EMPLOYMENT AGREEMENT\n...",
  "sent_date": "2024-01-15T10:30:00Z",
  "signed_date": "2024-01-15T14:20:00Z",
  "activated_date": "2024-01-15T15:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T15:30:00Z"
}
```

---

### Delete Contractor

**DELETE** `/api/v1/contractors/{contractor_id}`

**Authentication:** Required (Admin/SuperAdmin)

**Response:** `200 OK`
```json
{
  "message": "Contractor deleted successfully"
}
```

---

## Authentication APIs

### Login (OAuth2)

**POST** `/api/v1/auth/login`

**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
username=admin@aventus.com&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Login (JSON)

**POST** `/api/v1/auth/login-json`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "email": "admin@aventus.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Get Current User

**GET** `/api/v1/auth/me`

**Authentication:** Required

**Response:**
```json
{
  "id": "770g0622-g40d-63f6-c938-668877662222",
  "name": "Admin User",
  "email": "admin@aventus.com",
  "role": "admin",
  "is_active": true,
  "is_first_login": false,
  "contractor_id": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Reset Password

**POST** `/api/v1/auth/reset-password`

**Authentication:** Required

**Request Body:**
```json
{
  "current_password": "admin123",
  "new_password": "newSecurePassword123!"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

---

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Testing with curl

### Complete Onboarding Flow

```bash
# 1. Login as admin
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aventus.com","password":"admin123"}' \
  | jq -r '.access_token')

# 2. Create contractor (Step 1)
CONTRACTOR=$(curl -s -X POST "http://localhost:8000/api/v1/contractors/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "surname": "Doe",
    "gender": "Male",
    "nationality": "American",
    "home_address": "123 Main St",
    "phone": "+1234567890",
    "email": "john.doe@example.com",
    "dob": "1990-01-01",
    "role": "Engineer",
    "client_name": "Tech Corp",
    "location": "NYC",
    "currency": "USD",
    "start_date": "2024-03-01",
    "end_date": "2024-12-31"
  }')

CONTRACTOR_ID=$(echo $CONTRACTOR | jq -r '.id')
CONTRACT_TOKEN=$(echo $CONTRACTOR | jq -r '.contract_token')

echo "Contractor ID: $CONTRACTOR_ID"
echo "Contract Token: $CONTRACT_TOKEN"

# 3. Get contract (as contractor - no auth)
curl -X GET "http://localhost:8000/api/v1/contractors/token/$CONTRACT_TOKEN"

# 4. Sign contract
curl -X POST "http://localhost:8000/api/v1/contractors/sign/$CONTRACT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signature_type": "typed",
    "signature_data": "John Doe"
  }'

# 5. Submit CDS form
curl -X PUT "http://localhost:8000/api/v1/contractors/$CONTRACTOR_ID/cds-form" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "passport": "AB123456",
      "visa": "V123456"
    }
  }'

# 6. Activate account
curl -X POST "http://localhost:8000/api/v1/contractors/$CONTRACTOR_ID/activate" \
  -H "Authorization: Bearer $TOKEN"

# 7. List all contractors
curl -X GET "http://localhost:8000/api/v1/contractors/" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rate Limiting

Currently no rate limiting is implemented. Consider adding rate limiting for production deployment.

---

## Pagination

List endpoints currently return all results. Consider implementing pagination for production with query parameters:
- `page`: Page number
- `per_page`: Items per page

---

## Webhook Events (Future)

Potential webhook events to implement:
- `contractor.created`
- `contractor.contract_sent`
- `contractor.contract_signed`
- `contractor.activated`
- `contractor.suspended`

---

## Support

For API support or questions, contact the development team.
