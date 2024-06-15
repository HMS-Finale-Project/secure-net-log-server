import re
import json
import subprocess
import os
import time
import datetime
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

SESSIONS_FILE = 'sessions.txt'
LAST_MODIFIED = 0
LAST_JSON = None
LOGS_DIR = os.getcwd()  # Current directory

# Function to convert time string to ISO format
def convert_time(time_str):
    time_format = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.strptime(time_str, time_format).isoformat()

# Function to execute Linux command and capture output
def execute_command(command):
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode('utf-8')

# Read sessions.txt file
def read_sessions():
    global LAST_MODIFIED, LAST_JSON
    
    # Execute command to update sessions.txt
    execute_command("sshlog sessions > " + SESSIONS_FILE)
    
    # Check last modified time of sessions.txt
    modified_time = os.path.getmtime(SESSIONS_FILE)
    if modified_time > LAST_MODIFIED:
        LAST_MODIFIED = modified_time
        with open(SESSIONS_FILE, 'r') as file:
            lines = file.readlines()
        
        # Initialize list to store session data
        sessions = []

        # Skip the header line
        for line in lines[1:]:
            # Split line into fields using whitespace
            fields = re.split(r'\s{2,}', line.strip())
            
            # Extract fields
            user = fields[0]
            last_activity = fields[1]
            last_command = fields[2]
            session_start = convert_time(fields[3])
            client_ip = fields[4].split(':')[0]
            tty = fields[5]

            # Create session dictionary
            session = {
                'User': user,
                'Last Activity': last_activity,
                'Last Command': last_command,
                'Session Start': session_start,
                'Client IP': client_ip,
                'TTY': tty
            }

            # Append session to sessions list
            sessions.append(session)

        LAST_JSON = jsonify(sessions)
        return LAST_JSON
    else:
        # No update, return existing JSON
        if LAST_JSON:
            return LAST_JSON
        else:
            return "No data"

# Define endpoint to serve JSON logs
@app.route('/active_sessions', methods=['GET'])
def get_logs():
    return read_sessions()

# Define endpoint to list log files
@app.route('/list_logs', methods=['GET'])
def list_logs():
    log_files = [file for file in os.listdir(LOGS_DIR) if file.endswith('.log')]
    return jsonify(log_files)

# Define endpoint to get log file contents
@app.route('/get_log', methods=['GET'])
def get_log():
    file_name = request.args.get('file')
    try:
        return send_from_directory(LOGS_DIR, file_name)
    except FileNotFoundError:
        return 'File not found', 404
    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
