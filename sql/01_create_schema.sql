-- ============================================================================
-- PROJECT: Hostel Parcel Desk - Smart Parcel Reception & Pickup Verification
-- COURSE: BCSE302P Database Management Systems
-- SCRIPT: 01_create_schema.sql
-- DESCRIPTION: DDL for 7 normalized tables (3NF) with constraints, keys, sequences
-- ============================================================================

-- Drop existing tables and sequences if they exist (in reverse dependency order)
BEGIN
    FOR t IN (SELECT table_name FROM user_tables WHERE table_name IN 
              ('PICKUP_RECORD', 'PARCEL_AUDIT', 'NOTIFICATION_LOG', 'PARCEL', 'STUDENT', 'STAFF', 'COURIER')) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS';
    END LOOP;
END;
/

BEGIN
    FOR s IN (SELECT sequence_name FROM user_sequences WHERE sequence_name IN 
              ('SEQ_STUDENT', 'SEQ_STAFF', 'SEQ_COURIER', 'SEQ_PARCEL', 'SEQ_PICKUP', 'SEQ_AUDIT', 'SEQ_NOTIF')) LOOP
        EXECUTE IMMEDIATE 'DROP SEQUENCE ' || s.sequence_name;
    END LOOP;
END;
/

-- Sequences for Primary Keys
CREATE SEQUENCE SEQ_STUDENT START WITH 101 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_STAFF   START WITH 201 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_COURIER START WITH 301 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_PARCEL  START WITH 1001 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_PICKUP  START WITH 5001 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_AUDIT   START WITH 7001 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE SEQ_NOTIF   START WITH 9001 INCREMENT BY 1 NOCACHE;

-- ----------------------------------------------------------------------------
-- TABLE 1: STUDENT
-- Normalization: 3NF (all student details depend on student_id / reg_no alone)
-- ----------------------------------------------------------------------------
CREATE TABLE STUDENT (
    student_id      NUMBER(10)          DEFAULT SEQ_STUDENT.NEXTVAL PRIMARY KEY,
    reg_no          VARCHAR2(20)        NOT NULL UNIQUE,
    full_name       VARCHAR2(100)       NOT NULL,
    email           VARCHAR2(100)       NOT NULL UNIQUE,
    phone_no        VARCHAR2(15)        NOT NULL,
    hostel_block    VARCHAR2(20)        NOT NULL,
    room_no         VARCHAR2(10)        NOT NULL,
    created_at      TIMESTAMP           DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT chk_stud_block CHECK (hostel_block IN ('Block A', 'Block B', 'Block C', 'Block D', 'Block E'))
);

-- ----------------------------------------------------------------------------
-- TABLE 2: STAFF
-- Details of hostel reception staff & wardens authorized to log and verify parcels
-- ----------------------------------------------------------------------------
CREATE TABLE STAFF (
    staff_id        NUMBER(10)          DEFAULT SEQ_STAFF.NEXTVAL PRIMARY KEY,
    staff_code      VARCHAR2(20)        NOT NULL UNIQUE,
    full_name       VARCHAR2(100)       NOT NULL,
    email           VARCHAR2(100)       NOT NULL UNIQUE,
    phone_no        VARCHAR2(15)        NOT NULL,
    staff_role      VARCHAR2(30)        DEFAULT 'Receptionist' NOT NULL,
    is_active       CHAR(1)             DEFAULT 'Y' NOT NULL,
    CONSTRAINT chk_staff_role CHECK (staff_role IN ('Receptionist', 'Warden', 'Supervisor')),
    CONSTRAINT chk_staff_active CHECK (is_active IN ('Y', 'N'))
);

-- ----------------------------------------------------------------------------
-- TABLE 3: COURIER
-- Courier companies delivering to campus
-- ----------------------------------------------------------------------------
CREATE TABLE COURIER (
    courier_id      NUMBER(10)          DEFAULT SEQ_COURIER.NEXTVAL PRIMARY KEY,
    company_name    VARCHAR2(50)        NOT NULL UNIQUE,
    contact_phone   VARCHAR2(20),
    service_type    VARCHAR2(30)        DEFAULT 'Standard' NOT NULL,
    created_at      TIMESTAMP           DEFAULT SYSTIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- TABLE 4: PARCEL
-- Core table storing incoming packages, shelf location, and pickup verification code
-- ----------------------------------------------------------------------------
CREATE TABLE PARCEL (
    parcel_id       NUMBER(10)          DEFAULT SEQ_PARCEL.NEXTVAL PRIMARY KEY,
    tracking_number VARCHAR2(50)        NOT NULL UNIQUE,
    student_id      NUMBER(10)          NOT NULL,
    courier_id      NUMBER(10)          NOT NULL,
    registered_by   NUMBER(10)          NOT NULL,
    arrival_time    TIMESTAMP           DEFAULT SYSTIMESTAMP NOT NULL,
    shelf_location  VARCHAR2(20)        NOT NULL,
    pickup_code     VARCHAR2(10)        NOT NULL,
    status          VARCHAR2(20)        DEFAULT 'PENDING' NOT NULL,
    remarks         VARCHAR2(200),
    CONSTRAINT fk_parcel_student FOREIGN KEY (student_id) REFERENCES STUDENT(student_id),
    CONSTRAINT fk_parcel_courier FOREIGN KEY (courier_id) REFERENCES COURIER(courier_id),
    CONSTRAINT fk_parcel_staff   FOREIGN KEY (registered_by) REFERENCES STAFF(staff_id),
    CONSTRAINT chk_parcel_status CHECK (status IN ('PENDING', 'COLLECTED', 'OVERDUE', 'RETURNED'))
);

-- ----------------------------------------------------------------------------
-- TABLE 5: PICKUP_RECORD
-- Enforces 1:0..1 relationship. Each parcel has at most one successful pickup record.
-- ----------------------------------------------------------------------------
CREATE TABLE PICKUP_RECORD (
    pickup_id       NUMBER(10)          DEFAULT SEQ_PICKUP.NEXTVAL PRIMARY KEY,
    parcel_id       NUMBER(10)          NOT NULL UNIQUE,
    verified_by     NUMBER(10)          NOT NULL,
    collector_reg_no VARCHAR2(20)       NOT NULL,
    collected_at    TIMESTAMP           DEFAULT SYSTIMESTAMP NOT NULL,
    verification_mode VARCHAR2(20)      DEFAULT 'CODE_VERIFIED' NOT NULL,
    remarks         VARCHAR2(200),
    CONSTRAINT fk_pickup_parcel FOREIGN KEY (parcel_id) REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
    CONSTRAINT fk_pickup_staff  FOREIGN KEY (verified_by) REFERENCES STAFF(staff_id)
);

-- ----------------------------------------------------------------------------
-- TABLE 6: PARCEL_AUDIT
-- Automated audit trail populated by trigger on status change
-- ----------------------------------------------------------------------------
CREATE TABLE PARCEL_AUDIT (
    audit_id        NUMBER(10)          DEFAULT SEQ_AUDIT.NEXTVAL PRIMARY KEY,
    parcel_id       NUMBER(10)          NOT NULL,
    old_status      VARCHAR2(20)        NOT NULL,
    new_status      VARCHAR2(20)        NOT NULL,
    changed_at      TIMESTAMP           DEFAULT SYSTIMESTAMP NOT NULL,
    changed_by      VARCHAR2(50)        DEFAULT USER NOT NULL,
    CONSTRAINT fk_audit_parcel FOREIGN KEY (parcel_id) REFERENCES PARCEL(parcel_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- TABLE 7: NOTIFICATION_LOG
-- Records simulated notifications (ready for pickup, overdue reminders, collected confirmations)
-- ----------------------------------------------------------------------------
CREATE TABLE NOTIFICATION_LOG (
    notification_id   NUMBER(10)        DEFAULT SEQ_NOTIF.NEXTVAL PRIMARY KEY,
    parcel_id         NUMBER(10)        NOT NULL,
    student_id        NUMBER(10)        NOT NULL,
    notification_type VARCHAR2(30)      NOT NULL,
    channel           VARCHAR2(20)      DEFAULT 'SMS_SIMULATED' NOT NULL,
    message_body      VARCHAR2(400)     NOT NULL,
    sent_at           TIMESTAMP         DEFAULT SYSTIMESTAMP NOT NULL,
    delivery_status   VARCHAR2(20)      DEFAULT 'SENT' NOT NULL,
    CONSTRAINT fk_notif_parcel  FOREIGN KEY (parcel_id) REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
    CONSTRAINT fk_notif_student FOREIGN KEY (student_id) REFERENCES STUDENT(student_id),
    CONSTRAINT chk_notif_type   CHECK (notification_type IN ('READY_FOR_PICKUP', 'OVERDUE_REMINDER', 'COLLECTED_CONFIRMATION')),
    CONSTRAINT chk_notif_chan   CHECK (channel IN ('SMS_SIMULATED', 'EMAIL_SIMULATED'))
);

-- Useful Indexing for Frequent Searches
CREATE INDEX idx_parcel_student ON PARCEL(student_id);
CREATE INDEX idx_parcel_status  ON PARCEL(status);
CREATE INDEX idx_parcel_shelf   ON PARCEL(shelf_location);
CREATE INDEX idx_notif_student  ON NOTIFICATION_LOG(student_id);

COMMENT ON TABLE STUDENT IS 'Stores verified resident students in hostel blocks';
COMMENT ON TABLE STAFF IS 'Hostel reception desk officers and wardens';
COMMENT ON TABLE COURIER IS 'Delivery services delivering packages to hostel reception';
COMMENT ON TABLE PARCEL IS 'Incoming packages registered at reception with unique pickup PIN';
COMMENT ON TABLE PICKUP_RECORD IS 'Official pickup verification log preventing duplicate collections';
COMMENT ON TABLE PARCEL_AUDIT IS 'Audit log of all parcel status transitions maintained by trigger';
COMMENT ON TABLE NOTIFICATION_LOG IS 'Simulated notification log for students';
