import os
import telebot
import requests
import threading
import time
import json
from flask import Flask
from telebot import types

# ----------------------------------------------------
# ১. Render Port Binding ও Keep-Alive
# ----------------------------------------------------
app = Flask(__name__)
# আপনার ২য় বটের Render ওয়েবসাইট লিঙ্ক
RENDER_URL = "https://your-bot-2.onrender.com"

@app.route('/')
def home():
    return "Cloud OTP Bot 2 Active!", 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

def keep_alive_pinger():
    while True:
        time.sleep(300)
        try:
            if "your-bot-2" not in RENDER_URL:
                requests.get(RENDER_URL, timeout=10)
        except: pass

threading.Thread(target=keep_alive_pinger, daemon=True).start()

# ----------------------------------------------------
# ২. বটের মূল কনফিগারেশন (নতুন সাইট এপিআই)
# ----------------------------------------------------
BOT_TOKEN = "YOUR_SECOND_BOT_TOKEN"  # ২য় বটের নতুন টোকেন দিন
API_KEY = "YOUR_2OO9_CLOUD_API_KEY"  # নতুন সাইটের এপিআই কি দিন

# এপিআই বেস ইউআরএল
BASE_API = "https://api.2oo9.cloud/MXS47FLFX0U/tnemn/@public/api"

# ⚠️ এখানে /myid লিখে পাওয়া আপনার টেলিগ্রাম আইডি বসাবেন
ADMIN_ID = None  

BOT_USERNAME = "YourSecondBotUsername" # ২য় বটের ইউজারনেম
RANGE_GROUP = "@hototprange"           # ২য় বটের রেঞ্জ চ্যানেল/গ্রুপ

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "bot2_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"users": [], "ranges": {}, "total_otps": 0, "settings": {"support": "@hototpotp", "range_group": "@hototprange"}}

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(db, f)
    except: pass

db = load_data()
posted_signatures = set()

MENU_BUTTONS = [
    "☎️ Get Number", "⚙️ Change Range", "📱 Range Group", 
    "✉️ Get Tempmail", "🔐 2FA", "👤 Fake Name", "🔽 OTHER", 
    "💬 Support", "🏠 Home"
]

def is_admin(chat_id):
    if ADMIN_ID is None: return True
    return str(chat_id) == str(ADMIN_ID) or chat_id == ADMIN_ID

def get_setting(key, default_val):
    try:
        val = db.get("settings", {}).get(key)
        return val if val else default_val
    except:
        return default_val

# ----------------------------------------------------
# ৩. টেলিগ্রাম পপ-আপ মেনু কমান্ডস
# ----------------------------------------------------
try:
    bot_commands = [
        types.BotCommand("start", "🚀 Start"),
        types.BotCommand("home", "🏠 Home"),
        types.BotCommand("number", "☎️ Get Number"),
        types.BotCommand("range", "⚙️ Change Range"),
        types.BotCommand("admin", "⚙️ Admin Panel"),
        types.BotCommand("help", "💬 Support")
    ]
    bot.set_my_commands(bot_commands)
except Exception as e:
    print(f"Commands set error: {e}")

def bottom_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("☎️ Get Number"), types.KeyboardButton("⚙️ Change Range"))
    markup.add(types.KeyboardButton("📱 Range Group"), types.KeyboardButton("💬 Support"))
    return markup

print("---------------------------------")
print("🔥 Cloud OTP Bot 2 Started Successfully!")
print("---------------------------------")

# ----------------------------------------------------
# ৪. গ্লোবাল লাইভ ফিড অটো-পোস্টার (GET /hits)
# ----------------------------------------------------
def auto_post_live_hits():
    headers = {"mauthapi": API_KEY}
    while True:
        try:
            target_chan = get_setting("range_group", RANGE_GROUP)
            url = f"{BASE_API}/hits"
            res = requests.get(url, headers=headers, timeout=10).json()
            
            hits_list = []
            if isinstance(res, dict) and res.get("data"):
                hits_list = res.get("data", {}).get("hits", [])
                
            if isinstance(hits_list, list) and len(hits_list) > 0:
                for item in reversed(hits_list[:10]):
                    if not isinstance(item, dict): continue
                    
                    range_val = str(item.get("range") or "").strip()
                    sid = str(item.get("sid") or "OTP").strip()
                    msg = str(item.get("message") or "Live Signal").strip()
                    
                    if not range_val: continue
                    sig = f"{range_val}_{sid}_{msg[:10]}"
                    
                    if sig in posted_signatures: continue
                    posted_signatures.add(sig)
                    if len(posted_signatures) > 1000: posted_signatures.clear()

                    post_text = (
                        f"🔥 <b>LIVE OTP HIT SIGNAL</b> 🔥\n\n"
                        f"📱 <b>Range:</b> <code>{range_val}</code>\n"
                        f"🎯 <b>Service:</b> {sid}\n"
                        f"💬 <b>Status:</b> <code>{msg}</code>\n\n"
                        f"👇 <b>১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিতে নিচে চাপ দিন:</b>"
                    )

                    markup = types.InlineKeyboardMarkup()
                    btn = types.InlineKeyboardButton("🤖 Bot-এ এই নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}?start={range_val}")
                    markup.add(btn)

                    try:
                        bot.send_message(target_chan, post_text, reply_markup=markup, parse_mode="HTML")
                        time.sleep(3)
                    except telebot.apihelper.ApiTelegramException as te:
                        if te.error_code == 429: time.sleep(20)
                    except Exception: time.sleep(3)
        except Exception as e: print(f"Hits loop error: {e}")
        time.sleep(10)

threading.Thread(target=auto_post_live_hits, daemon=True).start()

# ----------------------------------------------------
# ৫. ওটিপি ফিল্টার (GET /otps)
# ----------------------------------------------------
def fetch_otp_2oo9(number):
    headers = {"mauthapi": API_KEY}
    clean_target = str(number).replace("+", "").strip()
    
    try:
        url = f"{BASE_API}/otps"
        res = requests.get(url, headers=headers, timeout=5).json()
        
        otps = []
        if isinstance(res, dict) and res.get("data"):
            otps = res.get("data", {}).get("otps", [])
            
        if isinstance(otps, list):
            for item in otps:
                if isinstance(item, dict):
                    num = str(item.get("number") or "").replace("+", "").strip()
                    if clean_target and clean_target in num:
                        sms_msg = item.get("message") or item.get("text") or ""
                        if sms_msg and str(sms_msg).strip() != "":
                            return f"📩 <b>OTP Received:</b> <code>{sms_msg}</code>"
    except Exception: pass
    return None

def auto_check_otp_2oo9(chat_id, number):
    for _ in range(60):
        time.sleep(3)
        otp = fetch_otp_2oo9(number)
        if otp:
            db["total_otps"] = db.get("total_otps", 0) + 1
            save_data()
            bot.send_message(chat_id, f"🎉 <b>ওটিপি চলে এসেছে!</b>\n\n{otp}", parse_mode="HTML")
            return

# ----------------------------------------------------
# ৬. বট মেসেজ হ্যান্ডলারস
# ----------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    bot.clear_step_handler_by_chat_id(chat_id)

    if chat_id not in db["users"]:
        db["users"].append(chat_id)
        save_data()

    args = message.text.split()
    if len(args) > 1:
        deep_range = args[1].strip()
        db["ranges"][chat_str] = deep_range
        save_data()
        bot.send_message(chat_id, f"✅ <b>রেঞ্জ সিলেক্ট হয়েছে:</b> <code>{deep_range}</code>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")
        fetch_and_send_number(chat_id, deep_range)
        return

    db["ranges"].pop(chat_str, None)
    save_data()
    bot.send_message(chat_id, "👋 <b>Welcome to OTP Bot 2!</b>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")

@bot.message_handler(commands=['myid'])
def my_id_command(message):
    bot.reply_to(message, f"🆔 আপনার আইডি: <code>{message.chat.id}</code>", parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_panel_cmd(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "❌ <b>Access Denied!</b>", parse_mode="HTML")
        return
    supp = get_setting("support", "@hototpotp")
    rng = get_setting("range_group", RANGE_GROUP)
    msg = f"⚙️ <b>ADMIN PANEL</b> ⚙️\n\n💬 Support: <code>{supp}</code>\n📱 Channel: <code>{rng}</code>"
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "☎️ Get Number" or m.text == "/number")
def get_number_handler(message):
    chat_id = message.chat.id
    saved_r = db["ranges"].get(str(chat_id))
    if saved_r:
        fetch_and_send_number(chat_id, saved_r)
    else:
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি টাইপ করে পাঠান\n(যেমন: <code>26134</code> বা <code>26134XXX</code>):", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_save_range)

@bot.message_handler(func=lambda m: m.text == "⚙️ Change Range" or m.text == "/range")
def change_range_handler(message):
    msg = bot.send_message(message.chat.id, "আপনার পছন্দমতো রেঞ্জটি টাইপ করুন:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_save_range)

@bot.message_handler(func=lambda m: m.text == "💬 Support" or m.text == "/help")
def support_handler(message):
    supp = get_setting("support", "@hototpotp")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 এডমিন সাপোর্ট", url=f"https://t.me/{supp.replace('@', '')}"))
    bot.send_message(message.chat.id, f"💬 <b>সহায়তা:</b> {supp}", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    chat_str = str(chat_id)
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data == "reset_all":
        db["ranges"].pop(chat_str, None)
        save_data()
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.send_message(chat_id, "🔄 <b>রিসেট করা হয়েছে!</b>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")
        
    elif call.data == "get_num_auto":
        saved_r = db["ranges"].get(chat_str)
        if saved_r: 
            fetch_and_send_number(chat_id, saved_r, message_id=call.message.message_id)

    elif call.data.startswith("check_otp_"):
        number = call.data.replace("check_otp_", "")
        otp = fetch_otp_2oo9(number)
        if otp: bot.send_message(chat_id, f"🎉 <b>ওটিপি চলে এসেছে!</b>\n\n{otp}", parse_mode="HTML")
        else: bot.answer_callback_query(call.id, text="এখনো ওটিপি আসেনি! ২-৩ সেকেন্ড পর আবার চাপুন...", show_alert=True)

def process_save_range(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    if text in MENU_BUTTONS or text.startswith("/"): return
    db["ranges"][str(chat_id)] = text
    save_data()
    bot.send_message(chat_id, f"✅ <b>রেঞ্জ সেভ হয়েছে:</b> <code>{text}</code>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")
    fetch_and_send_number(chat_id, text)

# ২oo৯ এপিআই দিয়ে নাম্বার নেওয়া
def fetch_and_send_number(chat_id, user_range, message_id=None):
    if not message_id:
        bot.send_message(chat_id, f"⏳ <code>{user_range}</code> রেঞ্জ দিয়ে নাম্বার নেওয়া হচ্ছে...", parse_mode="HTML")
    
    clean_rid = str(user_range).upper().replace("XXX", "").strip()
    
    url = f"{BASE_API}/getnum"
    headers = {"mauthapi": API_KEY, "Content-Type": "application/json"}
    payload = {"rid": clean_rid}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10).json()
        
        meta_code = res.get("meta", {}).get("code") or res.get("code")
        data = res.get("data", {}) or {}
        
        if meta_code == 200 and data.get("no_plus_number"):
            country = data.get("country", "Global")
            operator = data.get("operator", "")
            raw_num = str(data.get("no_plus_number")).strip()

            msg_text = (
                f"✅ <b>Number:</b> 🌐 {country} ({operator})\n\n"
                f"👇 <b>নাম্বারটির ওপর চাপ দিলে সরাসরি কপি হবে:</b>\n<code>{raw_num}</code>"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            try:
                btn_num1 = types.InlineKeyboardButton(f"📋 📱 {raw_num}", copy_text=types.CopyTextButton(raw_num))
            except:
                btn_num1 = types.InlineKeyboardButton(f"📋 📱 {raw_num}", callback_data="copy_info")

            btn_change_num = types.InlineKeyboardButton("🔄 Change Number", callback_data="get_num_auto")
            btn_refresh = types.InlineKeyboardButton("🔄 Refresh", callback_data=f"check_otp_{raw_num}")
            btn_back = types.InlineKeyboardButton("⬅️ Back", callback_data="reset_all")

            markup.add(btn_num1)
            markup.add(btn_change_num, btn_refresh)
            markup.add(btn_back)
            
            if message_id:
                try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg_text, reply_markup=markup, parse_mode="HTML")
                except: bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
                
            threading.Thread(target=auto_check_otp_2oo9, args=(chat_id, raw_num), daemon=True).start()
        else:
            err_msg = res.get("message") or "নাম্বার স্টক শেষ!"
            bot.send_message(chat_id, f"❌ সমস্যা: {err_msg}", reply_markup=bottom_main_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"❌ এপিআই এরর: {e}")

# ----------------------------------------------------
# ৭. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
