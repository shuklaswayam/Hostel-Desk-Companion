-- ============================================================================
-- SCRIPT: 04_triggers.sql
-- DESCRIPTION: Database row-level trigger to audit parcel status transitions
-- OBJECT: trg_parcel_status_audit
-- ============================================================================

CREATE OR REPLACE TRIGGER trg_parcel_status_audit
AFTER UPDATE OF status ON PARCEL
FOR EACH ROW
WHEN (OLD.status != NEW.status)
DECLARE
    v_user VARCHAR2(50);
BEGIN
    -- Capture the current session user or OS user
    v_user := COALESCE(SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER'), 
                       SYS_CONTEXT('USERENV', 'SESSION_USER'), 
                       USER);

    -- Insert record into PARCEL_AUDIT
    INSERT INTO PARCEL_AUDIT (
        audit_id,
        parcel_id,
        old_status,
        new_status,
        changed_at,
        changed_by
    ) VALUES (
        SEQ_AUDIT.NEXTVAL,
        :NEW.parcel_id,
        :OLD.status,
        :NEW.status,
        SYSTIMESTAMP,
        v_user
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Prevent unhandled trigger errors from breaking transaction silently
        RAISE_APPLICATION_ERROR(-20002, 'Failed to insert status audit record: ' || SQLERRM);
END trg_parcel_status_audit;
/
