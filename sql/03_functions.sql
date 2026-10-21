-- ============================================================================
-- SCRIPT: 03_functions.sql
-- DESCRIPTION: PL/SQL Stored Function to calculate elapsed waiting hours for a parcel
-- OBJECT: fn_parcel_waiting_hours
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_parcel_waiting_hours (
    p_parcel_id IN NUMBER
) RETURN NUMBER IS
    v_arrival_time TIMESTAMP;
    v_hours_waiting NUMBER(8, 2);
BEGIN
    -- Retrieve the parcel arrival timestamp
    SELECT arrival_time
    INTO v_arrival_time
    FROM PARCEL
    WHERE parcel_id = p_parcel_id;

    -- Calculate difference between current timestamp and arrival time in hours
    -- In Oracle, subtracting two timestamps yields an INTERVAL DAY TO SECOND.
    -- We extract days, hours, minutes, and seconds to compute the exact fractional hours.
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
        -- Return -1 if parcel ID does not exist
        RETURN -1;
    WHEN OTHERS THEN
        RAISE_APPLICATION_ERROR(-20001, 'Error in fn_parcel_waiting_hours: ' || SQLERRM);
END fn_parcel_waiting_hours;
/

-- Verification query
-- SELECT parcel_id, tracking_number, status, fn_parcel_waiting_hours(parcel_id) AS hours_waiting FROM PARCEL;
