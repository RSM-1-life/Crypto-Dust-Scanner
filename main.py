import os
import json
import websocket
import telebot
from flask import Flask
import threading

# Render-এর জন্য ওয়েব সার্ভার অংশ
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# আপনার বোট টোকেন ও আইডি
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635"
bot = telebot.TeleBot(TOKEN)

SEGMENTS = ["1", "2", "1", "5", "1", "10", "1", "2", "1", "5", "1", "Cash Hunt", "1", "2", "1", "5", "1", "10", "1", "2", "1", "Pachinko", "1", "2", "1", "5", "1", "10", "1", "2", "1", "Coin Flip", "1", "2", "1", "5", "1", "10", "1", "2", "1", "Crazy Time", "1", "2", "1", "5", "1", "10", "1", "2", "1", "Pachinko", "1", "5"]

class EvolutionPredictor:
    def __init__(self):
        self.ws_url = "wss://fra1-mdp-e18.egcvi.com/dc3_ct_hi"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            # মাল্টিপ্লায়ার চেক
            if "topSlotLog" in str(data):
                res = data.get('topSlotLog', {})
                bot.send_message(CHAT_ID, f"🎰 মাল্টিপ্লায়ার: {res.get('target')} ({res.get('value')}x)")
            # স্টপ অ্যাঙ্গেল চেক
            if "stopAngle" in str(data):
                angle = data.get('stopAngle')
                bot.send_message(CHAT_ID, f"🎯 চাকা থামার ডিগ্রি: {angle}°")
        except:
            pass

    def run(self):
        ws = websocket.WebSocketApp(self.ws_url, on_message=self.on_message)
        ws.run_forever()

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    predictor = EvolutionPredictor()
    predictor.run()
