import json
import time
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from better_profanity import profanity
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app)
load_dotenv()

messages = []
password = os.environ.get('PASSWORD')
presence = {}  # Store presence information

def load_messages():
    global messages
    try:
        with open('messages.json', 'r') as file:
            messages = json.load(file)
    except FileNotFoundError:
        messages = []

def save_messages():
    with open('messages.json', 'w') as file:
        json.dump(messages, file, indent=4)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    return jsonify(messages[-50:])

@app.route('/api/messages', methods=['POST'])
def add_message():
    name = request.json['name'][:20]  # Limit name to 20 characters
    if profanity.contains_profanity(name):
        return jsonify({'error': 'Name contains profanity.'}), 400

    content = request.json['content']
    timestamp = int(time.time())
    rgb_color = request.json.get('color', [239, 0, 10])

    if len(content) <= 1500:
        message = {'id': len(messages), 'name': name, 'content': content, 'timestamp': timestamp, 'color': rgb_color}
        messages.append(message)
        save_messages()
        return jsonify({'message': 'Message sent successfully.'}), 201
    else:
        return jsonify({'error': 'Message content exceeds the maximum limit of 1500 characters.'}), 400

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    password_input = request.args.get('password')
    if password_input == password:
        for message in messages:
            if message['id'] == message_id:
                messages.remove(message)
                save_messages()
                return jsonify({'message': 'Message deleted successfully.'}), 200
        return jsonify({'error': 'Message not found.'}), 404
    else:
        return jsonify({'error': 'Unauthorized access. Please check your password and try again.'}), 401

@app.route('/api/presence', methods=['POST'])
def update_presence():
    username = request.json.get('username')
    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    presence[username] = datetime.now()
    return jsonify({'message': 'Presence updated successfully.'}), 200

@app.route('/api/online-users', methods=['GET'])
def get_online_users():
    now = datetime.now()
    online_users = [user for user, last_seen in presence.items() if now - last_seen < timedelta(seconds=30)]
    return jsonify(online_users), 200

if __name__ == '__main__':
    profanity.load_censor_words()
    load_messages()
    socketio.run(app, allow_unsafe_werkzeug=True, port=5023)