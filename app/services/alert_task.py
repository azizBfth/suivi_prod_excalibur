import requests
import schedule
import time

# Global session to keep cookies and headers
session = requests.Session()

def login():
    try:
        login_url = "http://localhost/auth/login-json"  # ⚠️ mets /api/ si ton backend est sous /api
        credentials = {
            "username": "admin",
            "password": "HbB6yq+R+U"
        }

        response = session.post(login_url, json=credentials)

        print(f"🔎 Status: {response.status_code}")
        print(f"🔎 Raw response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if "data" in data and "access_token" in data["data"]:
                token = data["data"]["access_token"]
                token_type = data["data"].get("token_type", "bearer")
                session.headers.update({"Authorization": f"{token_type.capitalize()} {token}"})
                print("✅ Login successful, token set")
            else:
                print("⚠️ Login response did not contain access_token")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error during login: {e}")

def check_alerts():
    try:
        # Step 1: POST request to check alerts
        post_response = session.post("http://localhost/api/alerts/check")
        print(f"POST response: {post_response.status_code} - {post_response.text}")

        # Step 2: GET request to retrieve alerts
        get_response = session.get("http://localhost/api/alerts")
        print(f"GET response: {get_response.status_code}")

        try:
            alerts = get_response.json()
            print(f"Alerts: {alerts}")
        except ValueError:
            print("Error: GET response is not valid JSON")
            print(f"Response text: {get_response.text}")

    except Exception as e:
        print(f"Error while checking alerts: {e}")


# Step 0: Login first
login()

# Schedule the task every day at 07:00
schedule.every().day.at("08:24").do(check_alerts)

print("Scheduler started. Waiting for 07:00...")

while True:
    schedule.run_pending()
    time.sleep(1)  # check every second
