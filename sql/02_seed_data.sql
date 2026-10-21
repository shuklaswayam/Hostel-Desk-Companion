-- ============================================================================
-- SCRIPT: 02_seed_data.sql
-- DESCRIPTION: Realistic sample data for students, staff, couriers, parcels,
--              pickup records, audit logs, and simulated notifications.
-- ============================================================================

-- Clear existing data (if re-running seed script)
DELETE FROM PICKUP_RECORD;
DELETE FROM PARCEL_AUDIT;
DELETE FROM NOTIFICATION_LOG;
DELETE FROM PARCEL;
DELETE FROM STUDENT;
DELETE FROM STAFF;
DELETE FROM COURIER;

-- ----------------------------------------------------------------------------
-- SEED STUDENTS
-- ----------------------------------------------------------------------------
INSERT INTO STUDENT (student_id, reg_no, full_name, email, phone_no, hostel_block, room_no)
VALUES (101, '24BCE1024', 'Arya Zachariah', 'arya.zachariah2024@vitstudent.ac.in', '+919447123456', 'Block E', 'E-204');

INSERT INTO STUDENT (student_id, reg_no, full_name, email, phone_no, hostel_block, room_no)
VALUES (102, '24BCE1082', 'Viraj Akili', 'viraj.akili2024@vitstudent.ac.in', '+919845123456', 'Block D', 'D-312');

INSERT INTO STUDENT (student_id, reg_no, full_name, email, phone_no, hostel_block, room_no)
VALUES (103, '24BCE1210', 'Niya Rachel Juban', 'niya.racheljuban2024@vitstudent.ac.in', '+919746123456', 'Block C', 'C-108');

INSERT INTO STUDENT (student_id, reg_no, full_name, email, phone_no, hostel_block, room_no)
VALUES (104, '24BCE1099', 'Swayam Shukla', 'shuklaswayam2006@gmail.com', '+919054556455', 'Block A', 'A-101');

-- ----------------------------------------------------------------------------
-- SEED RECEPTION STAFF & WARDENS
-- ----------------------------------------------------------------------------
INSERT INTO STAFF (staff_id, staff_code, full_name, email, phone_no, staff_role, is_active)
VALUES (201, 'STF-01', 'Ramesh Kumar', 'ramesh.k@vit.ac.in', '+919811122334', 'Receptionist', 'Y');

INSERT INTO STAFF (staff_id, staff_code, full_name, email, phone_no, staff_role, is_active)
VALUES (202, 'STF-02', 'Sunita Rao', 'sunita.r@vit.ac.in', '+919822233445', 'Receptionist', 'Y');

INSERT INTO STAFF (staff_id, staff_code, full_name, email, phone_no, staff_role, is_active)
VALUES (203, 'WRD-01', 'Dr. S. K. Mukherjee', 'sk.mukherjee@vit.ac.in', '+919833344556', 'Warden', 'Y');

-- ----------------------------------------------------------------------------
-- SEED COURIER COMPANIES
-- ----------------------------------------------------------------------------
INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type)
VALUES (301, 'Amazon Delivery', '+9118003000900', 'Same-Day Express');

INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type)
VALUES (302, 'Blue Dart Express', '+9118602331234', 'Air Priority');

INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type)
VALUES (303, 'DTDC Courier', '+918025365511', 'Surface Standard');

INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type)
VALUES (304, 'India Post Speed Post', '+9118002666868', 'National Postal');

INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type)
VALUES (305, 'Delhivery Logistics', '+918069857000', 'E-commerce Courier');

-- ----------------------------------------------------------------------------
-- SEED PARCELS (with varied arrival timestamps for testing waiting hours & overdue)
-- ----------------------------------------------------------------------------
-- Parcel 1: Arrived 2 hours ago (Fresh, Pending)
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
VALUES (1001, 'TRK-AMZ-88214', 101, 301, 201, SYSTIMESTAMP - INTERVAL '2' HOUR, 'Shelf E-04', '839201', 'PENDING', 'Electronics & Study Material');

-- Parcel 2: Arrived 18 hours ago (Pending)
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
VALUES (1002, 'TRK-BLU-67431', 102, 302, 201, SYSTIMESTAMP - INTERVAL '18' HOUR, 'Shelf D-02', '512940', 'PENDING', 'Laptop Accessories Kit');

-- Parcel 3: Arrived 52 hours ago (OVERDUE > 48h, Pending pickup)
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
VALUES (1003, 'TRK-DTD-55102', 103, 303, 202, SYSTIMESTAMP - INTERVAL '52' HOUR, 'Shelf C-01', '773192', 'PENDING', 'Important Document Consignment');

-- Parcel 4: Arrived 4 hours ago (Fresh, Pending)
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
VALUES (1004, 'TRK-DEL-43920', 103, 305, 201, SYSTIMESTAMP - INTERVAL '4' HOUR, 'Shelf C-03', '440183', 'PENDING', 'Apparel Delivery');

-- Parcel 5: Arrived 26 hours ago and already collected
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
VALUES (1005, 'TRK-IND-90214', 104, 304, 201, SYSTIMESTAMP - INTERVAL '26' HOUR, 'Shelf A-01', '918234', 'COLLECTED', 'Academic Certificate');

-- Parcel 6: Arrived 2 hours ago (Fresh, Pending)
INSERT INTO PARCEL (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
VALUES (1006, 'TRK-AMZ-31980', 104, 301, 201, SYSTIMESTAMP - INTERVAL '2' HOUR, 'Shelf A-02', '332195', 'PENDING', 'Embedded Systems Dev Kit');

-- ----------------------------------------------------------------------------
-- SEED PICKUP RECORD (For parcel 1005)
-- ----------------------------------------------------------------------------
INSERT INTO PICKUP_RECORD (pickup_id, parcel_id, verified_by, collector_reg_no, collected_at, verification_mode, remarks)
VALUES (5001, 1005, 201, '24BCE1099', SYSTIMESTAMP - INTERVAL '2' HOUR, 'CODE_VERIFIED', 'Collected with verified PIN and Student ID');

-- ----------------------------------------------------------------------------
-- SEED AUDIT LOG (Record initial transitions)
-- ----------------------------------------------------------------------------
INSERT INTO PARCEL_AUDIT (audit_id, parcel_id, old_status, new_status, changed_at, changed_by)
VALUES (7001, 1005, 'PENDING', 'COLLECTED', SYSTIMESTAMP - INTERVAL '2' HOUR, 'Reception Desk');

-- ----------------------------------------------------------------------------
-- SEED NOTIFICATION LOG
-- ----------------------------------------------------------------------------
INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
VALUES (9001, 1001, 101, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Arya Zachariah, your parcel TRK-AMZ-88214 is ready at Reception (Shelf E-04). Pickup PIN: 839201.', SYSTIMESTAMP - INTERVAL '2' HOUR, 'DELIVERED');

INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
VALUES (9002, 1002, 102, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Viraj Akili, your parcel TRK-BLU-67431 is ready at Reception (Shelf D-02). Pickup PIN: 512940.', SYSTIMESTAMP - INTERVAL '18' HOUR, 'DELIVERED');

INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
VALUES (9003, 1003, 103, 'OVERDUE_REMINDER', 'EMAIL', 'REMINDER: Parcel TRK-DTD-55102 has been at Reception for 52 hours. Please collect promptly from Shelf C-01.', SYSTIMESTAMP - INTERVAL '4' HOUR, 'DELIVERED');

INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
VALUES (9004, 1004, 103, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Niya Rachel Juban, your parcel TRK-DEL-43920 is ready at Reception (Shelf C-03). Pickup PIN: 440183.', SYSTIMESTAMP - INTERVAL '4' HOUR, 'DELIVERED');

INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
VALUES (9005, 1005, 104, 'COLLECTED_CONFIRMATION', 'EMAIL', 'Receipt: Parcel TRK-IND-90214 was collected successfully on time.', SYSTIMESTAMP - INTERVAL '2' HOUR, 'DELIVERED');

INSERT INTO NOTIFICATION_LOG (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
VALUES (9006, 1006, 104, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Swayam Shukla, your parcel TRK-AMZ-31980 is ready at Reception (Shelf A-02). Pickup PIN: 332195.', SYSTIMESTAMP - INTERVAL '2' HOUR, 'DELIVERED');

COMMIT;
