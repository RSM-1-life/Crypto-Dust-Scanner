import os
import json
import websocket
import telebot
from flask import Flask
import threading
import time

# --- কনফিগারেশন ---
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635"
bot = telebot.TeleBot(TOKEN)

app = Flask('')
@app.route('/')
def home(): return "Scanner is Active and Analyzing Data..."

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- ক্রেজি টাইম হুইল ম্যাপ (৫৪টি সেগমেন্ট) ---
# এটি আপনার stopAngle কে সরাসরি সংখ্যায় রূপান্তর করবে
SEGMENTS = [
    "1", "2", "1", "5", "1", "10", "1", "2", "1", "5", 
    "1", "Cash Hunt", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Pachinko", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Coin Flip", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Crazy Time", "1", "2", "1", "5", "1", "10", "1", "2",
    "1", "Pachinko", "1", "5"
]

class MasterPredictor:
    def __init__(self):
        self.ws_url = "wss://fra1-mdp-e18.egcvi.com/dc3_ct_hi"
        self.packet_buffer = [] # ৮টি প্যাকেট জমানোর জন্য

    def calculate_result(self, angle):
        try:
            # ৩৬০ ডিগ্রিকে ৫৪ ভাগে ভাগ করে সঠিক সংখ্যা বের করা
            idx = int((angle % 360) / (360 / 54))
            return SEGMENTS[idx]
        except:
            return "Unknown"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.packet_buffer.append(data)
            
            # ৮টি প্যাকেট হয়ে গেলে বাফার ক্লিন করা (যাতে মেমোরি ফুল না হয়)
            if len(self.packet_buffer) > 20:
                self.packet_buffer.pop(0)

            # ১. মাল্টিপ্লায়ার (Top Slot) ডিটেকশন
            if "topSlotLog" in str(data):
                slot = data.get('topSlotLog', {})
                msg = (f"🎰 *TOP SLOT ALERT!*\n"
                       f"━━━━━━━━━━━━━━━\n"
                       f"টার্গেট: {slot.get('target')}\n"
                       f"গুণফল: {slot.get('value')}x")
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")

            # ২. স্টপ এঙ্গেল থেকে রেজাল্ট প্রেডিকশন
            if "stopAngle" in str(data):
                angle = data.get('stopAngle')
                prediction = self.calculate_result(angle)
                
                msg = (f"🎯 *PREDICTION FOUND!*\n"
                       f"━━━━━━━━━━━━━━━\n"
                       f"ডিগ্রি: {angle}°\n"
                       f"ফলাফল হতে পারে: *{prediction}*\n"
                       f"প্যাকেট স্ট্যাটাস: Analyzed ✅")
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")

        except Exception as e:
            print(f"Analysis Error: {e}")

    def on_open(self, ws):
        print("Connected to Game Stream...")
        bot.send_message(CHAT_ID, "🔄 সার্ভারের সাথে কানেকশন তৈরি হয়েছে। ডাটা স্ক্যান করা হচ্ছে...")

    def on_error(self, ws, error):
        print(f"Stream Error: {error}")

    def on_close(self, ws, *args):
        print("Connection Lost. Reconnecting in 5s...")
        time.sleep(5)
        self.connect()

    def connect(self):
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws.run_forever()

if __name__ == "__main__":
    # ওয়েব সার্ভার ব্যাকগ্রাউন্ডে চালানো
    threading.Thread(target=run_web, daemon=True).start()
    
    # বোট চালু করা
    predictor = MasterPredictor()
    predictor.connect()
