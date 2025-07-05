# 🩺 Google Fit Daily Logger (Python Script)

A simple but powerful Python script that pulls your **Google Fit data from the previous day** and logs it to a readable `.txt` file — including:

- 💗 Heart Rate (5-min interval + average)
- 💤 Sleep Stages (Light, Deep, REM)
- 🚶 Step Count
- ⚡ Calories Burned
- 💓 Heart Points
- 🏋️ Workout Sessions

Runs automatically every day. Ideal for smartwatch users who want **desktop access** to health data.

---

## 🚀 How to Use

### ✅ 1. Enable Google Fit API

1. Visit [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. **Create a new project**
3. Go to **APIs & Services → Library**
4. Search for **Fitness API**, then **Enable it**
5. Go to **APIs & Services → OAuth consent screen**
   - Choose **External**
   - Fill app name and user support email
   - Add scopes:
     ```
     https://www.googleapis.com/auth/fitness.activity.read
     https://www.googleapis.com/auth/fitness.heart_rate.read
     https://www.googleapis.com/auth/fitness.sleep.read
     https://www.googleapis.com/auth/fitness.location.read
     https://www.googleapis.com/auth/fitness.body.read
     ```
6. Go to **Credentials → Create Credentials → OAuth Client ID**
   - Select **Desktop App**
   - Download the `client_secret_XXXX.json`
   - Rename it to: `client_secret.json`
   - Put it in the same folder as the script

---

### 💾 2. Clone this Repository

```bash
git clone https://github.com/oolalabravo/google-fit-daily-logger.git
cd google-fit-daily-logger
