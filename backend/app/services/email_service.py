import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

def _send_email(to_email: str, student_name: str, subject: str, body: str):
    # Load SMTP config at runtime (after load_dotenv has been called)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    
    if not to_email:
        logger.warning("Skipping email for %s: no email address provided.", student_name)
        return

    if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.info(
            "[MOCK EMAIL - SMTP not configured]\n  To: %s\n  Subject: %s\n  Body:\n%s",
            to_email, subject, body,
        )
        return

    try:
        logger.info("Sending email to %s", to_email)
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        logger.debug("Connecting to %s:%s", SMTP_SERVER, SMTP_PORT)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        logger.debug("Authenticating as %s", SMTP_USERNAME)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        logger.info("Email sent to %s", to_email)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)


def send_attendance_email(to_email: str, student_name: str, status: str, date_str: str,faculty_name: str,):
    subject = f"Attendance Update - {date_str}"
    body = (
        f"Dear {student_name},\n\n"
        f"You have been marked as {status} for the class on {date_str}.\n\n"
        f"Regards,\n{faculty_name}"
    )
    _send_email(to_email, student_name, subject, body)


def send_attendance_marked_email(
    to_email: str,
    student_name: str,
    session_id: str,
    marked_at: datetime,
    section_name: str,
    faculty_name: str,
):
    marked_time = marked_at.strftime("%Y-%m-%d %H:%M:%S %Z") if marked_at else "N/A"
    subject = f"Attendance Marked - Session {session_id}"
    body = (
        f"Dear {student_name},\n\n"
        f"Your attendance has been marked as Present.\n"
        f"Section: {section_name}\n"
        f"Marked by: {faculty_name}\n"
        f"Session: {session_id}\n"
        f"Time: {marked_time}\n\n"
        f"Regards,\n{faculty_name}"
    )
    _send_email(to_email, student_name, subject, body)
