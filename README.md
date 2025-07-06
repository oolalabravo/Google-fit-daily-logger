![Python](https://img.shields.io/badge/python-3.7+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# 🩺 PyFit — Google Fit Daily Email Logger

**PyFit** is a smart, automated Python script that:

* 🧠 Pulls **your previous day's Google Fit data**
* 📂 Saves it to a readable `.txt` log
* 📧 Sends that log to your inbox — *automatically*

Perfect for smartwatch users who want **easy daily health logs via email**.

---

## 📊 Features

* 💗 **Heart Rate** (5-min intervals + average)
* 💤 **Sleep Analysis** (Stages: Light, Deep, REM, Awake)
* 🚶 **Step Count**
* ⚡ **Calories Burned**
* 💓 **Heart Points**
* 🏋️ **Workout Sessions**
* 📎 **Auto Email Delivery** (via Gmail API)

---

## 🚀 Setup Guide

### ✅ 1. Enable APIs in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a **new project**
3. Go to **APIs & Services → Library**
4. Enable the following APIs:

   * Google Fit API
   * Gmail API
5. Go to **OAuth Consent Screen**

   * Choose **External**
   * Fill app name & email
   * Add these **scopes**:

```
https://www.googleapis.com/auth/fitness.activity.read  
https://www.googleapis.com/auth/fitness.heart_rate.read  
https://www.googleapis.com/auth/fitness.sleep.read  
https://www.googleapis.com/auth/fitness.location.read  
https://www.googleapis.com/auth/fitness.body.read  
https://www.googleapis.com/auth/gmail.send  
```

6. Go to **Credentials → Create Credentials → OAuth Client ID**

   * Choose **Desktop App**
   * Download the JSON and rename it to `client_secret.json`
   * Place it in the same folder as `main.py`

---

### 🔐 2. First-Time Authorization

When you run the script:

* It will open a browser window to authenticate **Account A** (for Google Fit)
* Then again for **Account B** (for Gmail Send)
* Two token files (`token.json`, `token2.json`) will be generated and reused

> 🔁 This step only happens once per account.

---

### ⚙️ 3. Customize Settings

Open `main.py` and update these fields:

```python
SENDER = "your_sender_email@gmail.com"
TO = "your_recipient_email@gmail.com"
```

You can also rename the log file or set its path:

```python
LOG_FILE_PATH = BASE_DIR / "Fitness log.txt"
```

---

## ⏰ Automate Daily Logging

### 🪟 Windows: Use Task Scheduler

1. Press `Win + S` → **Task Scheduler**
2. **Create Basic Task**
3. Trigger: Daily → Time: e.g., `08:00 AM`
4. Action: `Start a program`
5. Program:

   ```
   pythonw.exe
   ```
6. Add arguments:

   ```
   main.py
   ```
7. Start in:

   ```
   Full path to script folder (e.g., C:\Users\You\Documents\pyfit)
   ```

✅ Now PyFit will run silently every day and send your log ✉️

---

### 🐧 Linux: Use crontab

```bash
crontab -e
```

Add this line to run daily at noon:

```bash
0 12 * * * /usr/bin/python3 /full/path/to/main.py
```

---

## 💾 File Structure

```
📁 pyfit/
├── main.py
├── client_secret.json
├── token.json
├── token2.json
├── Fitness log.txt
├── requirements.txt
└── README.md
```

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/pyfit.git
cd pyfit
pip install -r requirements.txt
python main.py
```

---

## 📜 License

This project is licensed under the **MIT License**.
Feel free to fork and improve it ✨

---

Let me know if you want a `requirements.txt` or GitHub Actions support too!
