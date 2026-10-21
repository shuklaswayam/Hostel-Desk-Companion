import random
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from config import Config
from notifications import pipeline

# Optional Oracle support via python-oracledb Thin Mode
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False


class DatabaseManager:
    """
    Multi-mode Database Manager for Hostel Parcel Desk:
    - Postgres Mode: Connects to Supabase / PostgreSQL in the cloud via psycopg2,
      utilizing cloud-hosted tables, triggers, and automated notification logging.
    - Oracle Mode: Connects to Oracle 19c/21c/23c via python-oracledb Thin Mode,
      invoking stored procedures, packages, functions, and triggers.
    - SQLite Mode: Out-of-the-box local demo engine replicating the exact 7 tables,
      foreign keys, check constraints, triggers, and PL/SQL business logic.
    """

    def __init__(self):
        self.mode = Config.DB_MODE
        if self.mode == "oracle" and not ORACLE_AVAILABLE:
            print("[WARN] oracledb not installed or failed to import. Falling back to SQLite.")
            self.mode = "sqlite"

    def _sql(self, query: str) -> str:
        """Adapts SQL placeholder parameter syntax for PostgreSQL (%s) vs SQLite (?)."""
        if self.mode == "postgres":
            return query.replace("?", "%s")
        return query

    def get_connection(self):
        if self.mode == "postgres":
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
        elif self.mode == "oracle":
            return oracledb.connect(
                user=Config.ORACLE_USER,
                password=Config.ORACLE_PASSWORD,
                host=Config.ORACLE_HOST,
                port=Config.ORACLE_PORT,
                service_name=Config.ORACLE_SERVICE_NAME
            )
        else:
            conn = sqlite3.connect(Config.SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn

    def init_database(self):
        """Initializes tables and seeds test data if using SQLite or Supabase PostgreSQL."""
        if self.mode == "sqlite":
            self._init_sqlite_schema()
        elif self.mode == "postgres":
            self._init_postgres_schema()
        else:
            print("[INFO] Oracle mode configured. Ensure SQL scripts (01 to 07) have been run in Oracle SQL Developer.")

    def _init_postgres_schema(self):
        """Initializes schema and seed data on Supabase PostgreSQL if tables don't exist yet."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'student');")
            exists = list(cur.fetchone().values())[0]
            if not exists:
                print(" * Initializing Supabase PostgreSQL schema & seed data...")
                from pathlib import Path
                sql_path = Path(__file__).resolve().parent / "sql" / "supabase_setup.sql"
                with open(sql_path, "r") as f:
                    setup_sql = f.read()
                cur.execute(setup_sql)
                conn.commit()
                print(" * Supabase schema & initial seed ready.")
        except Exception as e:
            conn.rollback()
            print(f"[WARN] Failed to auto-init Supabase Postgres schema: {e}")
        finally:
            conn.close()

    def _init_sqlite_schema(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # Create Tables
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS STUDENT (
            student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no          TEXT NOT NULL UNIQUE,
            full_name       TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            phone_no        TEXT NOT NULL,
            hostel_block    TEXT NOT NULL CHECK (hostel_block IN ('Block A', 'Block B', 'Block C', 'Block D', 'Block E')),
            room_no         TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS STAFF (
            staff_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_code      TEXT NOT NULL UNIQUE,
            full_name       TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            phone_no        TEXT NOT NULL,
            staff_role      TEXT NOT NULL DEFAULT 'Receptionist' CHECK (staff_role IN ('Receptionist', 'Warden', 'Supervisor')),
            is_active       TEXT NOT NULL DEFAULT 'Y' CHECK (is_active IN ('Y', 'N'))
        );

        CREATE TABLE IF NOT EXISTS COURIER (
            courier_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name    TEXT NOT NULL UNIQUE,
            contact_phone   TEXT,
            service_type    TEXT NOT NULL DEFAULT 'Standard',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS PARCEL (
            parcel_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT NOT NULL UNIQUE,
            student_id      INTEGER NOT NULL REFERENCES STUDENT(student_id),
            courier_id      INTEGER NOT NULL REFERENCES COURIER(courier_id),
            registered_by   INTEGER NOT NULL REFERENCES STAFF(staff_id),
            arrival_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            shelf_location  TEXT NOT NULL,
            pickup_code     TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COLLECTED', 'OVERDUE', 'RETURNED')),
            remarks         TEXT
        );

        CREATE TABLE IF NOT EXISTS PICKUP_RECORD (
            pickup_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id        INTEGER NOT NULL UNIQUE REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
            verified_by      INTEGER NOT NULL REFERENCES STAFF(staff_id),
            collector_reg_no TEXT NOT NULL,
            collected_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            verification_mode TEXT NOT NULL DEFAULT 'CODE_VERIFIED',
            remarks          TEXT
        );

        CREATE TABLE IF NOT EXISTS PARCEL_AUDIT (
            audit_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id        INTEGER NOT NULL REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
            old_status       TEXT NOT NULL,
            new_status       TEXT NOT NULL,
            changed_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            changed_by       TEXT NOT NULL DEFAULT 'Reception Desk'
        );

        CREATE TABLE IF NOT EXISTS NOTIFICATION_LOG (
            notification_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id         INTEGER NOT NULL REFERENCES PARCEL(parcel_id) ON DELETE CASCADE,
            student_id        INTEGER NOT NULL REFERENCES STUDENT(student_id),
            notification_type TEXT NOT NULL CHECK (notification_type IN ('READY_FOR_PICKUP', 'OVERDUE_REMINDER', 'COLLECTED_CONFIRMATION')),
            channel           TEXT NOT NULL CHECK (channel IN ('SMS', 'EMAIL', 'SMS_SIMULATED', 'EMAIL_SIMULATED')),
            message_body      TEXT NOT NULL,
            sent_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            delivery_status   TEXT NOT NULL DEFAULT 'SENT'
        );

        -- Trigger mirroring trg_parcel_status_audit
        CREATE TRIGGER IF NOT EXISTS trg_parcel_status_audit
        AFTER UPDATE OF status ON PARCEL
        FOR EACH ROW
        WHEN OLD.status <> NEW.status
        BEGIN
            INSERT INTO PARCEL_AUDIT (parcel_id, old_status, new_status, changed_at, changed_by)
            VALUES (NEW.parcel_id, OLD.status, NEW.status, CURRENT_TIMESTAMP, 'Reception Desk');
        END;
        """)

        # Check if seed data exists
        cur.execute("SELECT COUNT(*) FROM STUDENT")
        if cur.fetchone()[0] == 0:
            self._seed_sqlite_data(conn)

        conn.commit()
        conn.close()

    def _seed_sqlite_data(self, conn):
        cur = conn.cursor()
        now = datetime.now(timezone.utc)

        # Students
        students = [
            (101, '24BCE1024', 'Arya Zachariah', 'arya.zachariah2024@vitstudent.ac.in', '+919447123456', 'Block E', 'E-204'),
            (102, '24BCE1082', 'Viraj Akili', 'viraj.akili2024@vitstudent.ac.in', '+919845123456', 'Block D', 'D-312'),
            (103, '24BCE1210', 'Niya Rachel Juban', 'niya.racheljuban2024@vitstudent.ac.in', '+919746123456', 'Block C', 'C-108'),
            (104, '24BCE1099', 'Swayam Shukla', 'shuklaswayam2006@gmail.com', '+919054556455', 'Block A', 'A-101')
        ]
        cur.executemany("INSERT INTO STUDENT (student_id, reg_no, full_name, email, phone_no, hostel_block, room_no) VALUES (?, ?, ?, ?, ?, ?, ?)", students)

        # Staff
        staff = [
            (201, 'STF-01', 'Ramesh Kumar', 'ramesh.k@vit.ac.in', '+919811122334', 'Receptionist', 'Y'),
            (202, 'STF-02', 'Sunita Rao', 'sunita.r@vit.ac.in', '+919822233445', 'Receptionist', 'Y'),
            (203, 'WRD-01', 'Dr. S. K. Mukherjee', 'sk.mukherjee@vit.ac.in', '+919833344556', 'Warden', 'Y')
        ]
        cur.executemany("INSERT INTO STAFF (staff_id, staff_code, full_name, email, phone_no, staff_role, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)", staff)

        # Couriers
        couriers = [
            (301, 'Amazon Delivery', '+9118003000900', 'Same-Day Express'),
            (302, 'Blue Dart Express', '+9118602331234', 'Air Priority'),
            (303, 'DTDC Courier', '+918025365511', 'Surface Standard'),
            (304, 'India Post Speed Post', '+9118002666868', 'National Postal'),
            (305, 'Delhivery Logistics', '+918069857000', 'E-commerce Courier')
        ]
        cur.executemany("INSERT INTO COURIER (courier_id, company_name, contact_phone, service_type) VALUES (?, ?, ?, ?)", couriers)

        # Varied arrival timestamps for waiting hours testing
        t_now = now
        t_2h = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        t_18h = (now - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
        t_52h = (now - timedelta(hours=52)).strftime("%Y-%m-%d %H:%M:%S")
        t_75h = (now - timedelta(hours=75)).strftime("%Y-%m-%d %H:%M:%S")
        t_26h = (now - timedelta(hours=26)).strftime("%Y-%m-%d %H:%M:%S")
        t_4h = (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        parcels = [
            (1001, 'TRK-AMZ-88214', 101, 301, 201, t_2h, 'Shelf E-04', '839201', 'PENDING', 'Electronics & Study Material'),
            (1002, 'TRK-BLU-67431', 102, 302, 201, t_18h, 'Shelf D-02', '512940', 'PENDING', 'Laptop Accessories Kit'),
            (1003, 'TRK-DTD-55102', 103, 303, 202, t_52h, 'Shelf C-01', '773192', 'PENDING', 'Important Document Consignment'),
            (1004, 'TRK-DEL-43920', 103, 305, 201, t_4h, 'Shelf C-03', '440183', 'PENDING', 'Apparel Delivery'),
            (1005, 'TRK-IND-90214', 104, 304, 201, t_26h, 'Shelf A-01', '918234', 'COLLECTED', 'Academic Certificate'),
            (1006, 'TRK-AMZ-31980', 104, 301, 201, t_2h, 'Shelf A-02', '332195', 'PENDING', 'Embedded Systems Dev Kit')
        ]
        cur.executemany("""INSERT INTO PARCEL 
            (parcel_id, tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", parcels)

        # Pickup Record for 1005
        cur.execute("""INSERT INTO PICKUP_RECORD 
            (pickup_id, parcel_id, verified_by, collector_reg_no, collected_at, verification_mode, remarks) 
            VALUES (5001, 1005, 201, '24BCE1099', ?, 'CODE_VERIFIED', 'Collected with verified PIN and Student ID')""", 
            ((now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),))

        # Initial Audit for 1005
        cur.execute("""INSERT INTO PARCEL_AUDIT 
            (audit_id, parcel_id, old_status, new_status, changed_at, changed_by) 
            VALUES (7001, 1005, 'PENDING', 'COLLECTED', ?, 'Reception Desk')""", 
            ((now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),))

        # Initial Notifications
        notifs = [
            (9001, 1001, 101, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Arya Zachariah, your parcel TRK-AMZ-88214 is ready at Reception (Shelf E-04). Pickup PIN: 839201.', t_2h, 'DELIVERED'),
            (9002, 1002, 102, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Viraj Akili, your parcel TRK-BLU-67431 is ready at Reception (Shelf D-02). Pickup PIN: 512940.', t_18h, 'DELIVERED'),
            (9003, 1003, 103, 'OVERDUE_REMINDER', 'EMAIL', 'REMINDER: Parcel TRK-DTD-55102 has been at Reception for 52 hours. Please collect promptly from Shelf C-01.', (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"), 'DELIVERED'),
            (9004, 1004, 103, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Niya Rachel Juban, your parcel TRK-DEL-43920 is ready at Reception (Shelf C-03). Pickup PIN: 440183.', t_4h, 'DELIVERED'),
            (9005, 1005, 104, 'COLLECTED_CONFIRMATION', 'EMAIL', 'Receipt: Parcel TRK-IND-90214 was collected successfully on time.', (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), 'DELIVERED'),
            (9006, 1006, 104, 'READY_FOR_PICKUP', 'EMAIL', 'Dear Swayam Shukla, your parcel TRK-AMZ-31980 is ready at Reception (Shelf A-02). Pickup PIN: 332195.', t_2h, 'DELIVERED')
        ]
        cur.executemany("""INSERT INTO NOTIFICATION_LOG 
            (notification_id, parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", notifs)

        conn.commit()

    # -------------------------------------------------------------------------
    # Business Logic & DBMS Object Emulation / Oracle Dispatch
    # -------------------------------------------------------------------------

    def fn_parcel_waiting_hours(self, parcel_id: int) -> float:
        """
        Calculates elapsed waiting hours for a parcel.
        Corresponds to PL/SQL function fn_parcel_waiting_hours.
        """
        conn = self.get_connection()
        try:
            if self.mode == "oracle":
                cur = conn.cursor()
                res = cur.callfunc("fn_parcel_waiting_hours", oracledb.NUMBER, [parcel_id])
                return float(res) if res is not None else -1.0
            else:
                cur = conn.cursor()
                cur.execute(self._sql("SELECT arrival_time FROM PARCEL WHERE parcel_id = ?"), (parcel_id,))
                row = cur.fetchone()
                if not row:
                    return -1.0
                arr_val = row["arrival_time"]
                if isinstance(arr_val, datetime):
                    dt = arr_val
                else:
                    arr_str = str(arr_val)
                    try:
                        dt = datetime.fromisoformat(arr_str.replace("Z", "+00:00"))
                    except ValueError:
                        dt = datetime.strptime(arr_str, "%Y-%m-%d %H:%M:%S")
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                diff = datetime.now(timezone.utc) - dt
                return round(diff.total_seconds() / 3600.0, 2)
        finally:
            conn.close()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Retrieves total, pending, collected, and overdue counts.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            if self.mode == "oracle":
                p_total = cur.var(oracledb.NUMBER)
                p_pending = cur.var(oracledb.NUMBER)
                p_collected = cur.var(oracledb.NUMBER)
                p_overdue = cur.var(oracledb.NUMBER)
                cur.callproc("pkg_parcel_operations.pr_get_metrics", [p_total, p_pending, p_collected, p_overdue])
                return {
                    "total": int(p_total.getvalue()),
                    "pending": int(p_pending.getvalue()),
                    "collected": int(p_collected.getvalue()),
                    "overdue": int(p_overdue.getvalue()),
                    "mode": "Oracle PL/SQL"
                }
            else:
                def _fetch_scalar(c):
                    res = c.fetchone()
                    if res is None:
                        return 0
                    if isinstance(res, dict):
                        return list(res.values())[0]
                    return res[0]

                cur.execute("SELECT COUNT(*) FROM PARCEL")
                total = _fetch_scalar(cur)

                cur.execute("SELECT COUNT(*) FROM PARCEL WHERE status = 'PENDING'")
                pending = _fetch_scalar(cur)

                cur.execute("SELECT COUNT(*) FROM PARCEL WHERE status = 'COLLECTED'")
                collected = _fetch_scalar(cur)

                # Overdue: pending and arrival_time older than threshold
                threshold_time = (datetime.now(timezone.utc) - timedelta(hours=Config.OVERDUE_HOURS_THRESHOLD)).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(self._sql("SELECT COUNT(*) FROM PARCEL WHERE status = 'PENDING' AND arrival_time <= ?"), (threshold_time,))
                overdue = _fetch_scalar(cur)

                db_mode_label = "Supabase (PostgreSQL Cloud)" if self.mode == "postgres" else "SQLite (Coursework Mirror)"
                return {
                    "total": total,
                    "pending": pending,
                    "collected": collected,
                    "overdue": overdue,
                    "mode": db_mode_label
                }
        finally:
            conn.close()

    def list_parcels(self, search: Optional[str] = None, status: Optional[str] = None, block: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves parcels joined with student, courier, and staff information.
        Enriches records with calculated waiting hours.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
            SELECT 
                p.parcel_id, p.tracking_number, p.arrival_time, p.shelf_location, p.pickup_code, p.status, p.remarks,
                s.student_id, s.reg_no, s.full_name AS student_name, s.hostel_block, s.room_no, s.phone_no AS student_phone,
                c.company_name AS courier_name,
                st.full_name AS staff_name
            FROM PARCEL p
            JOIN STUDENT s ON p.student_id = s.student_id
            JOIN COURIER c ON p.courier_id = c.courier_id
            JOIN STAFF st ON p.registered_by = st.staff_id
            WHERE 1=1
            """
            params = []

            if status and status.upper() != "ALL":
                query += " AND p.status = ?"
                params.append(status.upper())

            if block and block.upper() != "ALL":
                query += " AND s.hostel_block = ?"
                params.append(block)

            if search:
                pattern = f"%{search.strip()}%"
                query += " AND (p.tracking_number LIKE ? OR s.reg_no LIKE ? OR s.full_name LIKE ? OR p.shelf_location LIKE ?)"
                params.extend([pattern, pattern, pattern, pattern])

            query += " ORDER BY p.arrival_time DESC"

            cur.execute(self._sql(query), params)
            rows = cur.fetchall()

            parcels = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("arrival_time"), datetime):
                    item["arrival_time"] = item["arrival_time"].strftime("%Y-%m-%d %H:%M:%S")
                waiting = self.fn_parcel_waiting_hours(item["parcel_id"])
                item["waiting_hours"] = waiting
                item["is_overdue"] = (item["status"] == "PENDING" and waiting >= Config.OVERDUE_HOURS_THRESHOLD)
                parcels.append(item)

            return parcels
        finally:
            conn.close()

    def register_parcel(self, tracking_no: str, student_id: int, courier_id: int, staff_id: int, shelf_location: str, remarks: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Invokes registration procedure:
        - Validates input foreign keys
        - Enforces UNIQUE constraint on tracking number
        - Generates random 6-digit pickup code
        - Inserts notification log
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            tracking_no = tracking_no.strip()

            if self.mode == "oracle":
                p_parcel_id = cur.var(oracledb.NUMBER)
                p_code = cur.var(oracledb.STRING)
                try:
                    cur.callproc("pkg_parcel_operations.pr_register_parcel", [
                        tracking_no, student_id, courier_id, staff_id, shelf_location, remarks, p_parcel_id, p_code
                    ])
                    return True, "Parcel registered successfully in Oracle database.", {
                        "parcel_id": int(p_parcel_id.getvalue()),
                        "pickup_code": str(p_code.getvalue()),
                        "tracking_number": tracking_no
                    }
                except oracledb.DatabaseError as e:
                    error_obj, = e.args
                    return False, f"Oracle Error [{error_obj.code}]: {error_obj.message}", None
            else:
                # 1. Validate student
                cur.execute(self._sql("SELECT student_id, full_name, email, phone_no, hostel_block, room_no, reg_no FROM STUDENT WHERE student_id = ?"), (student_id,))
                st_row = cur.fetchone()
                if not st_row:
                    return False, f"Validation Error: Student ID {student_id} not found.", None
                student_info = dict(st_row)
                student_name = student_info["full_name"]

                # 2. Validate courier
                cur.execute(self._sql("SELECT courier_id, company_name FROM COURIER WHERE courier_id = ?"), (courier_id,))
                c_row = cur.fetchone()
                if not c_row:
                    return False, f"Validation Error: Courier ID {courier_id} not found.", None
                courier_name = c_row["company_name"]

                # 3. Validate staff
                cur.execute(self._sql("SELECT staff_id FROM STAFF WHERE staff_id = ? AND is_active = 'Y'"), (staff_id,))
                if not cur.fetchone():
                    return False, f"Validation Error: Staff ID {staff_id} is invalid or inactive.", None

                # 4. Check unique tracking number constraint
                cur.execute(self._sql("SELECT parcel_id FROM PARCEL WHERE tracking_number = ?"), (tracking_no,))
                if cur.fetchone():
                    return False, f"Database Constraint Violation: Tracking number '{tracking_no}' is already registered.", None

                # 5. Generate 6-digit pickup code
                pickup_code = str(random.randint(100000, 999999))
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                if self.mode == "postgres":
                    cur.execute("""
                    INSERT INTO PARCEL (tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING', %s)
                    RETURNING parcel_id
                    """, (tracking_no, student_id, courier_id, staff_id, now_str, shelf_location, pickup_code, remarks))
                    res_row = cur.fetchone()
                    parcel_id = res_row["parcel_id"] if isinstance(res_row, dict) else res_row[0]
                else:
                    cur.execute("""
                    INSERT INTO PARCEL (tracking_number, student_id, courier_id, registered_by, arrival_time, shelf_location, pickup_code, status, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
                    """, (tracking_no, student_id, courier_id, staff_id, now_str, shelf_location, pickup_code, remarks))
                    parcel_id = cur.lastrowid
                conn.commit()

                # 6. Auto-send SMS and Email alerts
                parcel_info = {
                    "parcel_id": parcel_id,
                    "tracking_number": tracking_no,
                    "shelf_location": shelf_location,
                    "courier_name": courier_name
                }
                pipeline.notify_parcel_registered(student_info, parcel_info, pickup_code, self)

                return True, "Parcel registered successfully.", {
                    "parcel_id": parcel_id,
                    "pickup_code": pickup_code,
                    "tracking_number": tracking_no
                }
        finally:
            conn.close()

    def verify_pickup(self, parcel_id: int, entered_code: str, staff_id: int, collector_reg: Optional[str] = None, remarks: str = "") -> Tuple[bool, str]:
        """
        Executes pickup verification:
        - Validates parcel status (prevents double-collection)
        - Compares pickup code with stored database code
        - Updates status to 'COLLECTED' (triggers audit logging)
        - Inserts into PICKUP_RECORD
        - Dispatches automated completion receipt via SMS & Email
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            entered_code = entered_code.strip()

            if self.mode == "oracle":
                p_flag = cur.var(oracledb.STRING)
                p_msg = cur.var(oracledb.STRING)
                try:
                    cur.callproc("pkg_parcel_operations.pr_verify_pickup", [
                        parcel_id, entered_code, staff_id, collector_reg or "", remarks or "", p_flag, p_msg
                    ])
                    flag = str(p_flag.getvalue()).strip()
                    msg = str(p_msg.getvalue()).strip()
                    return (flag == 'Y'), msg
                except oracledb.DatabaseError as e:
                    error_obj, = e.args
                    return False, f"Oracle Error [{error_obj.code}]: {error_obj.message}"
            else:
                cur.execute(self._sql("""
                SELECT p.parcel_id, p.tracking_number, p.shelf_location, p.pickup_code, p.status, p.student_id,
                       s.reg_no, s.full_name, s.phone_no, s.email, s.hostel_block, s.room_no
                FROM PARCEL p
                JOIN STUDENT s ON p.student_id = s.student_id
                WHERE p.parcel_id = ?
                """), (parcel_id,))
                row = cur.fetchone()

                if not row:
                    return False, f"Error: Parcel ID #{parcel_id} not found."

                current_status = row["status"]
                actual_code = row["pickup_code"]
                tracking_no = row["tracking_number"]
                student_reg = row["reg_no"]
                student_name = row["full_name"]
                student_id = row["student_id"]

                # Rule 1: Cannot collect already collected package
                if current_status == "COLLECTED":
                    return False, f"Rejection: Parcel '{tracking_no}' has already been collected."

                if current_status == "RETURNED":
                    return False, f"Rejection: Parcel '{tracking_no}' has been marked as returned to sender."

                # Rule 2: Code must match
                if entered_code != actual_code:
                    return False, f"Rejection: Invalid pickup code entered. Collection rejected."

                # Status transition to COLLECTED (Fires trg_parcel_status_audit!)
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(self._sql("UPDATE PARCEL SET status = 'COLLECTED' WHERE parcel_id = ?"), (parcel_id,))

                # Insert into PICKUP_RECORD
                cur.execute(self._sql("""
                INSERT INTO PICKUP_RECORD (parcel_id, verified_by, collector_reg_no, collected_at, verification_mode, remarks)
                VALUES (?, ?, ?, ?, 'CODE_VERIFIED', ?)
                """), (parcel_id, staff_id, collector_reg or student_reg, now_str, remarks or "Verified with valid PIN"))

                conn.commit()

                # Dispatch automated collection receipt via SMS and Email
                student_info = {
                    "student_id": student_id,
                    "full_name": student_name,
                    "reg_no": student_reg,
                    "phone_no": row["phone_no"],
                    "email": row["email"]
                }
                parcel_info = {
                    "parcel_id": parcel_id,
                    "tracking_number": tracking_no,
                    "shelf_location": row["shelf_location"]
                }
                pickup_info = {
                    "collector_reg_no": collector_reg or student_reg,
                    "collected_at": now_str
                }
                pipeline.notify_parcel_collected(student_info, parcel_info, pickup_info, self)

                return True, f"Success! Parcel {tracking_no} verified and marked as COLLECTED for {student_name}."
        finally:
            conn.close()

    def get_unclaimed_cursor_report(self, threshold_hours: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Implements explicit cursor c_unclaimed_parcels logic.
        Iterates over pending parcels waiting >= threshold_hours.
        """
        threshold = threshold_hours if threshold_hours is not None else Config.OVERDUE_HOURS_THRESHOLD
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
            SELECT 
                p.parcel_id, p.tracking_number, p.arrival_time, p.shelf_location, p.status,
                s.student_id, s.reg_no, s.full_name AS student_name, s.hostel_block, s.room_no, s.phone_no AS student_phone,
                c.company_name AS courier_name
            FROM PARCEL p
            JOIN STUDENT s ON p.student_id = s.student_id
            JOIN COURIER c ON p.courier_id = c.courier_id
            WHERE p.status = 'PENDING'
            ORDER BY p.arrival_time ASC
            """
            cur.execute(self._sql(query))
            rows = cur.fetchall()

            unclaimed = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("arrival_time"), datetime):
                    item["arrival_time"] = item["arrival_time"].strftime("%Y-%m-%d %H:%M:%S")
                waiting = self.fn_parcel_waiting_hours(item["parcel_id"])
                if waiting >= threshold:
                    item["waiting_hours"] = waiting
                    unclaimed.append(item)

            return unclaimed
        finally:
            conn.close()

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves audit trail recorded by trg_parcel_status_audit."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
            SELECT a.audit_id, a.parcel_id, a.old_status, a.new_status, a.changed_at, a.changed_by,
                   p.tracking_number, s.full_name AS student_name, s.reg_no
            FROM PARCEL_AUDIT a
            JOIN PARCEL p ON a.parcel_id = p.parcel_id
            JOIN STUDENT s ON p.student_id = s.student_id
            ORDER BY a.changed_at DESC
            LIMIT ?
            """
            cur.execute(self._sql(query), (limit,))
            res = []
            for r in cur.fetchall():
                item = dict(r)
                if isinstance(item.get("changed_at"), datetime):
                    item["changed_at"] = item["changed_at"].strftime("%Y-%m-%d %H:%M:%S")
                res.append(item)
            return res
        finally:
            conn.close()

    def log_notification(self, parcel_id: int, student_id: int, notification_type: str, channel: str, message_body: str, delivery_status: str = "SENT"):
        """Logs a dispatched SMS or Email notification into NOTIFICATION_LOG."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            query = """
            INSERT INTO NOTIFICATION_LOG (parcel_id, student_id, notification_type, channel, message_body, sent_at, delivery_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cur.execute(self._sql(query), (parcel_id, student_id, notification_type, channel, message_body, now_str, delivery_status))
            conn.commit()
        finally:
            conn.close()

    def send_overdue_reminders(self, threshold_hours: Optional[float] = None) -> Dict[str, Any]:
        """Scans for overdue packages and automatically triggers SMS and Email alerts."""
        overdue_list = self.get_unclaimed_cursor_report(threshold_hours=threshold_hours)
        sent_count = 0
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            for p in overdue_list:
                cur.execute(self._sql("SELECT student_id, full_name, email, phone_no, hostel_block, room_no, reg_no FROM STUDENT WHERE student_id = ?"), (p["student_id"],))
                st_row = cur.fetchone()
                if st_row:
                    student_info = dict(st_row)
                    # Fetch code for parcel
                    cur.execute(self._sql("SELECT pickup_code FROM PARCEL WHERE parcel_id = ?"), (p["parcel_id"],))
                    code_row = cur.fetchone()
                    pickup_code = code_row["pickup_code"] if code_row else "------"
                    p_copy = dict(p)
                    p_copy["pickup_code"] = pickup_code
                    pipeline.notify_overdue(student_info, p_copy, p["waiting_hours"], self)
                    sent_count += 1
            return {
                "success": True,
                "overdue_found": len(overdue_list),
                "alerts_sent": sent_count,
                "channels": ["SMS", "EMAIL"]
            }
        finally:
            conn.close()

    def get_notification_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves automated SMS and Email notification logs."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
            SELECT n.notification_id, n.parcel_id, n.notification_type, n.channel, n.message_body, n.sent_at, n.delivery_status,
                   p.tracking_number, s.full_name AS student_name, s.phone_no, s.email AS student_email
            FROM NOTIFICATION_LOG n
            JOIN PARCEL p ON n.parcel_id = p.parcel_id
            JOIN STUDENT s ON n.student_id = s.student_id
            ORDER BY n.sent_at DESC
            LIMIT ?
            """
            cur.execute(self._sql(query), (limit,))
            res = []
            for r in cur.fetchall():
                item = dict(r)
                if isinstance(item.get("sent_at"), datetime):
                    item["sent_at"] = item["sent_at"].strftime("%Y-%m-%d %H:%M:%S")
                res.append(item)
            return res
        finally:
            conn.close()

    def get_students(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(self._sql("SELECT student_id, reg_no, full_name, hostel_block, room_no FROM STUDENT ORDER BY reg_no ASC"))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_couriers(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(self._sql("SELECT courier_id, company_name, service_type FROM COURIER ORDER BY company_name ASC"))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_staff(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(self._sql("SELECT staff_id, staff_code, full_name, staff_role FROM STAFF WHERE is_active = 'Y' ORDER BY staff_id ASC"))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


db = DatabaseManager()
