import os
import json
import websocket
import telebot
from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get('PORT', 10000)) # পোর্ট ১০০০০ ব্যবহার করা হয়েছে
    app.run(host='0.0.0.0', port=port)

# এখানে আপনার নিজের টোকেন এবং আইডি দিন
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635" # @userinfobot থেকে পাওয়া আপনার নিজের আইডি এখানে বসান
bot = telebot.TeleBot(TOKEN)

class EvolutionPredictor:
    def __init__(self):
        self.ws_url = "wss://fra1-mdp-e18.egcvi.com/dc3_ct_hi"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if "stopAngle" in str(data):
                angle = data.get('stopAngle')
                bot.send_message(CHAT_ID, f"🎯 চাকা থামার পূর্বাভাস: {angle}°")
        except:
            pass

    def run(self):
        ws = websocket.WebSocketApp(self.ws_url, on_message=self.on_message)
        ws.run_forever()

if __name__ == "__main__":
    # বোট চালু হওয়ার সাথে সাথে আপনাকে একটি মেসেজ পাঠাবে
    try:
        bot.send_message(CHAT_ID, "✅ বোট সফলভাবে কানেক্ট হয়েছে এবং সার্ভারে চালু আছে!")
    except:
        print("Chat ID ভুল হতে পারে")

    threading.Thread(target=run_web).start()
    predictor = EvolutionPredictor()
    predictor.run()
