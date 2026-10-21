# Hostel Parcel Desk — Smart Parcel Reception & Pickup Verification System
**Coursework**: BCSE302P Database Management Systems  
**Domain**: Campus Logistics & Student Services  

A complete database application for hostel reception staff and wardens to log arriving parcels, assign storage shelves, generate 6-digit verification pickup codes, verify student collections, flag overdue unclaimed packages, and maintain a trigger-driven audit trail.

---

## 🌟 Key Features
- **7-Table Relational Schema in 3NF**: Complete normalization ensuring zero data redundancy.
- **All 5 Required PL/SQL Objects**:
  1. `fn_parcel_waiting_hours`: Function calculating fractional waiting duration.
  2. `pr_register_parcel`: Procedure creating parcel & generating 6-digit PIN.
  3. `pr_verify_pickup`: Procedure validating pickup code and preventing double-collection.
  4. `pkg_parcel_operations`: Modular package bundling procedures, functions, and metrics.
  5. `trg_parcel_status_audit`: Row-level trigger logging all status changes to `PARCEL_AUDIT`.
  6. `c_unclaimed_parcels`: Explicit parameterized cursor scanning overdue packages.
- **Dual-Mode Database Engine**:
  - **Oracle Mode**: Connects directly via `python-oracledb` Thin Mode (no Oracle Client download required).
  - **SQLite Demo Mirror**: Runs instantly out-of-the-box for local testing and presentation without external database setup.
- **Modern Glassmorphic Web Dashboard**:
  - Live KPI cards (Total Received, Awaiting Pickup, Collected, Overdue).
  - Searchable and filterable parcel directory.
  - Pickup Verification Station with PIN validator and collection receipts.
  - Interactive Overdue Scanner with `DBMS_OUTPUT` console simulation.
  - Security Audit Trail & Notification Dispatch view.
  - Dark / Light mode toggle.

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
cd /Users/swayamshukla/DBMS
pip3 install -r requirements.txt
```

### 2. Run Automated Test Suite (7 Coursework Test Cases)
```bash
python3 test_system.py
```
This runs all 7 test cases specified in the project problem statement (verifying unique tracking constraints, PIN authentication, duplicate pickup blocking, trigger logging, and explicit cursor execution).

### 3. Launch Web Application
```bash
python3 app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📂 Project Structure
```
DBMS/
├── app.py                     # Flask web server & REST API
├── config.py                  # Application & database settings (.env loader)
├── database.py                # Dual-mode DB manager (Oracle Thin & SQLite Mirror)
├── requirements.txt           # Python dependencies
├── test_system.py             # Automated test suite for all 7 test cases
├── README.md                  # Quickstart documentation
│
├── sql/                       # Native Oracle PL/SQL Scripts
│   ├── 01_create_schema.sql   # DDL for 7 tables, sequences, PK/FK/CHECK constraints
│   ├── 02_seed_data.sql       # Realistic sample data (students, staff, couriers, parcels)
│   ├── 03_functions.sql       # fn_parcel_waiting_hours
│   ├── 04_triggers.sql        # trg_parcel_status_audit
│   ├── 05_procedures.sql      # pr_register_parcel & pr_verify_pickup
│   ├── 06_package_spec.sql    # pkg_parcel_operations specification
│   ├── 07_package_body.sql    # pkg_parcel_operations package body
│   ├── 08_explicit_cursor.sql # c_unclaimed_parcels anonymous block
│   └── 09_test_suite.sql      # PL/SQL test runner
│
├── templates/
│   └── index.html             # Reception dashboard HTML single-page app
│
├── static/
│   ├── css/
│   │   └── styles.css         # Modern glassmorphism theme (Dark & Light)
│   └── js/
│       └── dashboard.js       # Dynamic frontend logic & API handlers
│
└── docs/
    └── PROJECT_REPORT.md      # Academic report (ER diagrams, 3NF proof, DBMS specs)
```

---

## 🗄️ Running with Oracle Database
If connecting to an Oracle Database instance (e.g., Oracle XE, Oracle Cloud, or Oracle 23ai):
1. Execute scripts `01_create_schema.sql` through `07_package_body.sql` in Oracle SQL Developer or Live SQL.
2. Create a `.env` file in the project root:
   ```env
   DB_MODE=oracle
   ORACLE_USER=system
   ORACLE_PASSWORD=your_password
   ORACLE_HOST=localhost
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=XEPDB1
   ```
3. Run `python3 app.py`. The dashboard will automatically connect in Oracle PL/SQL mode!
