"""
Clawbot: Autonomous Background Execution Daemon
Runs continuously and triggers the CEO agent to generate pipelines
based on generic news and market trends.
"""
import time
import requests
import schedule
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def fetch_latest_trend():
    # In a real scenario, this could hit a News API or Twitter trends API
    # For now, we simulate fetching an industry trend
    trends = [
        "Review the latest Instagram algorithm trends for B2B SaaS and draft a lead gen campaign with a Reel.",
        "Analyze the impact of AI in fintech and create a LinkedIn sequence targeting CTOs.",
        "Research common drawbacks of SaaS pricing models and draft an email marketing campaign for enterprise clients.",
        "Analyze how mobile app startups are acquiring users in 2026 and draft social media posts to offer premium dev services."
    ]
    # Simple deterministic rotation based on the hour
    hour = datetime.now().hour
    return trends[hour % len(trends)]

def run_clawbot_cycle():
    print(f"\n[{datetime.now().isoformat()}] 🤖 Clawbot waking up...")
    
    # 1. Fetch current trend
    goal = fetch_latest_trend()
    print(f"[Clawbot] Selected Goal: {goal}")
    
    # 2. Trigger pipeline
    try:
        print("[Clawbot] Triggering Sureflow OS pipeline...")
        response = requests.post(
            f"{API_BASE}/pipeline/run",
            json={"goal": goal},
            stream=True
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if "event" in decoded:
                        print(f"   -> {decoded[:150]}...")
            print("[Clawbot] Pipeline cycle completed successfully.")
        else:
            print(f"[Clawbot] API Error: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print("[Clawbot] Sureflow OS backend is unreachable. Is uvicorn running?")
    except Exception as e:
        print(f"[Clawbot] Error during execution: {e}")

    print(f"[{datetime.now().isoformat()}] 💤 Clawbot going back to sleep.")


if __name__ == "__main__":
    print("🚀 Clawbot Autonomous Daemon Starting...")
    
    # Run once immediately on start
    run_clawbot_cycle()
    
    # Schedule to run every hour
    schedule.every(1).hours.do(run_clawbot_cycle)
    
    print("⏳ Scheduler active. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)
