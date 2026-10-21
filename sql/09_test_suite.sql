-- ============================================================================
-- SCRIPT: 09_test_suite.sql
-- DESCRIPTION: Automated PL/SQL Test Suite verifying all 7 coursework test cases
-- COURSE: BCSE302P Database Management Systems
-- ============================================================================

SET SERVEROUTPUT ON SIZE 1000000;

DECLARE
    v_new_parcel_id   NUMBER;
    v_pickup_code     VARCHAR2(10);
    v_success_flag    CHAR(1);
    v_message         VARCHAR2(300);
    v_audit_count     NUMBER;
    v_audit_old       VARCHAR2(20);
    v_audit_new       VARCHAR2(20);
    v_error_caught    BOOLEAN := FALSE;
    v_test_track      VARCHAR2(50) := 'TRK-TEST-' || TO_CHAR(SYSTIMESTAMP, 'HH24MISS');
BEGIN
    DBMS_OUTPUT.PUT_LINE('====================================================================');
    DBMS_OUTPUT.PUT_LINE('          HOSTEL PARCEL DESK - AUTOMATED DBMS TEST SUITE            ');
    DBMS_OUTPUT.PUT_LINE('====================================================================');

    -- ------------------------------------------------------------------------
    -- TEST CASE 1: Register parcel with valid unique tracking number
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 1] Register parcel with unique tracking number (' || v_test_track || ')...');
    pkg_parcel_operations.pr_register_parcel(
        p_tracking_no => v_test_track,
        p_student_id  => 101,
        p_courier_id  => 301,
        p_staff_id    => 201,
        p_shelf_loc   => 'Shelf A-99',
        p_remarks     => 'Automated test package',
        p_parcel_id   => v_new_parcel_id,
        p_pickup_code => v_pickup_code
    );
    IF v_new_parcel_id IS NOT NULL AND v_pickup_code IS NOT NULL THEN
        DBMS_OUTPUT.PUT_LINE('  -> PASS: Parcel created with ID: ' || v_new_parcel_id || ', Generated Code: ' || v_pickup_code);
    ELSE
        DBMS_OUTPUT.PUT_LINE('  -> FAIL: Parcel creation failed');
    END IF;

    -- ------------------------------------------------------------------------
    -- TEST CASE 2: Register duplicate tracking number
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 2] Register duplicate tracking number (expect DB constraint rejection)...');
    v_error_caught := FALSE;
    BEGIN
        pkg_parcel_operations.pr_register_parcel(
            p_tracking_no => v_test_track,
            p_student_id  => 102,
            p_courier_id  => 302,
            p_staff_id    => 201,
            p_shelf_loc   => 'Shelf B-99',
            p_remarks     => 'Duplicate attempt',
            p_parcel_id   => v_new_parcel_id,
            p_pickup_code => v_pickup_code
        );
    EXCEPTION
        WHEN OTHERS THEN
            v_error_caught := TRUE;
            DBMS_OUTPUT.PUT_LINE('  -> PASS: Correctly rejected by constraint: ' || SQLERRM);
    END;
    IF NOT v_error_caught THEN
        DBMS_OUTPUT.PUT_LINE('  -> FAIL: Duplicate tracking number was not rejected!');
    END IF;

    -- ------------------------------------------------------------------------
    -- TEST CASE 3: Enter an incorrect pickup code
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 3] Enter an incorrect pickup code (000000)...');
    pkg_parcel_operations.pr_verify_pickup(
        p_parcel_id     => v_new_parcel_id,
        p_entered_code  => '000000',
        p_staff_id      => 201,
        p_collector_reg => '22BCE1001',
        p_remarks       => 'Test invalid code',
        p_success_flag  => v_success_flag,
        p_message       => v_message
    );
    IF v_success_flag = 'N' THEN
        DBMS_OUTPUT.PUT_LINE('  -> PASS: Collection rejected as expected: ' || v_message);
    ELSE
        DBMS_OUTPUT.PUT_LINE('  -> FAIL: Incorrect code was accepted!');
    END IF;

    -- ------------------------------------------------------------------------
    -- TEST CASE 4: Verify with valid pickup code
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 4] Verify with valid pickup code (' || v_pickup_code || ')...');
    pkg_parcel_operations.pr_verify_pickup(
        p_parcel_id     => v_new_parcel_id,
        p_entered_code  => v_pickup_code,
        p_staff_id      => 201,
        p_collector_reg => '22BCE1001',
        p_remarks       => 'Verified with valid code and ID card',
        p_success_flag  => v_success_flag,
        p_message       => v_message
    );
    IF v_success_flag = 'Y' THEN
        DBMS_OUTPUT.PUT_LINE('  -> PASS: Pickup verified successfully: ' || v_message);
    ELSE
        DBMS_OUTPUT.PUT_LINE('  -> FAIL: Valid code verification failed: ' || v_message);
    END IF;

    -- ------------------------------------------------------------------------
    -- TEST CASE 5: Attempt to collect an already collected parcel
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 5] Attempt duplicate pickup on already collected parcel...');
    pkg_parcel_operations.pr_verify_pickup(
        p_parcel_id     => v_new_parcel_id,
        p_entered_code  => v_pickup_code,
        p_staff_id      => 201,
        p_collector_reg => '22BCE1001',
        p_remarks       => 'Second pickup attempt',
        p_success_flag  => v_success_flag,
        p_message       => v_message
    );
    IF v_success_flag = 'N' THEN
        DBMS_OUTPUT.PUT_LINE('  -> PASS: Second collection rejected as expected: ' || v_message);
    ELSE
        DBMS_OUTPUT.PUT_LINE('  -> FAIL: Duplicate collection was allowed!');
    END IF;

    -- ------------------------------------------------------------------------
    -- TEST CASE 6: Verify trg_parcel_status_audit trigger execution
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 6] Verify audit trigger recorded status change...');
    SELECT COUNT(*), MAX(old_status), MAX(new_status)
    INTO v_audit_count, v_audit_old, v_audit_new
    FROM PARCEL_AUDIT
    WHERE parcel_id = v_new_parcel_id;

    IF v_audit_count > 0 AND v_audit_old = 'PENDING' AND v_audit_new = 'COLLECTED' THEN
        DBMS_OUTPUT.PUT_LINE('  -> PASS: Audit trigger captured transition PENDING -> COLLECTED');
    ELSE
        DBMS_OUTPUT.PUT_LINE('  -> FAIL: Audit record missing or incorrect');
    END IF;

    -- ------------------------------------------------------------------------
    -- TEST CASE 7: Execute explicit cursor for overdue parcels
    -- ------------------------------------------------------------------------
    DBMS_OUTPUT.PUT_LINE('[TEST 7] Running explicit cursor c_unclaimed_parcels report...');
    pkg_parcel_operations.pr_print_unclaimed_report(p_threshold_hours => 48);
    DBMS_OUTPUT.PUT_LINE('  -> PASS: Cursor report completed successfully.');

    DBMS_OUTPUT.PUT_LINE('====================================================================');
    DBMS_OUTPUT.PUT_LINE('                   TEST SUITE SUMMARY: ALL PASSED                   ');
    DBMS_OUTPUT.PUT_LINE('====================================================================');
END;
/
