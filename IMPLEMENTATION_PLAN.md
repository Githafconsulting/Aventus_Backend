# Contractor Onboarding Flow - Implementation Plan

## Overview

This plan updates the contractor onboarding flow to properly handle different routes with their specific requirements.

---

## Current Routes (5 Types)

| Route | Label | Description |
|-------|-------|-------------|
| **SAUDI** | Saudi Arabia | 3rd Party - Saudi Arabia |
| **UAE** | UAE | 3rd Party - UAE |
| **OFFSHORE** | Offshore | International Placement |
| **FREELANCER** | Freelancer | Independent Contractor |
| **WPS** | WPS | Work Permit System |

---

## Updated Onboarding Flow by Route

### Phase 1: Initial Steps (SAME FOR ALL ROUTES)
1. Consultant creates contractor (name, email, phone)
2. Contractor receives email with document upload link
3. Contractor uploads personal info + documents
4. **Route Selection** → Different flows begin

---

### Phase 2: Route-Specific Steps

#### 1. SAUDI (3rd Party - Saudi Arabia)
```
Documents Uploaded → Select Route → Quote Sheet (send to 3rd party, they fill & submit)
→ CDS Form → Costing Sheet → Submit for Admin Review
```
- Quote Sheet: Consultant sends request to Saudi 3rd party
- 3rd party fills and submits the quote sheet
- Then proceed with CDS & CS

#### 2. UAE (3rd Party - UAE)
```
Documents Uploaded → Select Route → COHF (Cost of Hire Form) FIRST
→ CDS Form → Costing Sheet → Submit for Admin Review
```
- **COHF comes BEFORE CDS & CS** (key difference)
- COHF workflow: Consultant fills → Sends to 3rd party → DocuSign process
- After COHF complete, proceed with CDS & CS

#### 3. OFFSHORE (International)
```
Documents Uploaded → Select Route → CDS Form → Costing Sheet → Submit for Admin Review
```
- Straightforward: Direct to CDS & CS

#### 4. FREELANCER
```
Documents Uploaded → Select Route → CDS Form → Costing Sheet → Submit for Admin Review
```
- Straightforward: Direct to CDS & CS
- **Separate from WPS** (distinct route)

#### 5. WPS (Work Permit System)
```
Documents Uploaded → Select Route → CDS Form → Costing Sheet → Submit for Admin Review
```
- Straightforward: Direct to CDS & CS
- **Separate from Freelancer** (distinct route)

---

### Phase 3: Admin Review & Approval (SAME FOR ALL)
- Admin/Superadmin reviews contractor details
- Approves or Rejects
- If rejected → back to editing
- If approved → proceed to next phase

---

### Phase 4: Work Order / Proposal (SAME FOR ALL)
- Generate Work Order (WO) OR Proposal
- Send to client for signature
- Client signs and submits
- Status: `WORK_ORDER_COMPLETED`

---

### Phase 5: Contract (ROUTE-DEPENDENT)

| Route | Contract Flow |
|-------|---------------|
| **SAUDI** | Aventus generates & sends contract to contractor |
| **UAE** | **UAE 3rd party sends THEIR contract to Aventus (consultant)** |
| **OFFSHORE** | Aventus generates & sends contract to contractor |
| **FREELANCER** | Aventus generates & sends contract to contractor |
| **WPS** | Aventus generates & sends contract to contractor |

**Key Difference for UAE:**
- UAE 3rd party handles contractor contract
- They upload/send signed contract to Aventus
- Consultant receives it (upload functionality needed)
- Aventus does NOT send a contract to contractor

---

### Phase 6: Activation (SAME FOR ALL)
- Admin activates contractor account
- Contractor receives login credentials
- Status: `ACTIVE`

---

## Implementation Tasks

### Backend Changes

#### Task 1: Update Contractor Model & Status
- [ ] Add new status for UAE contract upload workflow: `PENDING_3RD_PARTY_CONTRACT`
- [ ] Update business_type enum to match 5 routes
- [ ] Add field for 3rd party uploaded contract

#### Task 2: Update Route Selection Endpoint
- [ ] Ensure route selection properly sets business_type
- [ ] Handle route-specific redirects

#### Task 3: Update COHF Endpoints (UAE Route)
- [ ] Create/update COHF submission endpoint
- [ ] COHF should come BEFORE CDS in UAE flow
- [ ] Store COHF data in contractor record

#### Task 4: Create 3rd Party Contract Upload Endpoint (UAE Route)
- [ ] `POST /contractors/{id}/upload-3rd-party-contract`
- [ ] Accept contract file from 3rd party
- [ ] Update contractor status to `CONTRACT_UPLOADED`
- [ ] Skip normal contract generation for UAE

#### Task 5: Update Contract Flow Logic
- [ ] Skip contract generation for UAE route
- [ ] UAE route waits for 3rd party contract upload
- [ ] Other routes continue with normal contract generation

#### Task 6: Update Quote Sheet Flow (Saudi Route)
- [ ] Redesign quote sheet endpoints (you will provide design)
- [ ] 3rd party fills and submits quote sheet
- [ ] Consultant receives notification

---

### Frontend Changes

#### Task 7: Update Route Selection Page
- [ ] Keep 5 separate routes (WPS, Freelancer, UAE, Saudi, Offshore)
- [ ] Remove any "combined" logic for Freelancer/WPS
- [ ] Update routing logic per route type

#### Task 8: Update UAE Flow
- [ ] UAE route: Route Selection → COHF → CDS & CS → Review
- [ ] Redirect to COHF page after selecting UAE route
- [ ] After COHF complete, redirect to CDS form

#### Task 9: Update COHF Page
- [ ] Connect to actual backend endpoints
- [ ] Save COHF data to contractor
- [ ] After completion, redirect to CDS form (not contract generation)

#### Task 10: Create 3rd Party Contract Upload Page (UAE)
- [ ] New page: `/dashboard/contractors/[id]/upload-contract`
- [ ] Allow consultant to upload contract received from UAE 3rd party
- [ ] Show status of contract upload process

#### Task 11: Update Contractor Detail Page
- [ ] Show route-specific workflow status
- [ ] For UAE: Show "Waiting for 3rd Party Contract" status
- [ ] Display correct next action buttons based on route

#### Task 12: Update Workflow Stepper Component
- [ ] Show correct steps based on selected route
- [ ] UAE shows: COHF → CDS & CS → Review → WO → 3rd Party Contract → Activate
- [ ] Others show: CDS & CS → Review → WO → Contract → Activate
- [ ] Saudi shows: Quote Sheet → CDS & CS → Review → WO → Contract → Activate

---

### Quote Sheet Redesign (Saudi Route)

#### Task 13: Quote Sheet System (Pending your design)
- [ ] Redesign quote sheet page
- [ ] 3rd party receives link to fill quote sheet
- [ ] 3rd party submits quote sheet
- [ ] Consultant receives notification
- [ ] Waiting for your design input

---

## Status Flow Updates

### Current Statuses (Keep)
- `DRAFT`
- `PENDING_DOCUMENTS`
- `DOCUMENTS_UPLOADED`
- `PENDING_CDS_CS`
- `PENDING_REVIEW`
- `APPROVED`
- `PENDING_CLIENT_WO_SIGNATURE`
- `WORK_ORDER_COMPLETED`
- `PENDING_SIGNATURE`
- `SIGNED`
- `ACTIVE`
- `SUSPENDED`
- `CANCELLED`

### New/Updated Statuses
- `PENDING_COHF` - UAE route: Waiting for COHF completion
- `COHF_COMPLETED` - UAE route: COHF done, ready for CDS
- `PENDING_3RD_PARTY_CONTRACT` - UAE route: Waiting for 3rd party to send contract
- `PENDING_THIRD_PARTY_QUOTE` - Saudi route: Waiting for 3rd party quote sheet

---

## File Changes Summary

### Backend Files
1. `app/models/contractor.py` - Update ContractorStatus enum
2. `app/routes/contractors.py` - Update/add endpoints
3. `app/schemas/contractor.py` - Update schemas if needed

### Frontend Files
1. `app/dashboard/contractors/[id]/select-route/page.tsx` - Update routing logic
2. `app/dashboard/contractors/[id]/cohf/page.tsx` - Connect to backend, update flow
3. `app/dashboard/contractors/complete-cds/[id]/page.tsx` - Update flow for UAE
4. `app/dashboard/contractors/[id]/page.tsx` - Update status display
5. `lib/workflowConfig.ts` - Update workflow definitions
6. `types/contractor.ts` - Update types
7. NEW: `app/dashboard/contractors/[id]/upload-3rd-party-contract/page.tsx`

---

## Priority Order

1. **High Priority**: UAE flow (COHF before CDS, 3rd party contract upload)
2. **High Priority**: Separate WPS and Freelancer routes
3. **Medium Priority**: Saudi quote sheet redesign (waiting for design)
4. **Low Priority**: UI polish and workflow stepper updates

---

## Questions/Clarifications Needed

1. Quote Sheet design for Saudi route - awaiting your input
2. Should COHF data be stored as JSON in contractor record or separate table?
3. For UAE 3rd party contract upload - what file formats should be accepted?
4. Should there be email notifications when 3rd party uploads contract?

---

## Next Steps

1. Review and approve this plan
2. You provide Quote Sheet design for Saudi route
3. Begin implementation starting with backend changes
4. Test each route flow end-to-end
