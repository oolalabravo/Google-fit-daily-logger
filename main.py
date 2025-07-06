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
    'https://www.googleapis.com/auth/fitness.body.read'
    
]
SCOPES2 = [
    'https://www.googleapis.com/auth/gmail.send'
]
BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR / "token.json"
TOKEN_PATH2=BASE_DIR / 'token2.json'
SECRET_PATH = BASE_DIR / "client_secret.json"
LOG_FILE_PATH = BASE_DIR / "Fitness log.txt"
SENDER = "examplw@example.com"  # 🔒 Replace or load via env vars
TO = "reciver@example.com"
SUBJECT = f"📊 Your Google Fit Daily Report of {datetime.datetime.today()}"



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

creds2 = None
if TOKEN_PATH2.exists():
    creds2 = Credentials.from_authorized_user_file(str(TOKEN_PATH2), SCOPES2)

if not creds2 or not creds2.valid:
    if creds2 and creds2.expired and creds2.refresh_token:
        creds2.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_PATH), SCOPES2)
        creds2 = flow.run_local_server(port=0)
    with open(TOKEN_PATH2, 'w') as token:
        token.write(creds2.to_json())

# Build both Fitness & Gmail services
service = build('fitness', 'v1', credentials=creds)
gmail_service = build('gmail', 'v1', credentials=creds2)
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

    start_time_millis = int(start_dt.timestamp() * 1000)
    end_time_millis = int(end_dt.timestamp() * 1000)
    return start_time_millis, end_time_millis

#=============DATA FETCHING==================================================

def Get_data(start_time, end_time):
    date_str = datetime.datetime.fromtimestamp(start_time / 1000).date()
    log_lines = [f"{date_str} {{"]

    # ------------------ HEART RATE ------------------
    heart_rates = []
    hr_response = service.users().dataset().aggregate(userId="me", body={
        "aggregateBy": [{
            "dataTypeName": "com.google.heart_rate.bpm",
            "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
        }],
        "bucketByTime": {"durationMillis": 300000},
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }).execute()

    for bucket in hr_response.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                if not point.get("value"):
                    continue
                start = int(point["startTimeNanos"]) / 1e9
                end = int(point["endTimeNanos"]) / 1e9
                avg_bpm = point["value"][0].get("fpVal")
                if avg_bpm is not None:
                    start_time_str = datetime.datetime.fromtimestamp(start).strftime("%H:%M:%S")
                    end_time_str = datetime.datetime.fromtimestamp(end).strftime("%H:%M:%S")
                    log_lines.append(f"\t🕓 {start_time_str} - {end_time_str} → 💗 {avg_bpm:.2f} bpm")
                    heart_rates.append(avg_bpm)

    if heart_rates:
        avg_day_hr = sum(heart_rates) / len(heart_rates)
        log_lines.append(f"\t📊 Avg Heart Rate: {avg_day_hr:.2f} bpm")

    # ------------------ STEP COUNT ------------------
    step_response = service.users().dataset().aggregate(userId="me", body={
        "aggregateBy": [{
            "dataTypeName": "com.google.step_count.delta",
            "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
        }],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }).execute()

    total_steps = 0
    for bucket in step_response.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                total_steps += point["value"][0].get("intVal", 0)

    log_lines.append(f"\t🚶 Step Count: {total_steps} steps")

# ------------------ SLEEP (Session + Segment summary + Grouped Duration) ------------------
 
    # ========= DATE SETUP =========== 
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    start_dt = datetime.datetime.combine(yesterday.date(), datetime.time.min)
    end_dt = datetime.datetime.combine(yesterday.date(), datetime.time.max)
    start_time = int(start_dt.timestamp() * 1000)
    end_time = int(end_dt.timestamp() * 1000)

    # print(f"\n📆 Sleep debug for: {yesterday.date()}")

    # ========= SESSION FETCH ============ 
    session_response = service.users().sessions().list(
        userId="me",
        startTime=start_dt.isoformat() + 'Z',
        endTime=end_dt.isoformat() + 'Z'
    ).execute()

    sessions = session_response.get("session", [])
    #print(f"📡 Found {len(sessions)} sessions\n")

    has_sleep_session = False

    for session in sessions:
        activity_type = session.get("activityType")
        name = session.get("name", "Unnamed session")
        s_start = session.get("startTime")
        s_end = session.get("endTime")

        #print(f"📝 Session: {name} | Type: {activity_type} | ⏰ {s_start or 'N/A'} to {s_end or 'N/A'}")

        if activity_type == 72:
            has_sleep_session = True
            #print("✅ Detected session with activityType = 72 (Sleep)")

            if s_start and s_end:
                s_start_dt = datetime.datetime.fromisoformat(s_start[:-1])
                s_end_dt = datetime.datetime.fromisoformat(s_end[:-1])
            else:
                #print("⚠️ Session missing start/end time. Using full-day range.")
                s_start_dt = start_dt
                s_end_dt = end_dt

            start_ns = int(s_start_dt.timestamp() * 1e9)
            end_ns = int(s_end_dt.timestamp() * 1e9)
            dataset_id = f"{start_ns}-{end_ns}"

            # Detect datasource
            ds_list = service.users().dataSources().list(userId="me").execute()
            segment_ds_id = next((ds["dataStreamId"] for ds in ds_list.get("dataSource", [])
                                if "com.google.sleep.segment" in ds.get("dataStreamId", "")), None)

            if not segment_ds_id:
                #print("❌ No sleep segment datasource found.")
                continue

            segment_data = service.users().dataSources().datasets().get(
                userId="me", dataSourceId=segment_ds_id, datasetId=dataset_id
            ).execute()

            sleep_stage_names = {
                1: "Awake",
                2: "Sleep (generic)",
                3: "Out-of-bed",
                4: "Light sleep",
                5: "Deep sleep",
                6: "REM sleep"
            }

            stage_durations = {
                "Awake": 0,
                "Light sleep": 0,
                "Deep sleep": 0,
                "REM sleep": 0
            }

            all_segments = []

            #print("\n🛏️ Sleep Segments:")
            for point in segment_data.get("point", []):
                stage_val = point["value"][0]["intVal"]
                seg_start = datetime.datetime.fromtimestamp(int(point["startTimeNanos"]) / 1e9)
                seg_end = datetime.datetime.fromtimestamp(int(point["endTimeNanos"]) / 1e9)
                duration = (seg_end - seg_start).total_seconds()

                stage_name = sleep_stage_names.get(stage_val, f"Unknown ({stage_val})")
                #print(f"   💤 {seg_start.strftime('%H:%M')} - {seg_end.strftime('%H:%M')} → {stage_name}")
                log_lines.append(f"   💤 {seg_start.strftime('%H:%M')} - {seg_end.strftime('%H:%M')} → {stage_name}")

                if stage_name in stage_durations:
                    stage_durations[stage_name] += duration
                    all_segments.append((seg_start, seg_end))

            # ====== FULL SLEEP WINDOW ==========
            if all_segments:
                full_start = min(seg[0] for seg in all_segments)
                full_end = max(seg[1] for seg in all_segments)
                full_sleep_duration = (full_end - full_start).total_seconds()
                
                #print("\n⏱️ Full Sleep Duration (based on 1st to last segment):")
                #print(f"   🛌 {full_start.strftime('%H:%M')} → {full_end.strftime('%H:%M')}  |  🕓 {round(full_sleep_duration / 3600, 2)} hrs")
                log_lines.append(f"   Sleep   🛌 {full_start.strftime('%H:%M')} → {full_end.strftime('%H:%M')}  |  🕓 {round(full_sleep_duration / 3600, 2)} hrs")

            # ====== SUMMARY ==========
            #print("\n📊 Sleep Stage Summary:")
            for stage, seconds in stage_durations.items():
                hrs = round(seconds / 3600, 2)
                #print(f"   • {stage}: {hrs} hrs")
                log_lines.append(f"   • {stage}: {hrs} hrs")

    if not has_sleep_session:
        #print("\n❌ No session with activityType 72 (Sleep) found.")
        #print("💡 NoiseFit may be syncing sleep in a different format or missing time fields.")
        




        # ------------------ HEART POINTS ------------------
        hp_response = service.users().dataset().aggregate(userId="me", body={
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_minutes",
                "dataSourceId": "derived:com.google.heart_minutes:com.google.android.gms:merge_heart_minutes"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }).execute()

        heart_points = 0
        for bucket in hp_response.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    heart_points += point["value"][0].get("fpVal", 0)

        log_lines.append(f"\t💓 Heart Points: {heart_points:.2f}")

    # ------------------ ENERGY EXPENDED ------------------
    energy_response = service.users().dataset().aggregate(userId="me", body={
        "aggregateBy": [{
            "dataTypeName": "com.google.calories.expended",
            "dataSourceId": "derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended"
        }],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }).execute()

    total_calories = 0
    for bucket in energy_response.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                total_calories += point["value"][0].get("fpVal", 0)

    log_lines.append(f"\t⚡ Energy Expended: {total_calories:.2f} kcal")

    # ------------------ WORKOUT SESSIONS ------------------
    sessions = service.users().sessions().list(userId="me", startTime=datetime.datetime.fromtimestamp(start_time / 1000).isoformat() + 'Z', endTime=datetime.datetime.fromtimestamp(end_time / 1000).isoformat() + 'Z').execute()

    workout_count = 0
    workouts = []
    for session in sessions.get("session", []):
        if session.get("activityType") not in [72, 109]:  # skip sleep
            workout_count += 1
            name = session.get("name", "Workout")
            workouts.append(name)

    if workout_count > 0:
        log_lines.append(f"\t🏋️ Workout Sessions: {workout_count} ({', '.join(workouts)})")
    else:
        log_lines.append("\t🏋️ Workout Sessions: 0")

    log_lines.append("}")
    data_log("\n".join(log_lines))


def data_log(content):
    with open(r"F:\programs\Google Fit\Fitness log.txt", "a", encoding="utf-8") as file:
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
    #log_fitness_data()
    send_email_with_log()


main()
# 🟢 Start Now
send_daily()
