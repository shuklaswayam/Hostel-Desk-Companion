import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from config import Config
import urllib.request
import urllib.parse
import json

class NotificationPipeline:
    """
    Automated Notification Pipeline for Hostel Parcel Desk.
    Supports:
    - Real SMS delivery via Twilio REST API (with graceful sandbox simulation fallback)
    - Real Email delivery via standard SMTP (with graceful sandbox simulation fallback)
    - Automatic dispatch on parcel registration, collection, and overdue escalation
    """

    def __init__(self):
        self.sms_enabled = Config.SMS_ENABLED
        self.email_enabled = Config.EMAIL_ENABLED

        # Twilio SMS Config
        self.twilio_sid = Config.TWILIO_ACCOUNT_SID
        self.twilio_token = Config.TWILIO_AUTH_TOKEN
        self.twilio_from = Config.TWILIO_FROM_PHONE

        # SMTP Email Config
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_password = Config.SMTP_PASSWORD
        self.smtp_from = Config.SMTP_FROM_EMAIL

    def is_twilio_configured(self) -> bool:
        return bool(self.twilio_sid and self.twilio_token and self.twilio_from)

    def is_smtp_configured(self) -> bool:
        return bool(self.smtp_server and self.smtp_user and self.smtp_password)

    def send_sms(self, to_phone: str, message: str) -> Tuple[bool, str, str]:
        """
        Dispatches SMS to recipient.
        Uses Twilio API if credentials are provided in .env, otherwise logs cleanly to the system log.
        """
        if not self.sms_enabled:
            return True, "DISABLED", "SMS delivery disabled in config"

        if self.is_twilio_configured():
            try:
                import ssl
                try:
                    import certifi
                    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
                except Exception:
                    ssl_ctx = ssl.create_default_context()

                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
                data = urllib.parse.urlencode({
                    "To": to_phone,
                    "From": self.twilio_from,
                    "Body": message
                }).encode("utf-8")

                req = urllib.request.Request(url, data=data, method="POST")
                import base64
                auth_str = f"{self.twilio_sid}:{self.twilio_token}"
                b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")
                req.add_header("Authorization", f"Basic {b64_auth}")

                with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as response:
                    resp_body = response.read().decode("utf-8")
                    resp_json = json.loads(resp_body)
                    status = resp_json.get("status", "sent").upper()
                    print(f" * [SMS LIVE] Successfully sent to {to_phone} (SID: {resp_json.get('sid')})")
                    return True, "DELIVERED", f"Sent via Twilio ({status})"
            except urllib.error.HTTPError as e:
                err_detail = e.read().decode("utf-8", errors="ignore")
                print(f" * [SMS ERROR] Twilio HTTP {e.code} to {to_phone}: {err_detail}")
                return False, "FAILED", f"Twilio HTTP {e.code}: {err_detail}"
            except Exception as e:
                print(f" * [SMS ERROR] Failed to send via Twilio to {to_phone}: {e}")
                return False, "FAILED", f"Twilio error: {str(e)}"
        else:
            # Clean local sandbox simulation
            print(f" * [SMS DISPATCH] To: {to_phone} | Message: \"{message}\"")
            return True, "SENT", "Sent (Simulated Gateway)"

    def send_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> Tuple[bool, str, str]:
        """
        Dispatches multipart HTML/text email to recipient.
        Uses SMTP if configured, otherwise logs cleanly to the system log.
        """
        if not self.email_enabled:
            return True, "DISABLED", "Email delivery disabled in config"

        if self.is_smtp_configured():
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.smtp_from
                msg["To"] = to_email

                part1 = MIMEText(text_body, "plain")
                part2 = MIMEText(html_body, "html")
                msg.attach(part1)
                msg.attach(part2)

                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                if self.smtp_port in (587, 25):
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                server.quit()
                print(f" * [EMAIL LIVE] Successfully sent to {to_email} (Subject: {subject})")
                return True, "DELIVERED", "Sent via SMTP"
            except Exception as e:
                print(f" * [EMAIL ERROR] Failed to send via SMTP to {to_email}: {e}")
                return False, "FAILED", f"SMTP error: {str(e)}"
        else:
            # Clean local sandbox simulation
            print(f" * [EMAIL DISPATCH] To: {to_email} | Subject: \"{subject}\"")
            return True, "SENT", "Sent (Campus Mail Gateway)"

    def notify_parcel_registered(self, student: Dict[str, Any], parcel: Dict[str, Any], pickup_code: str, db_manager) -> Dict[str, Any]:
        """
        Automatically dispatches SMS and Email when a new parcel is logged.
        """
        student_name = student.get("full_name", "Student")
        phone = student.get("phone_no", "")
        email = student.get("email", "")
        tracking = parcel.get("tracking_number", "")
        shelf = parcel.get("shelf_location", "")
        courier = parcel.get("courier_name", "Carrier Delivery")
        parcel_id = parcel.get("parcel_id")
        student_id = student.get("student_id")

        # 1. SMS Dispatch
        if self.sms_enabled:
            sms_text = f"Hostel Parcel Desk: Parcel {tracking} ({courier}) arrived at {shelf}. Your Pickup PIN is {pickup_code}. Present this at the desk."
            sms_ok, sms_status, sms_info = self.send_sms(phone, sms_text)
            db_manager.log_notification(parcel_id, student_id, "READY_FOR_PICKUP", "SMS", sms_text, sms_status)
        else:
            sms_status, sms_info = "DISABLED", "SMS disabled in config"

        # 2. Email Dispatch
        email_subject = f"📦 Package Ready for Pickup: {tracking} (PIN: {pickup_code})"
        email_text = f"""Hello {student_name},

A new package has arrived for you at the Hostel Parcel Reception Desk.

Details:
• Tracking Number: {tracking}
• Courier: {courier}
• Storage Location: {shelf}
• Pickup Verification PIN: {pickup_code}

Please present your student ID and this 6-digit PIN code at the reception counter to collect your parcel.

Hostel Reception & Logistics Desk
"""
        email_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
  .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
  .header {{ background: #4f46e5; color: #ffffff; padding: 24px; text-align: center; }}
  .header h2 {{ margin: 0; font-size: 22px; }}
  .content {{ padding: 24px; }}
  .pin-box {{ background: #f1f5f9; border: 2px dashed #6366f1; border-radius: 8px; text-align: center; padding: 18px; margin: 20px 0; }}
  .pin-val {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #4338ca; font-family: monospace; }}
  .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
  .info-table td {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
  .label {{ color: #64748b; font-weight: 500; width: 40%; }}
  .value {{ font-weight: 600; color: #0f172a; }}
  .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2>📦 Parcel Arrived & Ready</h2>
    <p style="margin: 4px 0 0; font-size: 14px; opacity: 0.9;">Hostel Parcel Reception Desk</p>
  </div>
  <div class="content">
    <p>Hello <strong>{student_name}</strong>,</p>
    <p>A package addressed to you has arrived at the reception desk. Please use the verification PIN below to collect it.</p>
    
    <div class="pin-box">
      <div style="font-size: 12px; font-weight: 600; color: #6366f1; text-transform: uppercase; margin-bottom: 4px;">Your 6-Digit Pickup PIN</div>
      <div class="pin-val">{pickup_code}</div>
      <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Show this PIN at the counter during collection</div>
    </div>

    <table class="info-table">
      <tr><td class="label">Tracking Number</td><td class="value">{tracking}</td></tr>
      <tr><td class="label">Courier Service</td><td class="value">{courier}</td></tr>
      <tr><td class="label">Storage Location</td><td class="value">{shelf}</td></tr>
      <tr><td class="label">Hostel & Room</td><td class="value">{student.get('hostel_block', '')} • {student.get('room_no', '')}</td></tr>
    </table>
  </div>
  <div class="footer">
    Hostel Parcel Desk • Smart Campus Logistics & Student Services
  </div>
</div>
</body>
</html>
"""
        email_ok, email_status, email_info = self.send_email(email, email_subject, email_text, email_html)
        db_manager.log_notification(parcel_id, student_id, "READY_FOR_PICKUP", "EMAIL", f"Pickup PIN: {pickup_code} sent for {tracking} at {shelf}", email_status)

        return {
            "sms": {"status": sms_status, "detail": sms_info},
            "email": {"status": email_status, "detail": email_info}
        }

    def notify_parcel_collected(self, student: Dict[str, Any], parcel: Dict[str, Any], pickup: Dict[str, Any], db_manager) -> Dict[str, Any]:
        """
        Dispatches collection confirmation receipt via SMS and Email.
        """
        student_name = student.get("full_name", "Student")
        phone = student.get("phone_no", "")
        email = student.get("email", "")
        tracking = parcel.get("tracking_number", "")
        collector_reg = pickup.get("collector_reg_no", student.get("reg_no", ""))
        collected_at = pickup.get("collected_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
        parcel_id = parcel.get("parcel_id")
        student_id = student.get("student_id")

        # SMS Receipt
        if self.sms_enabled:
            sms_text = f"Hostel Parcel Desk: Parcel {tracking} was collected on {collected_at} by {collector_reg}. Verification confirmed."
            sms_ok, sms_status, sms_info = self.send_sms(phone, sms_text)
            db_manager.log_notification(parcel_id, student_id, "COLLECTED_CONFIRMATION", "SMS", sms_text, sms_status)
        else:
            sms_status, sms_info = "DISABLED", "SMS disabled in config"

        # Email Receipt
        email_subject = f"✅ Parcel Collection Confirmation: {tracking}"
        email_text = f"""Hello {student_name},

Your parcel {tracking} has been successfully verified and collected.

Collection Receipt:
• Tracking Number: {tracking}
• Collector Reg No: {collector_reg}
• Timestamp: {collected_at}
• Storage Cleared: {parcel.get('shelf_location', '')}

Thank you for picking up your delivery promptly!

Hostel Reception & Logistics Desk
"""
        email_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
  .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
  .header {{ background: #10b981; color: #ffffff; padding: 24px; text-align: center; }}
  .header h2 {{ margin: 0; font-size: 22px; }}
  .content {{ padding: 24px; }}
  .info-table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  .info-table td {{ padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
  .label {{ color: #64748b; font-weight: 500; width: 40%; }}
  .value {{ font-weight: 600; color: #0f172a; }}
  .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2>✅ Package Collection Confirmed</h2>
    <p style="margin: 4px 0 0; font-size: 14px; opacity: 0.9;">Official Pickup Receipt</p>
  </div>
  <div class="content">
    <p>Hello <strong>{student_name}</strong>,</p>
    <p>This email confirms that your parcel has been verified with your pickup PIN and handed over.</p>

    <table class="info-table">
      <tr><td class="label">Tracking Number</td><td class="value">{tracking}</td></tr>
      <tr><td class="label">Collector Reg No</td><td class="value">{collector_reg}</td></tr>
      <tr><td class="label">Handover Time</td><td class="value">{collected_at}</td></tr>
      <tr><td class="label">Status</td><td class="value" style="color:#10b981;">COLLECTED & COMPLETED</td></tr>
    </table>
  </div>
  <div class="footer">
    Hostel Parcel Desk • Smart Campus Logistics & Student Services
  </div>
</div>
</body>
</html>
"""
        email_ok, email_status, email_info = self.send_email(email, email_subject, email_text, email_html)
        db_manager.log_notification(parcel_id, student_id, "COLLECTED_CONFIRMATION", "EMAIL", f"Receipt issued for {tracking} (Collector: {collector_reg})", email_status)

        return {
            "sms": {"status": sms_status, "detail": sms_info},
            "email": {"status": email_status, "detail": email_info}
        }

    def notify_overdue(self, student: Dict[str, Any], parcel: Dict[str, Any], waiting_hours: float, db_manager) -> Dict[str, Any]:
        """
        Dispatches urgent reminder via SMS and Email for an overdue parcel.
        """
        student_name = student.get("full_name", "Student")
        phone = student.get("phone_no", "")
        email = student.get("email", "")
        tracking = parcel.get("tracking_number", "")
        shelf = parcel.get("shelf_location", "")
        code = parcel.get("pickup_code", "------")
        parcel_id = parcel.get("parcel_id")
        student_id = student.get("student_id")
        hours_str = f"{waiting_hours:.1f}"

        # SMS Overdue
        if self.sms_enabled:
            sms_text = f"URGENT: Your parcel {tracking} at {shelf} is OVERDUE ({hours_str}h). Please collect today with PIN {code}."
            sms_ok, sms_status, sms_info = self.send_sms(phone, sms_text)
            db_manager.log_notification(parcel_id, student_id, "OVERDUE_REMINDER", "SMS", sms_text, sms_status)
        else:
            sms_status, sms_info = "DISABLED", "SMS disabled in config"

        # Email Overdue
        email_subject = f"⚠️ Urgent: Overdue Parcel at Hostel Reception ({tracking})"
        email_text = f"""Hello {student_name},

URGENT REMINDER:
Your parcel {tracking} has been stored at shelf {shelf} for {hours_str} hours and is now flagged as OVERDUE.

Locker shelf space is limited. Please collect your package as soon as possible.

Pickup PIN: {code}
Location: {shelf}

Hostel Reception & Logistics Desk
"""
        email_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
  .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #fecaca; overflow: hidden; box-shadow: 0 4px 12px rgba(239,68,68,0.08); }}
  .header {{ background: #ef4444; color: #ffffff; padding: 24px; text-align: center; }}
  .header h2 {{ margin: 0; font-size: 22px; }}
  .content {{ padding: 24px; }}
  .alert-banner {{ background: #fef2f2; border: 1px solid #f87171; border-radius: 8px; padding: 12px; margin-bottom: 20px; color: #991b1b; font-size: 13.5px; line-height: 1.4; }}
  .pin-box {{ background: #f8fafc; border: 2px dashed #ef4444; border-radius: 8px; text-align: center; padding: 16px; margin: 16px 0; }}
  .pin-val {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #dc2626; font-family: monospace; }}
  .info-table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  .info-table td {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
  .label {{ color: #64748b; font-weight: 500; width: 40%; }}
  .value {{ font-weight: 600; color: #0f172a; }}
  .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2>⚠️ Overdue Package Reminder</h2>
    <p style="margin: 4px 0 0; font-size: 14px; opacity: 0.9;">Unclaimed for {hours_str} Hours</p>
  </div>
  <div class="content">
    <div class="alert-banner">
      <strong>Action Required:</strong> Storage racks are approaching capacity. Please retrieve your delivery immediately from the reception desk.
    </div>
    
    <p>Hello <strong>{student_name}</strong>,</p>
    <p>Your delivery has exceeded the allowable hostel waiting period. Details are listed below:</p>

    <div class="pin-box">
      <div style="font-size: 12px; font-weight: 600; color: #ef4444; text-transform: uppercase;">Your Pickup PIN</div>
      <div class="pin-val">{code}</div>
    </div>

    <table class="info-table">
      <tr><td class="label">Tracking Number</td><td class="value">{tracking}</td></tr>
      <tr><td class="label">Storage Shelf</td><td class="value">{shelf}</td></tr>
      <tr><td class="label">Waiting Duration</td><td class="value" style="color:#ef4444;">{hours_str} hours</td></tr>
    </table>
  </div>
  <div class="footer">
    Hostel Parcel Desk • Smart Campus Logistics & Student Services
  </div>
</div>
</body>
</html>
"""
        email_ok, email_status, email_info = self.send_email(email, email_subject, email_text, email_html)
        db_manager.log_notification(parcel_id, student_id, "OVERDUE_REMINDER", "EMAIL", f"Overdue alert sent ({hours_str}h unclaimed)", email_status)

        return {
            "sms": {"status": sms_status, "detail": sms_info},
            "email": {"status": email_status, "detail": email_info}
        }

pipeline = NotificationPipeline()
