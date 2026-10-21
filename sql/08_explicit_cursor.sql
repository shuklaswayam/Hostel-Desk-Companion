-- ============================================================================
-- SCRIPT: 08_explicit_cursor.sql
-- DESCRIPTION: Standalone PL/SQL block demonstrating Explicit Cursor lifecycle
-- OBJECT: c_unclaimed_parcels
-- ============================================================================

SET SERVEROUTPUT ON SIZE 1000000;

DECLARE
    -- Definition of explicit cursor with parameter
    CURSOR c_unclaimed_parcels (p_min_hours NUMBER) IS
        SELECT 
            p.parcel_id,
            p.tracking_number,
            s.full_name,
            s.reg_no,
            s.hostel_block,
            s.room_no,
            p.shelf_location,
            p.arrival_time,
            ROUND(
                EXTRACT(DAY FROM (SYSTIMESTAMP - p.arrival_time)) * 24 +
                EXTRACT(HOUR FROM (SYSTIMESTAMP - p.arrival_time)) +
                EXTRACT(MINUTE FROM (SYSTIMESTAMP - p.arrival_time)) / 60,
                1
            ) AS waiting_hours
        FROM PARCEL p
        JOIN STUDENT s ON p.student_id = s.student_id
        WHERE p.status = 'PENDING'
          AND (SYSTIMESTAMP - p.arrival_time) >= NUMTODSINTERVAL(p_min_hours, 'HOUR')
        ORDER BY p.arrival_time ASC;

    -- Record variable matching cursor structure
    v_parcel_rec c_unclaimed_parcels%ROWTYPE;
    v_counter    NUMBER := 0;
    c_threshold  CONSTANT NUMBER := 48; -- 48 hours threshold
BEGIN
    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE('     BCSE302P EXPLICIT CURSOR DEMONSTRATION: OVERDUE UNCLAIMED PARCELS          ');
    DBMS_OUTPUT.PUT_LINE('     Criteria: Status = PENDING, Waiting Duration >= ' || c_threshold || ' Hours');
    DBMS_OUTPUT.PUT_LINE('================================================================================');
    DBMS_OUTPUT.PUT_LINE(
        RPAD('ID', 6) || 
        RPAD('TRACKING NO', 18) || 
        RPAD('STUDENT NAME', 20) || 
        RPAD('REG NO', 12) || 
        RPAD('BLOCK', 10) || 
        RPAD('SHELF', 12) || 
        'WAIT (HRS)'
    );
    DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');

    -- Cursor Lifecycle: OPEN
    OPEN c_unclaimed_parcels(c_threshold);

    -- Cursor Lifecycle: FETCH in LOOP
    LOOP
        FETCH c_unclaimed_parcels INTO v_parcel_rec;
        
        -- Cursor attribute %NOTFOUND to exit cleanly
        EXIT WHEN c_unclaimed_parcels%NOTFOUND;

        v_counter := v_counter + 1;

        DBMS_OUTPUT.PUT_LINE(
            RPAD(TO_CHAR(v_parcel_rec.parcel_id), 6) ||
            RPAD(v_parcel_rec.tracking_number, 18) ||
            RPAD(SUBSTR(v_parcel_rec.full_name, 1, 18), 20) ||
            RPAD(v_parcel_rec.reg_no, 12) ||
            RPAD(v_parcel_rec.hostel_block, 10) ||
            RPAD(v_parcel_rec.shelf_location, 12) ||
            TO_CHAR(v_parcel_rec.waiting_hours, '999.9')
        );
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');
    -- Cursor attribute %ROWCOUNT
    DBMS_OUTPUT.PUT_LINE('Cursor Fetched Rows: ' || c_unclaimed_parcels%ROWCOUNT);
    
    -- Cursor Lifecycle: CLOSE
    CLOSE c_unclaimed_parcels;

    IF v_counter = 0 THEN
        DBMS_OUTPUT.PUT_LINE('No parcels have exceeded the ' || c_threshold || '-hour waiting limit.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Action: Sent automated reminder notices to students and warden.');
    END IF;
    DBMS_OUTPUT.PUT_LINE('================================================================================');

EXCEPTION
    WHEN OTHERS THEN
        IF c_unclaimed_parcels%ISOPEN THEN
            CLOSE c_unclaimed_parcels;
        END IF;
        DBMS_OUTPUT.PUT_LINE('Exception caught in explicit cursor execution: ' || SQLERRM);
END;
/
