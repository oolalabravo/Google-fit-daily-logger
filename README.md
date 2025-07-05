![Python](https://img.shields.io/badge/python-3.7+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# 🩺 Google Fit Daily Email Logger (Python Script)

A simple but powerful Python script that:

- 🧠 Pulls your **Google Fit data from yesterday**
- 📂 Saves it into a clean `.txt` log file
- 📧 Emails that file automatically to your inbox!

Perfect for smartwatch users who want **desktop + email access** to their fitness and health data.

---

## 📊 Features

- 💗 Heart Rate (5-min intervals + daily average)
- 💤 Sleep Stages (Light, Deep, REM)
- 🚶 Step Count
- ⚡ Calories Burned
- 💓 Heart Points
- 🏋️ Workout Sessions
- 📎 Automatically emailed as an attachment

---

## 🚀 How to Use

### ✅ 1. Enable Google Fit API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create a new project**
3. Navigate to **APIs & Services → Library**
4. Search for **Fitness API** → Enable it
5. Go to **OAuth Consent Screen**
   - Choose **External**
   - Fill app name and email
   - Add these scopes:
     ```
     https://www.googleapis.com/auth/fitness.activity.read
     https://www.googleapis.com/auth/fitness.heart_rate.read
     https://www.googleapis.com/auth/fitness.sleep.read
     https://www.googleapis.com/auth/fitness.location.read
     https://www.googleapis.com/auth/fitness.body.read
     https://www.googleapis.com/auth/gmail.send
     ```
6. Go to **Credentials → Create Credentials → OAuth Client ID**
   - Choose **Desktop App**
   - Download the file `client_secret_XXXX.json`
   - Rename it to `client_secret.json`
   - Put it in the same folder as your script


---


### ⏰ 7. Automate Daily Logging (Optional)

Want to log your health data **every day without opening the script manually?**  
Follow the guide for your OS below:

---

### 🪟 Windows: Use Task Scheduler

1. Press `Win + S` → Search for **Task Scheduler** → Open it  
2. In the right panel, click **“Create Basic Task”**
3. Name it `Google Fit Logger` and click **Next**
4. **Trigger** → Select `Daily` → set time (e.g., `12:00 PM`)
5. **Action** → Choose `Start a Program`
6. In **Program/script**, write:
7. In **Add arguments**, write:
8. In **Start in**, write the full path to your script folder  
*(e.g., `C:\Users\YourName\Documents\google-fit-daily-logger`)*  
9. Click **Finish**

✅ Your logger will now run automatically every day at 12 PM!

---

### 🐧 Linux: Use crontab

1. Open terminal  
2. Run the command:

```bash
crontab -e
0 12 * * * /usr/bin/python3 /full/path/to/main.py



### 💾  Clone this Repository

```bash
git clone https://github.com/oolalabravo/google-fit-daily-logger.git
cd google-fit-daily-logger

## File structure should be
├── main.py
├── requirements.txt
├── token.json
├── README.md
└── seacrets.json

