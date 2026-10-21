import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from config import Config
from database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config.from_object(Config)

# Initialize database on app startup (wrapped to prevent serverless import crashes)
try:
    db.init_database()
except Exception as e:
    print(f"[WARN] Initial database startup connection failed: {e}")

@app.route("/static/<path:filename>")
def serve_static(filename):
    """Fallback static asset delivery for serverless environments."""
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

@app.route("/")
def index():
    """Main Reception Dashboard view."""
    return render_template("index.html", db_mode=db.mode)

@app.route("/api/debug-path")
def api_debug_path():
    return jsonify({
        "path": request.path,
        "url": request.url,
        "headers": dict(request.headers),
        "environ_path_info": request.environ.get("PATH_INFO"),
        "environ_matched_path": request.environ.get("HTTP_X_MATCHED_PATH"),
        "environ_raw_uri": request.environ.get("RAW_URI")
    })

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Returns dashboard KPI counts."""
    stats = db.get_dashboard_stats()
    return jsonify({"success": True, "data": stats})

@app.route("/api/parcels", methods=["GET"])
def api_parcels():
    """Returns list of registered parcels with optional filtering."""
    search = request.args.get("search", "")
    status = request.args.get("status", "ALL")
    block = request.args.get("block", "ALL")
    parcels = db.list_parcels(search=search, status=status, block=block)
    return jsonify({"success": True, "count": len(parcels), "data": parcels})

@app.route("/api/form-options", methods=["GET"])
def api_form_options():
    """Returns student, courier, and staff lists for select dropdowns."""
    return jsonify({
        "success": True,
        "students": db.get_students(),
        "couriers": db.get_couriers(),
        "staff": db.get_staff()
    })

@app.route("/api/parcels/register", methods=["POST"])
def api_register_parcel():
    """Registers an arriving parcel via the database procedure."""
    data = request.get_json() or {}
    tracking_no = data.get("tracking_number", "").strip()
    student_id = data.get("student_id")
    courier_id = data.get("courier_id")
    staff_id = data.get("staff_id", 201)
    shelf_loc = data.get("shelf_location", "").strip()
    remarks = data.get("remarks", "").strip()

    if not tracking_no or not student_id or not courier_id or not shelf_loc:
        return jsonify({
            "success": False,
            "message": "Missing required fields: Tracking Number, Student, Courier, and Shelf Location are mandatory."
        }), 400

    try:
        student_id = int(student_id)
        courier_id = int(courier_id)
        staff_id = int(staff_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid ID format."}), 400

    success, message, result = db.register_parcel(
        tracking_no=tracking_no,
        student_id=student_id,
        courier_id=courier_id,
        staff_id=staff_id,
        shelf_location=shelf_loc,
        remarks=remarks
    )

    if success:
        return jsonify({"success": True, "message": message, "result": result})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route("/api/parcels/verify-pickup", methods=["POST"])
def api_verify_pickup():
    """Verifies student pickup PIN code and marks parcel collected."""
    data = request.get_json() or {}
    parcel_id = data.get("parcel_id")
    entered_code = str(data.get("entered_code", "")).strip()
    staff_id = data.get("staff_id", 201)
    collector_reg = data.get("collector_reg_no", "").strip()
    remarks = data.get("remarks", "").strip()

    if not parcel_id or not entered_code:
        return jsonify({
            "success": False,
            "message": "Parcel selection and 6-digit pickup code are required."
        }), 400

    try:
        parcel_id = int(parcel_id)
        staff_id = int(staff_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid parcel ID."}), 400

    success, message = db.verify_pickup(
        parcel_id=parcel_id,
        entered_code=entered_code,
        staff_id=staff_id,
        collector_reg=collector_reg,
        remarks=remarks
    )

    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code

@app.route("/api/reports/overdue", methods=["GET"])
def api_overdue_report():
    """Runs explicit cursor logic for parcels exceeding waiting threshold."""
    hours_param = request.args.get("hours")
    threshold = float(hours_param) if hours_param else Config.OVERDUE_HOURS_THRESHOLD
    overdue_list = db.get_unclaimed_cursor_report(threshold_hours=threshold)
    return jsonify({
        "success": True,
        "threshold_hours": threshold,
        "count": len(overdue_list),
        "data": overdue_list
    })

@app.route("/api/audit-log", methods=["GET"])
def api_audit_log():
    """Returns database trigger audit trail."""
    logs = db.get_audit_trail()
    return jsonify({"success": True, "count": len(logs), "data": logs})

@app.route("/api/notifications", methods=["GET"])
def api_notifications():
    """Returns SMS and Email notification dispatch records."""
    notifs = db.get_notification_logs()
    return jsonify({"success": True, "count": len(notifs), "data": notifs})

@app.route("/api/notifications/send-overdue-reminders", methods=["POST"])
def api_send_overdue_reminders():
    """Auto-dispatches SMS and Email reminders to all students with overdue packages."""
    data = request.get_json() or {}
    hours_param = data.get("hours")
    threshold = float(hours_param) if hours_param else Config.OVERDUE_HOURS_THRESHOLD
    result = db.send_overdue_reminders(threshold_hours=threshold)
    return jsonify({
        "success": True,
        "message": f"Successfully dispatched automated Email alerts to {result['alerts_sent']} overdue recipients.",
        "data": result
    })

if __name__ == "__main__":
    import os
    import socket

    port = int(os.environ.get("PORT", 5000))
    if port == 5000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", 5000)) == 0:
                print(" * Port 5000 is occupied (e.g. by macOS AirPlay/ControlCenter). Switching to port 5001.")
                port = 5001

    print(f" * Launching Hostel Parcel Desk on http://0.0.0.0:{port} (LAN: http://172.16.146.181:{port})")
    app.run(host="0.0.0.0", port=port, debug=True)

