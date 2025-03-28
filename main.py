from flask import Flask, render_template, request, jsonify
import os
import random
import asyncio
from threading import Thread
from maher_zubair_baileys import Gifted_Tech, useMultiFileAuthState, makeCacheableSignalKeyStore
import pino

app = Flask(__name__)

sessions = {}

# 🔥 Pairing Code Generate करने का फंक्शन 🔥
async def generate_pair_code(number):
    session_id = f"session_{random.randint(1000, 9999)}"
    sessions[number] = session_id
    state, saveCreds = await useMultiFileAuthState(f'./temp/{session_id}')

    bot = Gifted_Tech({
        "auth": {
            "creds": state.creds,
            "keys": makeCacheableSignalKeyStore(state.keys, pino.Logger(level="fatal"))
        },
        "printQRInTerminal": False,
        "logger": pino.Logger(level="fatal"),
        "browser": ["Chrome (Linux)", "", ""]
    })

    await asyncio.sleep(2)
    code = await bot.requestPairingCode(number)
    return code

# 🔥 WhatsApp Connection का Route 🔥
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/code', methods=['GET'])
def get_code():
    number = request.args.get("number")
    if not number:
        return jsonify({"error": "Enter a valid number"}), 400
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    code = loop.run_until_complete(generate_pair_code(number))
    return jsonify({"code": code})

# 🔥 मैसेज भेजने का फंक्शन 🔥
async def send_message(session_id, target, message, is_group):
    state, saveCreds = await useMultiFileAuthState(f'./temp/{session_id}')
    
    bot = Gifted_Tech({
        "auth": {
            "creds": state.creds,
            "keys": makeCacheableSignalKeyStore(state.keys, pino.Logger(level="fatal"))
        },
        "logger": pino.Logger(level="fatal"),
        "browser": ["Chrome (Linux)", "", ""]
    })

    await asyncio.sleep(2)

    if is_group:
        await bot.sendMessage(target, {"text": message})
    else:
        await bot.sendMessage(f"{target}@s.whatsapp.net", {"text": message})

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    number = data.get("number")
    target = data.get("target")
    message = data.get("message")
    is_group = data.get("is_group", False)

    if not number or not target or not message:
        return jsonify({"error": "Invalid input"}), 400

    session_id = sessions.get(number)
    if not session_id:
        return jsonify({"error": "Session not found"}), 400

    thread = Thread(target=lambda: asyncio.run(send_message(session_id, target, message, is_group)))
    thread.start()

    return jsonify({"status": "Message Sent!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)