import os
import time
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

# Telegram Bot Setup
BOT_TOKEN = "7785620184:AAGRe49shvUuulN2-7gHQ4k3rzxkTiVYEBw"
CHAT_ID = "876179160"

CHECK_INTERVAL = 10  # seconds
JOB_SITE_URL = "https://www.jobsatamazon.co.uk/app#/jobSearch"
SEEN_JOBS_FILE = "seen_jobs.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("✅ Telegram alert sent")
    else:
        print("❌ Failed to send Telegram message:", response.text)

def get_job_cards():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(JOB_SITE_URL)
        page.wait_for_timeout(5000)

        job_cards = page.query_selector_all('[data-test-id="JobCard"]')
        jobs = []
        for card in job_cards:
            title = card.query_selector("strong") or ""
            type_el = card.query_selector("text=Type:")
            duration_el = card.query_selector("text=Duration:")
            pay_el = card.query_selector("text=Pay rate:")
            location_el = card.query_selector("text=Liverpool")

            job = {
                "title": title.inner_text().strip() if title else "N/A",
                "type": type_el.inner_text().strip() if type_el else "N/A",
                "duration": duration_el.inner_text().strip() if duration_el else "N/A",
                "pay": pay_el.inner_text().strip() if pay_el else "N/A",
                "location": location_el.inner_text().strip() if location_el else "N/A"
            }

            job_text = f"{job['title']}\n{job['location']}"
            jobs.append(job_text)

        browser.close()
        return jobs

def load_seen_jobs():
    if not os.path.exists(SEEN_JOBS_FILE):
        return []
    with open(SEEN_JOBS_FILE, "r") as f:
        return f.read().splitlines()

def save_seen_jobs(jobs):
    with open(SEEN_JOBS_FILE, "w") as f:
        f.write("\n".join(jobs))

def main():
    print("Starting job monitor...")
    seen_jobs = load_seen_jobs()

    while True:
        try:
            now = datetime.now()
            current_hour = now.hour

            if 10 <= current_hour < 20:
                print(f"Checking for jobs at {now.strftime('%H:%M:%S')}...")

                current_jobs = get_job_cards()
                new_jobs = [job for job in current_jobs if job not in seen_jobs]

                if new_jobs:
                    print(f"Found {len(new_jobs)} new job(s)")
                    for job in new_jobs:
                        send_telegram_message(f"📢 New Job Posted:\n\n{job}")
                    seen_jobs.extend(new_jobs)
                    save_seen_jobs(seen_jobs)
                else:
                    print("No new jobs.")
                    send_telegram_message("ℹ️ No new jobs found.")
            else:
                print("⏰ Outside checking hours (10 AM to 8 PM).")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
