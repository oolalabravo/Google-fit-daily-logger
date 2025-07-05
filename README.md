# Google Fit Daily Logger 🩺📊

This Python script fetches and logs your **previous day’s** health data from **Google Fit**, including:

- 💗 Heart Rate (5-min intervals + average)
- 💤 Sleep stages and durations
- 🚶 Step count
- ⚡ Energy expended (kcal)
- 🏋️ Workout sessions
- 💓 Heart points

## Features

- Automated OAuth2 authentication
- Pulls from multiple Google Fit data streams
- Saves readable daily logs in `.txt` format
- Can be scheduled to run every day at noon

- ## Example Output

- 2025-07-04 {
🕓 01:23:00 - 01:28:00 → 💗 61.56 bpm
📊 Avg Heart Rate: 83.26 bpm
🚶 Step Count: 993 steps
💤 02:00 - 02:24 → Light sleep
• Light sleep: 0.4 hrs
⚡ Energy Expended: 1298.69 kcal
🏋️ Workout Sessions: 0
}
