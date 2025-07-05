from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
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

TOKEN_PATH = os.path.join(os.getcwd(), "token.json")
CLIENT_SECRET_PATH = os.path.join(os.getcwd(), "client_secret.json")

creds = None
if os.path.exists(TOKEN_PATH):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

service = build('fitness', 'v1', credentials=creds)
#=============================AUTH ENDS=================================================

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

    # ========= SLEEP SETUP =========
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    start_dt = datetime.datetime.combine(yesterday.date(), datetime.time.min)
    end_dt = datetime.datetime.combine(yesterday.date(), datetime.time.max)
    start_time = int(start_dt.timestamp() * 1000)
    end_time = int(end_dt.timestamp() * 1000)

    session_response = service.users().sessions().list(
        userId="me",
        startTime=start_dt.isoformat() + 'Z',
        endTime=end_dt.isoformat() + 'Z'
    ).execute()

    sessions = session_response.get("session", [])
    has_sleep_session = False

    for session in sessions:
        if session.get("activityType") == 72:
            has_sleep_session = True
            s_start = session.get("startTime")
            s_end = session.get("endTime")

            if s_start and s_end:
                s_start_dt = datetime.datetime.fromisoformat(s_start[:-1])
                s_end_dt = datetime.datetime.fromisoformat(s_end[:-1])
            else:
                s_start_dt = start_dt
                s_end_dt = end_dt

            start_ns = int(s_start_dt.timestamp() * 1e9)
            end_ns = int(s_end_dt.timestamp() * 1e9)
            dataset_id = f"{start_ns}-{end_ns}"

            ds_list = service.users().dataSources().list(userId="me").execute()
            segment_ds_id = next((ds["dataStreamId"] for ds in ds_list.get("dataSource", [])
                                  if "com.google.sleep.segment" in ds.get("dataStreamId", "")), None)

            if not segment_ds_id:
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

            for point in segment_data.get("point", []):
                stage_val = point["value"][0]["intVal"]
                seg_start = datetime.datetime.fromtimestamp(int(point["startTimeNanos"]) / 1e9)
                seg_end = datetime.datetime.fromtimestamp(int(point["endTimeNanos"]) / 1e9)
                duration = (seg_end - seg_start).total_seconds()

                stage_name = sleep_stage_names.get(stage_val, f"Unknown ({stage_val})")
                log_lines.append(f"   💤 {seg_start.strftime('%H:%M')} - {seg_end.strftime('%H:%M')} → {stage_name}")

                if stage_name in stage_durations:
                    stage_durations[stage_name] += duration
                    all_segments.append((seg_start, seg_end))

            if all_segments:
                full_start = min(seg[0] for seg in all_segments)
                full_end = max(seg[1] for seg in all_segments)
                full_sleep_duration = (full_end - full_start).total_seconds()
                log_lines.append(f"   Sleep   🛌 {full_start.strftime('%H:%M')} → {full_end.strftime('%H:%M')}  |  🕓 {round(full_sleep_duration / 3600, 2)} hrs")

            for stage, seconds in stage_durations.items():
                hrs = round(seconds / 3600, 2)
                log_lines.append(f"   • {stage}: {hrs} hrs")

    if not has_sleep_session:
        log_lines.append("   ❌ No sleep data found.")

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

    # ------------------ CALORIES ------------------
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
    sessions = service.users().sessions().list(
        userId="me",
        startTime=datetime.datetime.fromtimestamp(start_time / 1000).isoformat() + 'Z',
        endTime=datetime.datetime.fromtimestamp(end_time / 1000).isoformat() + 'Z'
    ).execute()

    workout_count = 0
    workouts = []
    for session in sessions.get("session", []):
        if session.get("activityType") not in [72, 109]:
            workout_count += 1
            workouts.append(session.get("name", "Workout"))

    if workout_count > 0:
        log_lines.append(f"\t🏋️ Workout Sessions: {workout_count} ({', '.join(workouts)})")
    else:
        log_lines.append("\t🏋️ Workout Sessions: 0")

    log_lines.append("}")
    data_log("\n".join(log_lines))


def data_log(content):
    log_path = os.path.join(os.getcwd(), "Fitness log.txt")
    with open(log_path, "a", encoding="utf-8") as file:
        file.write(content + "\n\n")


main()
