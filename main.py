import os
import json
import websocket
import telebot
from flask import Flask
import threading
import time

# Render-এর জন্য ওয়েব সার্ভার
app = Flask('')
@app.route('/')
def home(): return "Bot is Scanning Data..."

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# আপনার বোট ক্রেডেনশিয়াল
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635"
bot = telebot.TeleBot(TOKEN)

class SmartPredictor:
    def __init__(self):
        # গেম সার্ভার লিঙ্ক (এটি সমস্যা করলে অটো-রিসেট হবে)
        self.ws_url = "wss://fra1-mdp-e18.egcvi.com/dc3_ct_hi"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            
            # ১. মাল্টিপ্লায়ার (গুণ) বিশ্লেষণ (Top Slot Data)
            if "topSlotLog" in str(data):
                slot = data.get('topSlotLog', {})
                target = slot.get('target', 'N/A')
                value = slot.get('value', 1)
                bot.send_message(CHAT_ID, f"🎰 *মাল্টিপ্লায়ার আপডেট:*\nটার্গেট: {target}\nগুণ: {value}x", parse_mode="Markdown")

            # ২. চাকা থামার অ্যাঙ্গেল ও সংখ্যা নির্বাচন
            if "stopAngle" in str(data):
                angle = data.get('stopAngle')
                # এখানে আপনার গাণিতিক লজিক অনুযায়ী রেজাল্ট ক্যালকুলেট হবে
                bot.send_message(CHAT_ID, f"🎯 *ফলাফল সংকেত:*\nচাকা থামছে: {angle}° এ।", parse_mode="Markdown")

        except Exception as e:
            print(f"Error parsing data: {e}")

    def on_error(self, ws, error):
        print(f"Server Error: {error}")

    def on_close(self, ws, *args):
        print("### কানেকশন বিচ্ছিন্ন! ৫ সেকেন্ড পর নতুন আইডি/কানেকশন খুঁজছে... ###")
        time.sleep(5)
        self.run() # অটোমেটিক রিস্টার্ট লজিক

    def run(self):
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.run_forever()

if __name__ == "__main__":
    # ওয়েব সার্ভার ও বোট একসাথে চালানো
    threading.Thread(target=run_web).start()
    bot.send_message(CHAT_ID, "🚀 স্মার্ট ডাটা স্ক্যানার চালু হয়েছে। গেমের তথ্য বিশ্লেষণ করা হচ্ছে...")
    predictor = SmartPredictor()
    predictor.run()
