-- ============================================================================
-- SUPABASE POSTGRESQL SCHEMA & INITIAL SEED SCRIPT
-- Project: Hostel Parcel Desk
-- Description: Run this script directly in the Supabase SQL Editor.
-- ============================================================================

-- Clean up any existing tables in proper dependency order
DROP TABLE IF EXISTS NOTIFICATION_LOG CASCADE;
DROP TABLE IF EXISTS PARCEL_AUDIT CASCADE;
DROP TABLE IF EXISTS PICKUP_RECORD CASCADE;
DROP TABLE IF EXISTS PARCEL CASCADE;
DROP TABLE IF EXISTS COURIER CASCADE;
DROP TABLE IF EXISTS STAFF CASCADE;
DROP TABLE IF EXISTS STUDENT CASCADE;

-- ----------------------------------------------------------------------------
-- 1. STUDENT REGISTRY
-- ----------------------------------------------------------------------------
CREATE TABLE STUDENT (
    student_id      SERIAL PRIMARY KEY,
    reg_no          VARCHAR(20) NOT NULL UNIQUE,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone_no        VARCHAR(20) NOT NULL,
    hostel_block    VARCHAR(20) NOT NULL CHECK (hostel_block IN ('Block A', 'Block B', 'Block C', 'Block D', 'Block E')),
    room_no         VARCHAR(20) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. RECEPTION STAFF & WARDENS
-- ----------------------------------------------------------------------------
CREATE TABLE STAFF (
    staff_id        SERIAL PRIMARY KEY,
    staff_code      VARCHAR(20) NOT NULL UNIQUE,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone_no        VARCHAR(20) NOT NULL,
    staff_role      VARCHAR(30) NOT NULL DEFAULT 'Receptionist' CHECK (staff_role IN ('Receptionist', 'Warden', 'Supervisor')),
    is_active       VARCHAR(1) NOT NULL DEFAULT 'Y' CHECK (is_active IN ('Y', 'N'))
);

-- ----------------------------------------------------------------------------
-- 3. COURIER AGENCIES
-- ----------------------------------------------------------------------------
CREATE TABLE COURIER (
    courier_id      SERIAL PRIMARY KEY,
    company_name    VARCHAR(100) NOT NULL UNIQUE,
    contact_phone   VARCHAR(30),
    service_type    VARCHAR(50) NOT NULL DEFAULT 'Standard',
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. PARCEL INTAKE RECORDS
-- ----------------------------------------------------------------------------
CREATE TABLE PARCEL (
    parcel_id       SERIAL PRIMARY KEY,
    tracking_number VARCHAR(100) NOT NULL UNIQUE,
    student_id      INTEGER NOT NULL REFERENCES STUDENT(student_id) ON DELETE RESTRICT,
    courier_id      INTEGER NOT NULL REFERENCES COURIER(courier_id) ON DELETE RESTRICT,
    registered_by   INTEGER NOT NULL REFERENCES STAFF(staff_id) ON DELETE RESTRICT,
    arrival_time    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    shelf_location  VARCHAR(50) NOT NULL,
    pickup_code     VARCHAR(10) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COLLECTED', 'OVERDUE', 'RETURNED')),
    remarks         TEXT
);

-- ----------------------------------------------------------------------------
-- 5. PICKUP & HANDOVER RECORDS
-- ----------------------------------------------------------------------------
CREATE TABLE PICKUP_RECORD (
    pickup_id        SERIAL PRIMARY KEY,
    parcel_id        INTEGER NOT NULL UNIQUE REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
    verified_by      INTEGER NOT NULL REFERENCES STAFF(staff_id) ON DELETE RESTRICT,
    collector_reg_no VARCHAR(20) NOT NULL,
    collected_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verification_mode VARCHAR(30) NOT NULL DEFAULT 'CODE_VERIFIED',
    remarks          TEXT
);

-- ----------------------------------------------------------------------------
-- 6. AUDIT LOG (Status Transitions)
-- ----------------------------------------------------------------------------
CREATE TABLE PARCEL_AUDIT (
    audit_id         SERIAL PRIMARY KEY,
    parcel_id        INTEGER NOT NULL REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
    old_status       VARCHAR(20) NOT NULL,
    new_status       VARCHAR(20) NOT NULL,
    changed_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    changed_by       VARCHAR(50) NOT NULL DEFAULT 'Reception Desk'
);

-- ----------------------------------------------------------------------------
-- 7. NOTIFICATION LOG (Email & Dispatch History)
-- ----------------------------------------------------------------------------
CREATE TABLE NOTIFICATION_LOG (
    notification_id   SERIAL PRIMARY KEY,
    parcel_id         INTEGER NOT NULL REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
    student_id        INTEGER NOT NULL REFERENCES STUDENT(student_id) ON DELETE RESTRICT,
    notification_type VARCHAR(30) NOT NULL CHECK (notification_type IN ('READY_FOR_PICKUP', 'OVERDUE_REMINDER', 'COLLECTED_CONFIRMATION')),
    channel           VARCHAR(30) NOT NULL CHECK (channel IN ('SMS', 'EMAIL', 'SMS_SIMULATED', 'EMAIL_SIMULATED')),
    message_body      TEXT NOT NULL,
    sent_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    delivery_status   VARCHAR(20) NOT NULL DEFAULT 'SENT'
);

-- ----------------------------------------------------------------------------
-- DATABASE TRIGGER: Automatic Status Audit Logging
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_trg_parcel_status_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO PARCEL_AUDIT (parcel_id, old_status, new_status, changed_at, changed_by)
        VALUES (NEW.parcel_id, OLD.status, NEW.status, CURRENT_TIMESTAMP, 'Reception Desk');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_parcel_status_audit ON PARCEL;
CREATE TRIGGER trg_parcel_status_audit
AFTER UPDATE OF status ON PARCEL
FOR EACH ROW
EXECUTE FUNCTION fn_trg_parcel_status_audit();

-- ----------------------------------------------------------------------------
-- SEED DATA
-- ----------------------------------------------------------------------------

-- Seed Students
INSERT INTO STUDENT (student_id, reg_no, full_name, email, phone_no, hostel_block, room_no) VALUES
(101, '24BCE1024', 'Arya Zachariah', 'arya.zachariah2024@vitstudent.ac.in', '+919447123456', 'Block E', 'E-204'),
(102, '24BCE1082', 'Viraj Akili', 'viraj.akili2024@vitstudent.ac.in', '+919845123456', 'Block D', 'D-312'),
(103, '24BCE1210', 'Niya Rachel Juban', 'niya.racheljuban2024@vitstudent.ac.in', '+919746123456', 'Block C', 'C-108'),
(104, '24BCE1099', 'Swayam Shukla', 'shuklaswayam2006@gmail.com', '+919054556455', 'Block A', 'A-101');

SELECT setval('student_student_id_seq', (SELECT MAX(student_id) FROM STUDENT));

-- Seed Staff
INSERT INTO STAFF (staff_id, staff_code, full_name, email, phone_no, staff_role, is_active) VALUES
(201, 'STF-01', 'Ramesh Kumar', 'ramesh.k@vit.ac.in', '+919811122334', 'Receptionist', 'Y'),
(202, 'STF-02', 'Sunita Rao', 'sunita.r@vit.ac.in', '+919822233445', 'Receptionist', 'Y'),
(203, 'WRD-01', 'Dr. S. K. Mukherjee', 'sk.mukherjee@vit.ac.in', '+919833344556', 'Warden', 'Y');

SELECT setval('staff_staff_id_seq', (SELECT MAX(staff_id) FROM STAFF));

-- Seed Couriers
INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type) VALUES
(301, 'Amazon Delivery', '+9118003000900', 'Same-Day Express'),
(302, 'Blue Dart Express', '+9118602331234', 'Air Priority'),
(303, 'DTDC Courier', '+918025365511', 'Surface Standard'),
(304, 'India Post Speed Post', '+9118002666868', 'National Postal'),
(305, 'Delhivery Logistics', '+918069857000', 'E-commerce Courier');

SELECT setval('courier_courier_id_seq', (SELECT MAX(courier_id) FROM COURIER));

-- Seed Parcels
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks) VALUES
(1001, 'TRK-AMZ-88214', 101, 301, 201, CURRENT_TIMESTAMP - INTERVAL '2 hours', 'Shelf E-04', '839201', 'PENDING', 'Electronics & Study Material'),
(1002, 'TRK-BLU-67431', 102, 302, 201, CURRENT_TIMESTAMP - INTERVAL '18 hours', 'Shelf D-02', '512940', 'PENDING', 'Laptop Accessories Kit'),
(1003, 'TRK-DTD-55102', 103, 303, 202, CURRENT_TIMESTAMP - INTERVAL '52 hours', 'Shelf C-01', '773192', 'PENDING', 'Important Document Consignment'),
(1004, 'TRK-DEL-43920', 103, 305, 201, CURRENT_TIMESTAMP - INTERVAL '4 hours', 'Shelf C-03', '440183', 'PENDING', 'Apparel Delivery'),
(1005, 'TRK-IND-90214', 104, 304, 201, CURRENT_TIMESTAMP - INTERVAL '26 hours', 'Shelf A-01', '918234', 'COLLECTED', 'Academic Certificate'),
(1006, 'TRK-AMZ-31980', 104, 301, 201, CURRENT_TIMESTAMP - INTERVAL '2 hours', 'Shelf A-02', '332195', 'PENDING', 'Embedded Systems Dev Kit');

SELECT setval('parcel_parcel_id_seq', (SELECT MAX(parcel_id) FROM PARCEL));

-- Seed Pickup Record for 1005
INSERT INTO PICKUP_RECORD (pickup_id, parcel_id, verified_by, collector_reg_no, collected_at, verification_mode, remarks) VALUES
(5001, 1005, 201, '24BCE1099', CURRENT_TIMESTAMP - INTERVAL '2 hours', 'CODE_VERIFIED', 'Collected with verified PIN and Student ID');

SELECT setval('pickup_record_pickup_id_seq', (SELECT MAX(pickup_id) FROM PICKUP_RECORD));

-- Seed Audit for 1005
INSERT INTO PARCEL_AUDIT (audit_id, parcel_id, old_status, new_status, changed_at, changed_by) VALUES
(7001, 1005, 'PENDING', 'COLLECTED', CURRENT_TIMESTAMP - INTERVAL '2 hours', 'Reception Desk');

SELECT setval('parcel_audit_audit_id_seq', (SELECT MAX(audit_id) FROM PARCEL_AUDIT));

-- Seed Notification Log
INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status) VALUES
(9001, 1001, 101, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Arya Zachariah, your parcel TRK-AMZ-88214 is ready at Reception (Shelf E-04). Pickup PIN: 839201.', CURRENT_TIMESTAMP - INTERVAL '2 hours', 'DELIVERED'),
(9002, 1002, 102, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Viraj Akili, your parcel TRK-BLU-67431 is ready at Reception (Shelf D-02). Pickup PIN: 512940.', CURRENT_TIMESTAMP - INTERVAL '18 hours', 'DELIVERED'),
(9003, 1003, 103, 'OVERDUE_REMINDER', 'EMAIL', 'REMINDER: Parcel TRK-DTD-55102 has been at Reception for 52 hours. Please collect promptly from Shelf C-01.', CURRENT_TIMESTAMP - INTERVAL '4 hours', 'DELIVERED'),
(9004, 1004, 103, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Niya Rachel Juban, your parcel TRK-DEL-43920 is ready at Reception (Shelf C-03). Pickup PIN: 440183.', CURRENT_TIMESTAMP - INTERVAL '4 hours', 'DELIVERED'),
(9005, 1005, 104, 'COLLECTED_CONFIRMATION', 'EMAIL', 'Receipt: Parcel TRK-IND-90214 was collected successfully on time.', CURRENT_TIMESTAMP - INTERVAL '2 hours', 'DELIVERED'),
(9006, 1006, 104, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Swayam Shukla, your parcel TRK-AMZ-31980 is ready at Reception (Shelf A-02). Pickup PIN: 332195.', CURRENT_TIMESTAMP - INTERVAL '2 hours', 'DELIVERED');

SELECT setval('notification_log_notification_id_seq', (SELECT MAX(notification_id) FROM NOTIFICATION_LOG));
