-- ============================================================================
-- SCRIPT: 06_package_spec.sql
-- DESCRIPTION: PL/SQL Package Specification for Hostel Parcel Desk Operations
-- OBJECT: pkg_parcel_operations
-- ============================================================================

CREATE OR REPLACE PACKAGE pkg_parcel_operations AS

    -- Custom Exceptions
    e_invalid_code EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_invalid_code, -20021);

    e_already_collected EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_already_collected, -20022);

    -- Procedure 1: Register arriving parcel
    PROCEDURE pr_register_parcel (
        p_tracking_no   IN  VARCHAR2,
        p_student_id    IN  NUMBER,
        p_courier_id    IN  NUMBER,
        p_staff_id      IN  NUMBER,
        p_shelf_loc     IN  VARCHAR2,
        p_remarks       IN  VARCHAR2,
        p_parcel_id     OUT NUMBER,
        p_pickup_code   OUT VARCHAR2
    );

    -- Procedure 2: Verify pickup code and complete hand-over
    PROCEDURE pr_verify_pickup (
        p_parcel_id      IN  NUMBER,
        p_entered_code   IN  VARCHAR2,
        p_staff_id       IN  NUMBER,
        p_collector_reg  IN  VARCHAR2,
        p_remarks        IN  VARCHAR2,
        p_success_flag   OUT CHAR,
        p_message        OUT VARCHAR2
    );

    -- Function: Calculate elapsed waiting hours
    FUNCTION fn_parcel_waiting_hours (
        p_parcel_id IN NUMBER
    ) RETURN NUMBER;

    -- Procedure: Explicit cursor-based report for overdue packages
    PROCEDURE pr_print_unclaimed_report (
        p_threshold_hours IN NUMBER DEFAULT 48
    );

    -- Procedure: Fetch summary counts for reception dashboard
    PROCEDURE pr_get_metrics (
        p_total     OUT NUMBER,
        p_pending   OUT NUMBER,
        p_collected OUT NUMBER,
        p_overdue   OUT NUMBER
    );

END pkg_parcel_operations;
/
