import os
import json
import websocket
import telebot
from flask import Flask
import threading

# Render-এর জন্য ছোট একটি ওয়েব সার্ভার সেটআপ (যাতে বোটটি বন্ধ না হয়)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    # Render স্বয়ংক্রিয়ভাবে একটি পোর্ট দেয়, সেটি ব্যবহার করা
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# আপনার দেওয়া বোট টোকেন এবং চ্যাট আইডি
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635"
bot = telebot.TeleBot(TOKEN)

# চাকার ৫৪টি সেগমেন্টের ম্যাপ (Crazy Time standard map)
SEGMENTS = [
    "1", "2", "1", "5", "1", "10", "1", "2", "1", "5", 
    "1", "Cash Hunt", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Pachinko", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Coin Flip", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Crazy Time", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Pachinko", "1", "5"
]

class EvolutionPredictor:
    def __init__(self):
        # এভোল্যুশন গেমিংয়ের ডাটা স্ট্রিম ইউআরএল
        self.ws_url = "wss://fra1-mdp-e18.egcvi.com/dc3_ct_hi"
        self.packet_count = 0

    def calculate_result(self, angle):
        try:
            # ৩৬০ ডিগ্রীকে ৫৪ ভাগে ভাগ করে ফলাফল বের করা
            idx = int((angle % 360) / (360 / 54))
            return SEGMENTS[idx]
        except:
            return "Unknown"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.packet_count += 1

            # ১. মাল্টিপ্লায়ার স্লট চেক করা (প্রথম ৮টি ডাটা প্যাকেটে থাকে)
            if "topSlotLog" in str(data):
                res = data.get('topSlotLog', {})
                msg = f"🎰 *মাল্টিপ্লায়ার অ্যালার্ট!*\nটার্গেট: {res.get('target')}\nগুণ: {res.get('value')}x"
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")

            # ২. স্টপ অ্যাঙ্গেল বা চূড়ান্ত ফলাফল পূর্বাভাস
            if "stopAngle" in str(data):
                angle = data.get('stopAngle')
                prediction = self.calculate_result(angle)
                msg = f"🎯 *চাকা থামার পূর্বাভাস:*\nডিগ্রী: {angle}°\nফলাফল: *{prediction}*"
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                self.packet_count = 0 # কাউন্টার রিসেট

        except Exception as e:
            print(f"Error processing message: {e}")

    def run(self):
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_open=lambda ws: print("Connected to Game Server..."),
            on_error=lambda ws, err: print(f"Connection Error: {err}")
        )
        ws.run_forever()

if __name__ == "__main__":
    # ১. ওয়েব সার্ভারকে আলাদা থ্রেডে চালু করা (যাতে Render খুশি থাকে)
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    # ২. মূল প্রেডিকশন ইঞ্জিন চালু করা
    predictor = EvolutionPredictor()
    predictor.run()
