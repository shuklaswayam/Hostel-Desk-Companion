-- ============================================================================
-- SCRIPT: 07_package_body.sql
-- DESCRIPTION: PL/SQL Package Body implementing all operations and business logic
-- OBJECT: pkg_parcel_operations
-- ============================================================================

CREATE OR REPLACE PACKAGE BODY pkg_parcel_operations AS

    -- ------------------------------------------------------------------------
    -- FUNCTION: fn_parcel_waiting_hours
    -- ------------------------------------------------------------------------
    FUNCTION fn_parcel_waiting_hours (
        p_parcel_id IN NUMBER
    ) RETURN NUMBER IS
        v_arrival_time TIMESTAMP;
        v_hours_waiting NUMBER(8, 2);
    BEGIN
        SELECT arrival_time
        INTO v_arrival_time
        FROM PARCEL
        WHERE parcel_id = p_parcel_id;

        SELECT ROUND(
            EXTRACT(DAY FROM (SYSTIMESTAMP - v_arrival_time)) * 24 +
            EXTRACT(HOUR FROM (SYSTIMESTAMP - v_arrival_time)) +
            EXTRACT(MINUTE FROM (SYSTIMESTAMP - v_arrival_time)) / 60 +
            EXTRACT(SECOND FROM (SYSTIMESTAMP - v_arrival_time)) / 3600,
            2
        )
        INTO v_hours_waiting
        FROM DUAL;

        RETURN v_hours_waiting;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN -1;
        WHEN OTHERS THEN
            RETURN -99;
    END fn_parcel_waiting_hours;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: pr_register_parcel
    -- ------------------------------------------------------------------------
    PROCEDURE pr_register_parcel (
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
        -- Validations
        SELECT COUNT(*), MAX(full_name) INTO v_stud_count, v_stud_name FROM STUDENT WHERE student_id = p_student_id;
        IF v_stud_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20010, 'Student ID ' || p_student_id || ' does not exist.');
        END IF;

        SELECT COUNT(*) INTO v_courier_count FROM COURIER WHERE courier_id = p_courier_id;
        IF v_courier_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20011, 'Courier ID ' || p_courier_id || ' does not exist.');
        END IF;

        SELECT COUNT(*) INTO v_staff_count FROM STAFF WHERE staff_id = p_staff_id AND is_active = 'Y';
        IF v_staff_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20012, 'Staff ID ' || p_staff_id || ' is invalid or inactive.');
        END IF;

        -- Generate 6-digit random code
        v_raw_code := TRUNC(DBMS_RANDOM.VALUE(100000, 999999));
        p_pickup_code := TO_CHAR(v_raw_code);
        p_parcel_id := SEQ_PARCEL.NEXTVAL;

        INSERT INTO PARCEL (
            parcel_id, tracking_number, student_id, courier_id, registered_by,
            arrival_time, shelf_location, pickup_code, status, remarks
        ) VALUES (
            p_parcel_id, p_tracking_no, p_student_id, p_courier_id, p_staff_id,
            SYSTIMESTAMP, p_shelf_loc, p_pickup_code, 'PENDING', p_remarks
        );

        INSERT INTO NOTIFICATION_LOG (
            notification_id, parcel_id, student_id, notification_type,
            channel, message_body, sent_at, delivery_status
        ) VALUES (
            SEQ_NOTIF.NEXTVAL, p_parcel_id, p_student_id, 'READY_FOR_PICKUP',
            'SMS_SIMULATED',
            'Dear ' || v_stud_name || ', your parcel ' || p_tracking_no || 
            ' is at reception shelf ' || p_shelf_loc || '. Pickup Code: ' || p_pickup_code,
            SYSTIMESTAMP, 'SENT'
        );

        COMMIT;
    EXCEPTION
        WHEN DUP_VAL_ON_INDEX THEN
            ROLLBACK;
            RAISE_APPLICATION_ERROR(-20013, 'Tracking number ' || p_tracking_no || ' is already registered.');
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END pr_register_parcel;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: pr_verify_pickup
    -- ------------------------------------------------------------------------
    PROCEDURE pr_verify_pickup (
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

        IF v_current_status = 'COLLECTED' THEN
            p_success_flag := 'N';
            p_message := 'Rejection: Parcel ' || v_tracking_no || ' has already been collected.';
            ROLLBACK;
            RETURN;
        ELSIF v_current_status = 'RETURNED' THEN
            p_success_flag := 'N';
            p_message := 'Rejection: Parcel has been marked RETURNED.';
            ROLLBACK;
            RETURN;
        END IF;

        IF TRIM(p_entered_code) != TRIM(v_actual_code) THEN
            p_success_flag := 'N';
            p_message := 'Rejection: Incorrect pickup code entered.';
            ROLLBACK;
            RETURN;
        END IF;

        -- Update status: fires trg_parcel_status_audit
        UPDATE PARCEL
        SET status = 'COLLECTED'
        WHERE parcel_id = p_parcel_id;

        INSERT INTO PICKUP_RECORD (
            pickup_id, parcel_id, verified_by, collector_reg_no,
            collected_at, verification_mode, remarks
        ) VALUES (
            SEQ_PICKUP.NEXTVAL, p_parcel_id, p_staff_id,
            COALESCE(p_collector_reg, v_student_reg),
            SYSTIMESTAMP, 'CODE_VERIFIED', p_remarks
        );

        INSERT INTO NOTIFICATION_LOG (
            notification_id, parcel_id, student_id, notification_type,
            channel, message_body, sent_at, delivery_status
        ) VALUES (
            SEQ_NOTIF.NEXTVAL, p_parcel_id, v_student_id, 'COLLECTED_CONFIRMATION',
            'SMS_SIMULATED',
            'Hello ' || v_student_name || ', your parcel ' || v_tracking_no || 
            ' was successfully collected and verified.',
            SYSTIMESTAMP, 'SENT'
        );

        COMMIT;
        p_success_flag := 'Y';
        p_message := 'Success: Parcel ' || v_tracking_no || ' verified and handed over to ' || v_student_name || '.';
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            p_success_flag := 'N';
            p_message := 'Database error: ' || SQLERRM;
    END pr_verify_pickup;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: pr_print_unclaimed_report (Uses Explicit Cursor)
    -- ------------------------------------------------------------------------
    PROCEDURE pr_print_unclaimed_report (
        p_threshold_hours IN NUMBER DEFAULT 48
    ) IS
        -- Explicit Cursor with parameter
        CURSOR c_unclaimed (cp_hours NUMBER) IS
            SELECT p.parcel_id, p.tracking_number, s.full_name, s.reg_no,
                   s.hostel_block, s.room_no, p.shelf_location, p.arrival_time,
                   ROUND(EXTRACT(DAY FROM (SYSTIMESTAMP - p.arrival_time))*24 +
                         EXTRACT(HOUR FROM (SYSTIMESTAMP - p.arrival_time)), 1) AS waiting_hrs
            FROM PARCEL p
            JOIN STUDENT s ON p.student_id = s.student_id
            WHERE p.status = 'PENDING'
              AND (SYSTIMESTAMP - p.arrival_time) >= NUMTODSINTERVAL(cp_hours, 'HOUR')
            ORDER BY p.arrival_time ASC;

        v_rec c_unclaimed%ROWTYPE;
        v_count NUMBER := 0;
    BEGIN
        DBMS_OUTPUT.PUT_LINE('================================================================================');
        DBMS_OUTPUT.PUT_LINE('             HOSTEL RECEPTION - OVERDUE UNCLAIMED PARCELS REPORT                ');
        DBMS_OUTPUT.PUT_LINE('             Threshold: >= ' || p_threshold_hours || ' Hours                    ');
        DBMS_OUTPUT.PUT_LINE('================================================================================');
        DBMS_OUTPUT.PUT_LINE(RPAD('ID', 6) || RPAD('TRACKING NO', 18) || RPAD('RECIPIENT', 18) || 
                             RPAD('REG NO', 12) || RPAD('BLOCK', 10) || RPAD('SHELF', 12) || 'WAIT (HRS)');
        DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');

        OPEN c_unclaimed(p_threshold_hours);
        LOOP
            FETCH c_unclaimed INTO v_rec;
            EXIT WHEN c_unclaimed%NOTFOUND;
            v_count := v_count + 1;
            DBMS_OUTPUT.PUT_LINE(
                RPAD(TO_CHAR(v_rec.parcel_id), 6) ||
                RPAD(v_rec.tracking_number, 18) ||
                RPAD(SUBSTR(v_rec.full_name, 1, 16), 18) ||
                RPAD(v_rec.reg_no, 12) ||
                RPAD(v_rec.hostel_block, 10) ||
                RPAD(v_rec.shelf_location, 12) ||
                TO_CHAR(v_rec.waiting_hrs, '999.9')
            );
        END LOOP;
        CLOSE c_unclaimed;

        DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');
        DBMS_OUTPUT.PUT_LINE('Total Overdue Packages Found: ' || v_count);
        DBMS_OUTPUT.PUT_LINE('================================================================================');
    END pr_print_unclaimed_report;

    -- ------------------------------------------------------------------------
    -- PROCEDURE: pr_get_metrics
    -- ------------------------------------------------------------------------
    PROCEDURE pr_get_metrics (
        p_total     OUT NUMBER,
        p_pending   OUT NUMBER,
        p_collected OUT NUMBER,
        p_overdue   OUT NUMBER
    ) IS
    BEGIN
        SELECT COUNT(*) INTO p_total FROM PARCEL;
        SELECT COUNT(*) INTO p_pending FROM PARCEL WHERE status = 'PENDING';
        SELECT COUNT(*) INTO p_collected FROM PARCEL WHERE status = 'COLLECTED';
        SELECT COUNT(*) INTO p_overdue FROM PARCEL 
        WHERE status = 'PENDING' AND (SYSTIMESTAMP - arrival_time) >= NUMTODSINTERVAL(48, 'HOUR');
    END pr_get_metrics;

END pkg_parcel_operations;
/
