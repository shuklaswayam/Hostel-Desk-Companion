# BCSE302P Database Management Systems — Project Report

## Project Title
**Hostel Parcel Desk: Smart Parcel Reception & Pickup Verification System**

---

## 1. Problem Statement & Background
In large college residential hostels (housing thousands of students across multiple blocks), daily volumes of e-commerce deliveries, couriers, and family parcels are extremely high. When reception staff record deliveries in manual paper logbooks or ad-hoc spreadsheets:
- Parcels frequently get misplaced across physical shelf racks.
- Collection status is either never updated or marked ambiguously without recipient verification.
- Receptionists face unauthorized package pickups, proxy claims, or duplicate collection disputes.
- Unclaimed packages remain indefinitely on storage shelves, congesting mailroom capacity.

**Hostel Parcel Desk** addresses these challenges through a centralized relational database management system. When a parcel arrives, reception staff log its unique carrier tracking number, recipient student, courier vendor, and allocated shelf rack. The database generates an unpredictable 6-digit pickup verification code and records a simulated notification. When the student arrives at reception, the database procedure verifies the code, enforces single-collection integrity, records the verifying officer, and automatically audits the status transition.

---

## 2. Main Objectives
1. **Student, Staff & Courier Record Management**: Maintain strict 3NF relations for residents, authorized reception staff, and delivery agencies.
2. **Centralized Registration & Inventory**: Enforce unique carrier tracking numbers and map packages to designated storage shelves.
3. **Cryptographic/PIN Pickup Verification**: Validate 6-digit pickup codes in the database prior to parcel release.
4. **Prevent Duplicate Claims & Tampering**: Enforce database constraints and procedure locks (`FOR UPDATE`) preventing double collection.
5. **Waiting Duration & Overdue Monitoring**: Compute elapsed hours using timestamp interval arithmetic (`fn_parcel_waiting_hours`) and report parcels exceeding 48 hours via explicit cursor (`c_unclaimed_parcels`).
6. **Automated Audit Trail**: Utilize row-level triggers (`trg_parcel_status_audit`) to record every status transition in `PARCEL_AUDIT`.
7. **Interactive Reception Web Interface**: Provide a modern dashboard for receptionists and wardens.

---

## 3. Entity-Relationship (ER) Architecture

```mermaid
erDiagram
    STUDENT ||--o{ PARCEL : receives
    STUDENT ||--o{ NOTIFICATION_LOG : notified_via
    STAFF ||--o{ PARCEL : registers
    STAFF ||--o{ PICKUP_RECORD : verifies
    COURIER ||--o{ PARCEL : delivers
    PARCEL ||--o| PICKUP_RECORD : has_collection
    PARCEL ||--o{ PARCEL_AUDIT : audits_transitions
    PARCEL ||--o{ NOTIFICATION_LOG : generates

    STUDENT {
        number student_id PK
        varchar reg_no UK
        varchar full_name
        varchar email UK
        varchar phone_no
        varchar hostel_block
        varchar room_no
    }

    STAFF {
        number staff_id PK
        varchar staff_code UK
        varchar full_name
        varchar email UK
        varchar staff_role
        char is_active
    }

    COURIER {
        number courier_id PK
        varchar company_name UK
        varchar contact_phone
        varchar service_type
    }

    PARCEL {
        number parcel_id PK
        varchar tracking_number UK
        number student_id FK
        number courier_id FK
        number registered_by FK
        timestamp arrival_time
        varchar shelf_location
        varchar pickup_code
        varchar status
    }

    PICKUP_RECORD {
        number pickup_id PK
        number parcel_id FK_UK
        number verified_by FK
        varchar collector_reg_no
        timestamp collected_at
        varchar verification_mode
    }

    PARCEL_AUDIT {
        number audit_id PK
        number parcel_id FK
        varchar old_status
        varchar new_status
        timestamp changed_at
        varchar changed_by
    }

    NOTIFICATION_LOG {
        number notification_id PK
        number parcel_id FK
        number student_id FK
        varchar notification_type
        varchar channel
        varchar message_body
        timestamp sent_at
    }
```

---

## 4. Normalization & 3NF Proof

### Functional Dependencies (FDs)
- **STUDENT**:
  - `student_id -> {reg_no, full_name, email, phone_no, hostel_block, room_no}`
  - `reg_no -> {student_id, full_name, email, phone_no, hostel_block, room_no}`
- **STAFF**:
  - `staff_id -> {staff_code, full_name, email, phone_no, staff_role, is_active}`
  - `staff_code -> {staff_id, full_name, ...}`
- **COURIER**:
  - `courier_id -> {company_name, contact_phone, service_type}`
- **PARCEL**:
  - `parcel_id -> {tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks}`
  - `tracking_number -> {parcel_id, ...}`
- **PICKUP_RECORD**:
  - `pickup_id -> {parcel_id, verified_by, collector_reg_no, collected_at, verification_mode, remarks}`
  - `parcel_id -> {pickup_id, ...}` (1:0..1 cardinality)
- **PARCEL_AUDIT**:
  - `audit_id -> {parcel_id, old_status, new_status, changed_at, changed_by}`
- **NOTIFICATION_LOG**:
  - `notification_id -> {parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status}`

### Normal Form Justification
1. **1NF Compliance**:
   - Every attribute contains only atomic, indivisible values.
   - Repeating groups (e.g. multiple items in a parcel or multiple collections) are eliminated by splitting them into dedicated relations.
2. **2NF Compliance**:
   - The relation is in 1NF.
   - All primary keys are single-attribute numeric surrogate keys (`parcel_id`, `student_id`, etc.). Therefore, no partial dependencies on composite keys exist.
3. **3NF Compliance**:
   - The relation is in 2NF.
   - No transitive functional dependencies exist ($X \to Y$ and $Y \to Z$).
   - Student demographic details (hostel block, room number, contact) are not duplicated inside `PARCEL`; only the foreign key `student_id` is maintained.
   - Courier contact details are not repeated in `PARCEL`.
   - Pickup verification data is isolated into `PICKUP_RECORD`, maintaining 3NF across all relations.

---

## 5. Required Database Objects (PL/SQL Specifications)

### 1. Function: `fn_parcel_waiting_hours`
- **Location**: `sql/03_functions.sql`
- **Signature**: `fn_parcel_waiting_hours(p_parcel_id NUMBER) RETURN NUMBER`
- **Description**: Performs exact timestamp arithmetic by calculating `SYSTIMESTAMP - arrival_time` and extracting day, hour, and minute components to return elapsed fractional hours.

### 2. Procedures: `pr_register_parcel` & `pr_verify_pickup`
- **Location**: `sql/05_procedures.sql`
- **`pr_register_parcel`**:
  - Validates foreign keys for student, courier, and active staff.
  - Generates a random 6-digit pickup PIN via `DBMS_RANDOM.VALUE(100000, 999999)`.
  - Enforces `UNIQUE` constraint on carrier tracking number.
  - Automatically registers initial notification in `NOTIFICATION_LOG`.
- **`pr_verify_pickup`**:
  - Locks target parcel with `SELECT ... FOR UPDATE OF p.status`.
  - Rejects pickup if status is already `COLLECTED` or `RETURNED`.
  - Compares submitted code with database pickup code.
  - Updates status to `COLLECTED` and inserts verification entry in `PICKUP_RECORD`.

### 3. Package: `pkg_parcel_operations`
- **Location**: `sql/06_package_spec.sql` & `sql/07_package_body.sql`
- **Description**: Encapsulates all hostel mailroom operations into a single modular PL/SQL interface with custom exceptions (`e_invalid_code`, `e_already_collected`).

### 4. Trigger: `trg_parcel_status_audit`
- **Location**: `sql/04_triggers.sql`
- **Type**: `AFTER UPDATE OF status ON PARCEL FOR EACH ROW WHEN (OLD.status != NEW.status)`
- **Description**: Automatically records every parcel state change in `PARCEL_AUDIT` along with the old status, new status, execution timestamp, and active user session.

### 5. Explicit Cursor: `c_unclaimed_parcels`
- **Location**: `sql/08_explicit_cursor.sql`
- **Description**: A parameterized explicit cursor iterating through unclaimed parcels where `status = 'PENDING'` and `waiting_hours >= p_threshold_hours` (48 hours), utilizing `OPEN`, `FETCH`, `%NOTFOUND`, and `CLOSE`.

---

## 6. Testing & Verification Matrix

| Test ID | Test Scenario | Database Rule Enforced | Expected Outcome | Actual Result | Status |
|:---|:---|:---|:---|:---|:---:|
| **TC-01** | Register valid parcel with unique tracking # | Primary Key & Foreign Key integrity | Parcel created with status `PENDING`, 6-digit PIN generated | Created Parcel #1007, PIN: 974280 | **PASS** |
| **TC-02** | Register duplicate tracking # | Unique constraint on `PARCEL.tracking_number` | Database rejects duplicate insert | `Constraint Violation: already registered` | **PASS** |
| **TC-03** | Submit incorrect pickup PIN | Stored procedure PIN validation | Collection rejected; status remains `PENDING` | `Rejection: Invalid pickup code entered` | **PASS** |
| **TC-04** | Submit correct 6-digit pickup PIN | Procedure status update & pickup log | Status transitions to `COLLECTED`, row added to `PICKUP_RECORD` | `Success! Parcel marked as COLLECTED` | **PASS** |
| **TC-05** | Attempt second pickup on collected parcel | Eligibility rule in `pr_verify_pickup` | Second collection rejected | `Rejection: has already been collected` | **PASS** |
| **TC-06** | Parcel status update | Row trigger `trg_parcel_status_audit` | Automatic record logged in `PARCEL_AUDIT` | Audit record logged: `PENDING -> COLLECTED` | **PASS** |
| **TC-07** | Execute cursor for overdue parcels | Explicit cursor `c_unclaimed_parcels` | Lists packages pending &ge; 48 hours | Identified 2 overdue parcels (#1003, #1004) | **PASS** |

---

## 7. Web Application Architecture
The web application is built with **Flask**, styled with a custom **glassmorphic design system**, and operates under a dual-mode database engine:
- **Oracle Mode**: Direct connection via `python-oracledb` Thin Mode (invoking PL/SQL procedures, packages, functions).
- **SQLite Mirror Engine**: Zero-configuration local engine mirroring the exact schema, triggers, and procedures for offline demonstrations.
