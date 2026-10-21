-- ============================================================================
-- SCRIPT: 05_procedures.sql
-- DESCRIPTION: Standalone Stored Procedures for parcel registration & verification
-- OBJECTS: pr_register_parcel, pr_verify_pickup
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PROCEDURE 1: pr_register_parcel
-- Registers incoming parcel, generates 6-digit pickup code, logs notification
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE pr_register_parcel (
    p_tracking_no   IN  VARCHAR2,
    p_student_id    IN  NUMBER,
    p_courier_id    IN  NUMBER,
    p_staff_id      IN  NUMBER,
    p_shelf_loc     IN  VARCHAR2,
    p_remarks       IN  VARCHAR2,
    p_parcel_id     OUT NUMBER,
    p_pickup_code   OUT VARCHAR2
) IS
    v_stud_count    NUMBER;
    v_courier_count NUMBER;
    v_staff_count   NUMBER;
    v_stud_name     VARCHAR2(100);
    v_raw_code      NUMBER;
BEGIN
    -- 1. Validate Student existence
    SELECT COUNT(*), MAX(full_name)
    INTO v_stud_count, v_stud_name
    FROM STUDENT
    WHERE student_id = p_student_id;

    IF v_stud_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20010, 'Student ID ' || p_student_id || ' does not exist.');
    END IF;

    -- 2. Validate Courier existence
    SELECT COUNT(*) INTO v_courier_count FROM COURIER WHERE courier_id = p_courier_id;
    IF v_courier_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20011, 'Courier ID ' || p_courier_id || ' does not exist.');
    END IF;

    -- 3. Validate Staff existence and active status
    SELECT COUNT(*) INTO v_staff_count FROM STAFF WHERE staff_id = p_staff_id AND is_active = 'Y';
    IF v_staff_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20012, 'Staff ID ' || p_staff_id || ' is invalid or inactive.');
    END IF;

    -- 4. Generate random 6-digit pickup PIN (100000 to 999999)
    v_raw_code := TRUNC(DBMS_RANDOM.VALUE(100000, 999999));
    p_pickup_code := TO_CHAR(v_raw_code);

    -- 5. Allocate new parcel ID
    p_parcel_id := SEQ_PARCEL.NEXTVAL;

    -- 6. Insert new Parcel record
    INSERT INTO PARCEL (
        parcel_id,
        tracking_number,
        student_id,
        courier_id,
        registered_by,
        arrival_time,
        shelf_location,
        pickup_code,
        status,
        remarks
    ) VALUES (
        p_parcel_id,
        p_tracking_no,
        p_student_id,
        p_courier_id,
        p_staff_id,
        SYSTIMESTAMP,
        p_shelf_loc,
        p_pickup_code,
        'PENDING',
        p_remarks
    );

    -- 7. Log simulated notification
    INSERT INTO NOTIFICATION_LOG (
        notification_id,
        parcel_id,
        student_id,
        notification_type,
        channel,
        message_body,
        sent_at,
        delivery_status
    ) VALUES (
        SEQ_NOTIF.NEXTVAL,
        p_parcel_id,
        p_student_id,
        'READY_FOR_PICKUP',
        'SMS_SIMULATED',
        'Dear ' || v_stud_name || ', your parcel ' || p_tracking_no || 
        ' is ready for collection at ' || p_shelf_loc || '. Pickup Code: ' || p_pickup_code,
        SYSTIMESTAMP,
        'SENT'
    );

    COMMIT;

EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
        ROLLBACK;
        RAISE_APPLICATION_ERROR(-20013, 'Tracking number ' || p_tracking_no || ' already registered in the system.');
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END pr_register_parcel;
/


-- ----------------------------------------------------------------------------
-- PROCEDURE 2: pr_verify_pickup
-- Validates pickup code, prevents double-collection, records pickup and audit
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE pr_verify_pickup (
    p_parcel_id      IN  NUMBER,
    p_entered_code   IN  VARCHAR2,
    p_staff_id       IN  NUMBER,
    p_collector_reg  IN  VARCHAR2,
    p_remarks        IN  VARCHAR2,
    p_success_flag   OUT CHAR,
    p_message        OUT VARCHAR2
) IS
    v_actual_code    VARCHAR2(10);
    v_current_status VARCHAR2(20);
    v_student_id     NUMBER;
    v_student_reg    VARCHAR2(20);
    v_student_name   VARCHAR2(100);
    v_tracking_no    VARCHAR2(50);
BEGIN
    -- 1. Lock and fetch parcel record
    BEGIN
        SELECT p.pickup_code, p.status, p.student_id, s.reg_no, s.full_name, p.tracking_number
        INTO v_actual_code, v_current_status, v_student_id, v_student_reg, v_student_name, v_tracking_no
        FROM PARCEL p
        JOIN STUDENT s ON p.student_id = s.student_id
        WHERE p.parcel_id = p_parcel_id
        FOR UPDATE OF p.status;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_success_flag := 'N';
            p_message := 'Parcel ID ' || p_parcel_id || ' not found.';
            RETURN;
    END;

    -- 2. Verify eligibility (must not already be collected)
    IF v_current_status = 'COLLECTED' THEN
        p_success_flag := 'N';
        p_message := 'Rejection: Parcel ' || v_tracking_no || ' has already been collected.';
        ROLLBACK;
        RETURN;
    ELSIF v_current_status = 'RETURNED' THEN
        p_success_flag := 'N';
        p_message := 'Rejection: Parcel has been marked RETURNED to sender.';
        ROLLBACK;
        RETURN;
    END IF;

    -- 3. Verify pickup code match
    IF TRIM(p_entered_code) != TRIM(v_actual_code) THEN
        p_success_flag := 'N';
        p_message := 'Invalid pickup code provided. Collection verification failed.';
        ROLLBACK;
        RETURN;
    END IF;

    -- 4. Code verified: Update parcel status to COLLECTED
    UPDATE PARCEL
    SET status = 'COLLECTED'
    WHERE parcel_id = p_parcel_id;

    -- 5. Insert pickup verification record
    INSERT INTO PICKUP_RECORD (
        pickup_id,
        parcel_id,
        verified_by,
        collector_reg_no,
        collected_at,
        verification_mode,
        remarks
    ) VALUES (
        SEQ_PICKUP.NEXTVAL,
        p_parcel_id,
        p_staff_id,
        COALESCE(p_collector_reg, v_student_reg),
        SYSTIMESTAMP,
        'CODE_VERIFIED',
        p_remarks
    );

    -- 6. Log confirmation in notification log
    INSERT INTO NOTIFICATION_LOG (
        notification_id,
        parcel_id,
        student_id,
        notification_type,
        channel,
        message_body,
        sent_at,
        delivery_status
    ) VALUES (
        SEQ_NOTIF.NEXTVAL,
        p_parcel_id,
        v_student_id,
        'COLLECTED_CONFIRMATION',
        'SMS_SIMULATED',
        'Hello ' || v_student_name || ', your parcel ' || v_tracking_no || 
        ' was successfully collected and verified by staff STF-' || p_staff_id || '.',
        SYSTIMESTAMP,
        'SENT'
    );

    COMMIT;
    p_success_flag := 'Y';
    p_message := 'Success: Parcel ' || v_tracking_no || ' verified and handed over to ' || v_student_name || '.';

EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_success_flag := 'N';
        p_message := 'Database error during verification: ' || SQLERRM;
END pr_verify_pickup;
/
