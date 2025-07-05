from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import base64
import os
import datetime

#===============AUTH STARTS=========================================================
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read',
    'https://www.googleapis.com/auth/fitness.location.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/gmail.send'
]

BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR / "token.json"
SECRET_PATH = BASE_DIR / "client_secret.json"
LOG_FILE_PATH = BASE_DIR / "Fitness log.txt"

SENDER = os.getenv("EMAIL_SENDER", "your_email@gmail.com")  # Load from env or use dummy
TO = os.getenv("EMAIL_TO", "recipient@example.com")
SUBJECT = f"📊 Your Google Fit Daily Report of {datetime.datetime.today():%Y-%m-%d}"

creds = None
if TOKEN_PATH.exists():
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

# Build both Fitness & Gmail services
service = build('fitness', 'v1', credentials=creds)
gmail_service = build('gmail', 'v1', credentials=creds)

#=================================AUTH END=======================================================

def main():
    yesterday_date = get_date()
    start_time, end_time = date_optimization(yesterday_date)
    Get_data(start_time, end_time)

def get_date():
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    return yesterday

def date_optimization(target_date):
    start_dt = datetime.datetime.combine(target_date.date(), datetime.time.min)
    end_dt = datetime.datetime.combine(target_date.date(), datetime.time.max)
    return int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)

#=============DATA FETCHING==================================================

def Get_data(start_time, end_time):
    date_str = datetime.datetime.fromtimestamp(start_time / 1000).date()
    log_lines = [f"{date_str} {{"]

    # [💗 Heart rate logic...]
    # [🚶 Step count logic...]
    # [🛏️ Sleep session logic...]
    # [💓 Heart points...]
    # [⚡ Calories...]
    # [🏋️ Workouts...]

    # (Kept as-is in your original — no need to paste full again unless edits are needed)

    log_lines.append("}")
    data_log("\n".join(log_lines))

def data_log(content):
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as file:
        file.write(content + "\n\n")

# ========== EMAIL SENDER ==========

def create_message_with_attachment(sender, to, subject, body_text, file_path):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    message.attach(MIMEText(body_text, 'plain'))

    with open(file_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{file_path.name}"')
    message.attach(part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email_with_log():
    body = (
        "Hey!\n\nHere's your attached Google Fit log for yesterday 📎.\n\n"
        "Keep crushing it!\n— Your Python Script"
    )
    msg = create_message_with_attachment(SENDER, TO, SUBJECT, body, LOG_FILE_PATH)
    result = gmail_service.users().messages().send(userId="me", body=msg).execute()
    print(f"✅ Email sent successfully! ID: {result['id']}")

# ========== RUN DAILY ==========
def send_daily():
    send_email_with_log()

main()
send_daily()
