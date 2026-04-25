import os
import json
import websocket
import telebot
import threading

# আপনার দেওয়া তথ্যগুলো এনভায়রনমেন্ট ভ্যারিয়েবল হিসেবে থাকবে
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635"
bot = telebot.TeleBot(TOKEN)

# চাকার সেগমেন্ট ম্যাপ (৫.৫৬ ডিগ্রী প্রতি ঘর - আদর্শ Crazy Time মডেল)
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
        self.ws_url = "wss://fra1-mdp-e18.egcvi.com/dc3_ct_hi" # আপনার স্ক্রিনশট থেকে পাওয়া
        self.packet_count = 0

    def calculate_result(self, angle):
        try:
            # ৩৬০ ডিগ্রীকে ৫৪ দিয়ে ভাগ করে ঘরের অবস্থান বের করা
            idx = int((angle % 360) / (360 / 54))
            return SEGMENTS[idx]
        except:
            return "Unknown"

    def on_message(self, ws, message):
        data = json.loads(message)
        self.packet_count += 1

        # ক) প্রথম ৮টি ফাইলে মাল্টিপ্লায়ার স্লট শনাক্তকরণ
        if self.packet_count <= 8:
            if "topSlotLog" in str(data):
                res = data.get('topSlotLog', {})
                bot.send_message(CHAT_ID, f"🎰 মাল্টিপ্লায়ার অ্যালার্ট!\nটার্গেট: {res.get('target')}\nগুণ: {res.get('value')}x")

        # খ) স্টপ অ্যাঙ্গেল শনাক্তকরণ (আগাম পূর্বাভাস)
        if "stopAngle" in str(data):
            angle = data.get('stopAngle')
            prediction = self.calculate_result(angle)
            bot.send_message(CHAT_ID, f"🎯 চাকা থামার পূর্বাভাস:\nডিগ্রী: {angle}°\nসম্ভাব্য ফলাফল: {prediction}")
            self.packet_count = 0 # রাউন্ড শেষে কাউন্টার রিসেট

    def run(self):
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_open=lambda ws: print("Connected to Evolution Stream...")
        )
        ws.run_forever()

if __name__ == "__main__":
    predictor = EvolutionPredictor()
    predictor.run()
