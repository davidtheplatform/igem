import json
import time
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from better_profanity import profanity

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app)
load_dotenv()

messages = []
password = os.environ.get('PASSWORD')

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
        print(password_input)
        return jsonify({'error': 'Unauthorized access. If you entered the password correctly Google AI suggests jumping off a bridge.'}), 401
if __name__ == '__main__':
    profanity.load_censor_words()
    load_messages()
    socketio.run(app, allow_unsafe_werkzeug=True, port=5023)
