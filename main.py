import json
import os
import random
import time

import requests
import telebot


def load_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_json_env(name: str, default: str = "{}") -> dict:
    raw_value = os.getenv(name, default)
    try:
        parsed = json.loads(raw_value)
        if not isinstance(parsed, dict):
            raise ValueError
        return parsed
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must contain valid JSON object") from exc


def chunk_text(text: str, size: int = 4000) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)] or [""]


def load_dotenv_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


load_dotenv_file()

BOT_TOKEN = load_env("BOT_TOKEN")
INSTAGRAM_URL = load_env("INSTAGRAM_URL")
REQUEST_PARAMS = load_json_env("INSTAGRAM_PARAMS_JSON", '{"count": "12", "hl": "ar"}')
REQUEST_HEADERS = load_json_env("INSTAGRAM_HEADERS_JSON")
REQUEST_COOKIES = load_json_env("INSTAGRAM_COOKIES_JSON")

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "مرحباً بك في البوت 🤖\n"
        "أرسل أمر /fetch لبدء جلب البيانات.",
    )


@bot.message_handler(commands=["fetch"])
def fetch_instagram_data(message):
    status_msg = bot.reply_to(message, "🔄 جاري جلب البيانات... انتظر قليلاً.")

    session = requests.Session()
    all_users = []
    page_num = 1
    params = dict(REQUEST_PARAMS)

    while True:
        print(f"🔄 جاري جلب الصفحة رقم {page_num}...")
        response = session.get(
            INSTAGRAM_URL,
            headers=REQUEST_HEADERS,
            params=params,
            cookies=REQUEST_COOKIES,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            users_in_page = data.get("users", [])
            all_users.extend(users_in_page)

            print(f"✅ تم جلب {len(users_in_page)} مستخدم في هذه الصفحة. الإجمالي: {len(all_users)}")
            for user in users_in_page:
                username = user.get("username")
                if username:
                    print(f"   - @{username}")

            has_more = data.get("has_more", False)
            next_max_id = data.get("next_max_id")

            if has_more and next_max_id:
                params["max_id"] = str(next_max_id)
                page_num += 1
                sleep_time = random.uniform(3.0, 7.0)
                print(f"⏳ الانتظار لمدة {sleep_time:.2f} ثوانٍ...")
                time.sleep(sleep_time)
                print("-" * 40)
            else:
                print("🎉 تم جلب جميع البيانات بنجاح!")
                break

        elif response.status_code == 429:
            print("⚠️ تم الوصول إلى حد الطلبات (429).")
            break
        else:
            print(f"❌ فشل الطلب عند الصفحة {page_num}، كود الخطأ: {response.status_code}")
            print(response.text)
            break

    result_lines = [
        f"🎉 تم جلب البيانات بنجاح!",
        f"📊 إجمالي العناصر المستخرجة: {len(all_users)}",
        "",
        "القائمة:",
    ]
    for idx, user in enumerate(all_users, 1):
        username = user.get("username", "unknown")
        result_lines.append(f"{idx}. @{username}")

    result_text = "\n".join(result_lines)

    if len(result_text) > 4000:
        bot.send_message(message.chat.id, "📄 القائمة طويلة جداً، سيتم تقسيمها:")
        for part in chunk_text(result_text):
            bot.send_message(message.chat.id, part)
    else:
        bot.edit_message_text(result_text, chat_id=message.chat.id, message_id=status_msg.message_id)


print("⚡ البوت يعمل الآن ومستعد لاستقبال الأوامر...")
bot.infinity_polling()
