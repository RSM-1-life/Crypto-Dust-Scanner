import os
import json
import websocket
import telebot
from flask import Flask
import threading
import time
import logging
from datetime import datetime

# ========== কনফিগারেশন ==========
TOKEN = "8688875247:AAHm2ywUUTKCiHa2aSunXRaI4U1h549SZ6A"
CHAT_ID = "6075712635"
bot = telebot.TeleBot(TOKEN)

# Flask অ্যাপ (হেলথ চেকের জন্য)
app = Flask('')
@app.route('/')
def home(): 
    return "✅ Crazy Time Signal Bot is Running..."

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# লগিং সেটআপ (ডিবাগের জন্য)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== ডিফল্ট সেগমেন্ট (যদি real-time না পাওয়া যায়) ==========
DEFAULT_SEGMENTS = [
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
        self.current_segments = None          # Real-time segments from server
        self.last_spin_id = None              # Duplicate check
        self.last_alert_time = 0
        self.min_interval = 2                 # Minimum seconds between alerts (avoid spam)
        self.ws = None
        self.running = True

    def get_segments(self):
        """Returns current dynamic segments or default if not available"""
        return self.current_segments if self.current_segments else DEFAULT_SEGMENTS

    def calculate_result(self, angle):
        """Convert stopAngle to segment value using current segment list"""
        try:
            segments = self.get_segments()
            # 54 segments total
            idx = int((angle % 360) / (360 / 54))
            idx = min(idx, 53)  # safety
            return segments[idx]
        except Exception as e:
            logger.error(f"Angle calculation error: {e}")
            return "Unknown"

    def send_alert(self, title, details, parse_mode="Markdown"):
        """Send message to Telegram with rate limiting"""
        now = time.time()
        if now - self.last_alert_time < self.min_interval:
            time.sleep(0.5)  # small delay to avoid flooding
        self.last_alert_time = now
        
        msg = f"🎯 *{title}*\n━━━━━━━━━━━━━━━\n{details}"
        try:
            bot.send_message(CHAT_ID, msg, parse_mode=parse_mode)
            logger.info(f"Alert sent: {title}")
        except Exception as e:
            logger.error(f"Telegram send error: {e}")

    def on_message(self, ws, message):
        try:
            # লগে কাঁচা ডেটা রাখুন (প্রয়োজনে কমেন্ট আউট করুন)
            # with open("debug.log", "a") as f:
            #     f.write(f"{datetime.now()}: {message}\n")
            
            data = json.loads(message)
            
            # 1. Real-time wheel segments update (if available)
            if "wheelSegments" in data:
                self.current_segments = data["wheelSegments"]
                logger.info(f"✅ Dynamic segments loaded: {len(self.current_segments)} items")
                self.send_alert("হুইল সেগমেন্ট আপডেট!", 
                                f"সার্ভার থেকে {len(self.current_segments)}টি সেগমেন্ট সফলভাবে সংগ্রহ করা হয়েছে।\nপ্রেডিকশন এখন আরও নির্ভুল হবে।")
                return
            
            # 2. Top Slot / Multiplier Alert
            if "topSlotLog" in str(data):
                slot = data.get('topSlotLog', {})
                if slot:
                    target = slot.get('target', 'Unknown')
                    value = slot.get('value', 'N/A')
                    details = f"🎰 *টপ স্লট মাল্টিপ্লায়ার*\nটার্গেট: `{target}`\nগুণফল: *{value}x*"
                    self.send_alert("মাল্টিপ্লায়ার ডিটেক্টেড!", details)
                    return
            
            # Alternative bonus game detection (many streams use "bonusGame")
            if "bonusGame" in data:
                bonus = data["bonusGame"]
                details = f"🎁 *বোনাস গেম*\nনাম: `{bonus.get('name','?')}`\nমাল্টিপ্লায়ার: {bonus.get('multiplier',1)}x"
                self.send_alert("বোনাস রাউন্ড!", details)
                return
            
            # 3. Stop Angle Prediction (main spin result)
            if "stopAngle" in data:
                angle = data.get('stopAngle')
                # Duplicate check using spinId or timestamp
                spin_id = data.get('spinId') or data.get('roundId') or str(angle) + str(data.get('timestamp',''))
                if spin_id == self.last_spin_id:
                    return  # same spin, ignore
                self.last_spin_id = spin_id
                
                prediction = self.calculate_result(angle)
                details = (f"📐 *স্টপ অ্যাঙ্গেল:* `{angle}°`\n"
                           f"🔮 *প্রেডিকটেড রেজাল্ট:* **{prediction}**\n"
                           f"🕒 *টাইম:* {datetime.now().strftime('%H:%M:%S')}")
                self.send_alert("নতুন স্পিন প্রেডিকশন!", details)
                return
            
            # 4. কোনো সাধারণ ফলাফল (ক্ষেত্রবিশেষে)
            if "result" in data:
                res = data["result"]
                details = f"ফলাফল: `{res}`\nসম্পূর্ণ ডেটা: {json.dumps(data, indent=2)[:200]}"
                self.send_alert("স্পিন রেজাল্ট লগ!", details)
                return
                
        except json.JSONDecodeError:
            logger.warning("Non-JSON message received")
        except Exception as e:
            logger.error(f"on_message error: {e}")

    def on_open(self, ws):
        logger.info("✅ WebSocket connected to Crazy Time stream")
        bot.send_message(CHAT_ID, "🟢 *সিগন্যাল বট চালু হয়েছে!*\nওয়েবসকেট সংযোগ সফল। রিয়েল-টাইম প্রেডিকশন আসতে থাকবে।", parse_mode="Markdown")

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        bot.send_message(CHAT_ID, f"⚠️ ওয়েবসকেট এরর: `{str(error)[:100]}`\nপুনঃসংযোগের চেষ্টা চলছে...", parse_mode="Markdown")

    def on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"Connection closed: {close_status_code} - {close_msg}")
        bot.send_message(CHAT_ID, "🔌 সংযোগ বিচ্ছিন্ন হয়েছে। ৫ সেকেন্ড পর পুনরায় চেষ্টা করছি...")
        time.sleep(5)
        if self.running:
            self.connect()

    def connect(self):
        """Establish WebSocket connection with auto-reconnect"""
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                logger.error(f"Connection attempt failed: {e}")
                time.sleep(10)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

# ========== টেলিগ্রাম কমান্ড হ্যান্ডলার ==========
predictor = None  # will be set after bot starts

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
                 "🤖 *Crazy Time Signal Bot*\n━━━━━━━━━━━━━━━\n"
                 "কমান্ড সমূহ:\n"
                 "/status - বট ও ওয়েবসকেটের অবস্থা দেখুন\n"
                 "/predict - সর্বশেষ স্পিনের প্রেডিকশন (যদি থাকে)\n"
                 "/reset - ডুপ্লিকেট ফিল্টার রিসেট করুন\n\n"
                 "বট স্বয়ংক্রিয়ভাবে প্রতি স্পিনে ফলাফল পাঠাবে।", 
                 parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def status_command(message):
    if predictor:
        seg_type = "✅ Dynamic" if predictor.current_segments else "⚠️ Default (static)"
        status_text = (f"📡 *সংযোগ স্ট্যাটাস*\n"
                       f"ওয়েবসকেট: {'🟢 সংযুক্ত' if predictor.ws and predictor.ws.sock else '🔴 বিচ্ছিন্ন'}\n"
                       f"সেগমেন্ট: {seg_type} ({len(predictor.get_segments())}个)\n"
                       f"শেষ স্পিন আইডি: `{predictor.last_spin_id}`")
    else:
        status_text = "বট ইনিশিয়ালাইজ হয়নি।"
    bot.reply_to(message, status_text, parse_mode="Markdown")

@bot.message_handler(commands=['predict'])
def predict_command(message):
    if predictor and predictor.last_spin_id:
        # last predicted result from most recent angle (we don't store it, but can calculate if we have last angle)
        bot.reply_to(message, "শেষ স্পিনের তথ্য মেমরিতে নেই। পরবর্তী স্পিনের জন্য অপেক্ষা করুন।")
    else:
        bot.reply_to(message, "এখনও কোনো স্পিন ডিটেক্ট হয়নি।")

@bot.message_handler(commands=['reset'])
def reset_command(message):
    if predictor:
        predictor.last_spin_id = None
        bot.reply_to(message, "✅ ডুপ্লিকেট ফিল্টার রিসেট করা হয়েছে।")
    else:
        bot.reply_to(message, "বট চলছে না।")

# ========== মেইন এন্ট্রি পয়েন্ট ==========
if __name__ == "__main__":
    # ফ্লাস্ক সার্ভার ব্যাকগ্রাউন্ডে চালান (হেরোকু/রেন্ডার এর জন্য)
    threading.Thread(target=run_web, daemon=True).start()
    
    # টেলিগ্রাম বটের জন্য পোলিং থ্রেড
    def run_bot():
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(5)
    
    threading.Thread(target=run_bot, daemon=True).start()
    time.sleep(2)  # বট স্টার্টআপের জন্য সামান্য দেরি
    
    # প্রেডিক্টর শুরু
    predictor = MasterPredictor()
    predictor.connect()
