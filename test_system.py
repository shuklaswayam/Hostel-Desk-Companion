#!/usr/bin/env python3
"""
Automated Test Runner for Hostel Parcel Desk System
Verifies all 7 coursework test cases specified in the project problem statement.
"""

import sys
import unittest
import time
from database import db
from config import Config

class HostelParcelDeskTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 70)
        print(" HOSTEL PARCEL DESK: AUTOMATED TEST VERIFICATION SUITE")
        print(f" Database Mode: {db.mode.upper()}")
        print("=" * 70)
        db.init_database()

    def test_01_register_parcel_valid(self):
        """TC-1: Register a parcel with a valid unique tracking number -> record created"""
        track_no = f"TRK-TEST-{int(time.time())}"
        success, msg, data = db.register_parcel(
            tracking_no=track_no,
            student_id=101,
            courier_id=301,
            staff_id=201,
            shelf_location="Shelf A-88",
            remarks="Valid registration test"
        )
        self.assertTrue(success, f"Registration failed: {msg}")
        self.assertIsNotNone(data)
        self.assertIn("parcel_id", data)
        self.assertIn("pickup_code", data)
        self.assertEqual(len(data["pickup_code"]), 6)
        print(f" [PASS] TC-1: Created Parcel #{data['parcel_id']} with Code {data['pickup_code']}")

    def test_02_register_duplicate_tracking_number(self):
        """TC-2: Register a duplicate tracking number -> rejected by database constraint"""
        track_no = f"TRK-DUP-UNIQUE-{int(time.time())}"
        # First registration should succeed
        s1, m1, d1 = db.register_parcel(track_no, 102, 302, 201, "Shelf B-10", "Initial")
        self.assertTrue(s1)

        # Second registration with exact same tracking number MUST fail via DB constraint
        s2, m2, d2 = db.register_parcel(track_no, 103, 303, 201, "Shelf B-11", "Duplicate attempt")
        self.assertFalse(s2, "Duplicate tracking number was improperly accepted!")
        self.assertIn("already registered", m2.lower(), f"Unexpected error message: {m2}")
        print(f" [PASS] TC-2: Duplicate tracking correctly rejected by constraint -> '{m2}'")

    def test_03_verify_incorrect_pickup_code(self):
        """TC-3: Enter an incorrect pickup code -> collection rejected"""
        track_no = f"TRK-WRONG-CODE-{int(time.time())}"
        s, m, data = db.register_parcel(track_no, 104, 304, 201, "Shelf C-99", "Test wrong pin")
        self.assertTrue(s)
        parcel_id = data["parcel_id"]

        # Attempt verification with wrong code '000000'
        v_ok, v_msg = db.verify_pickup(parcel_id=parcel_id, entered_code="000000", staff_id=201)
        self.assertFalse(v_ok, "Wrong code was improperly verified!")
        self.assertIn("invalid", v_msg.lower())
        print(f" [PASS] TC-3: Incorrect code rejected -> '{v_msg}'")

    def test_04_verify_valid_pickup_code(self):
        """TC-4: Verify a valid pickup code -> parcel marked collected & pickup record created"""
        track_no = f"TRK-VALID-{int(time.time())}"
        s, m, data = db.register_parcel(track_no, 103, 305, 201, "Shelf D-44", "Test valid collection")
        self.assertTrue(s)
        parcel_id = data["parcel_id"]
        correct_code = data["pickup_code"]

        # Verify with valid code
        v_ok, v_msg = db.verify_pickup(
            parcel_id=parcel_id,
            entered_code=correct_code,
            staff_id=201,
            collector_reg="24BCE1210",
            remarks="Valid ID shown"
        )
        self.assertTrue(v_ok, f"Verification failed: {v_msg}")

        # Check parcel status is now COLLECTED
        parcels = db.list_parcels(search=track_no)
        self.assertEqual(len(parcels), 1)
        self.assertEqual(parcels[0]["status"], "COLLECTED")
        print(f" [PASS] TC-4: Valid code verified and status updated to COLLECTED")

    def test_05_prevent_duplicate_collection(self):
        """TC-5: Attempt to collect an already collected parcel -> second collection rejected"""
        track_no = f"TRK-DOUBLE-COLL-{int(time.time())}"
        s, m, data = db.register_parcel(track_no, 104, 301, 201, "Shelf A-12", "Test double collection")
        self.assertTrue(s)
        parcel_id = data["parcel_id"]
        code = data["pickup_code"]

        # First collection
        v1_ok, _ = db.verify_pickup(parcel_id, code, 201)
        self.assertTrue(v1_ok)

        # Second collection attempt MUST be rejected
        v2_ok, v2_msg = db.verify_pickup(parcel_id, code, 201)
        self.assertFalse(v2_ok, "Second collection was allowed!")
        self.assertIn("already been collected", v2_msg.lower())
        print(f" [PASS] TC-5: Duplicate collection blocked -> '{v2_msg}'")

    def test_06_audit_trigger_execution(self):
        """TC-6: Change a parcel's status -> audit trigger records the change in PARCEL_AUDIT"""
        track_no = f"TRK-AUDIT-{int(time.time())}"
        s, m, data = db.register_parcel(track_no, 101, 301, 201, "Shelf A-05", "Test audit trigger")
        self.assertTrue(s)
        parcel_id = data["parcel_id"]
        code = data["pickup_code"]

        # Transition status from PENDING to COLLECTED
        db.verify_pickup(parcel_id, code, 201)

        # Check PARCEL_AUDIT table for record
        audit_trail = db.get_audit_trail(limit=20)
        found = [a for a in audit_trail if a["parcel_id"] == parcel_id]
        self.assertGreater(len(found), 0, "No audit trail found for status transition!")
        self.assertEqual(found[0]["old_status"], "PENDING")
        self.assertEqual(found[0]["new_status"], "COLLECTED")
        print(f" [PASS] TC-6: Audit trigger trg_parcel_status_audit recorded transition PENDING -> COLLECTED")

    def test_07_explicit_cursor_overdue_parcels(self):
        """TC-7: Run overdue-parcel cursor -> pending parcels older than specified period are listed"""
        # Threshold 48 hours
        overdue_list = db.get_unclaimed_cursor_report(threshold_hours=48.0)
        self.assertIsInstance(overdue_list, list)
        # In seed data, we seeded parcels 1003 (52h) and 1004 (75h)
        overdue_ids = [p["parcel_id"] for p in overdue_list]
        self.assertTrue(any(pid in overdue_ids for pid in [1003, 1004]), "Seeded overdue parcels not detected!")
        for p in overdue_list:
            self.assertGreaterEqual(p["waiting_hours"], 48.0)
            self.assertEqual(p["status"], "PENDING")
        print(f" [PASS] TC-7: Explicit cursor identified {len(overdue_list)} overdue parcels (>= 48 hours)")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(HostelParcelDeskTests)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 70)
        print(" ALL 7 TEST CASES PASSED SUCCESSFULLY!")
        print("=" * 70)
        sys.exit(0)
    else:
        sys.exit(1)
