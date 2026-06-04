import asyncio
import json
import os
import random

import httpx
import pandas as pd
import telebot
from telebot.async_telebot import AsyncTeleBot


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

bot = AsyncTeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
async def send_welcome(message):
    await bot.reply_to(
        message,
        "مرحباً بك في البوت 🤖\n"
        "أرسل أمر /fetch لبدء جلب البيانات واستخراج ملف Excel.",
    )


@bot.message_handler(commands=["fetch"])
async def fetch_instagram_data(message):
    status_msg = await bot.reply_to(message, "🔄 جاري جلب البيانات وإنشاء ملف Excel... انتظر قليلاً.")

    all_users = []
    page_num = 1
    params = dict(REQUEST_PARAMS)

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            print(f"🔄 جاري جلب الصفحة رقم {page_num}...")
            try:
                response = await client.get(
                    INSTAGRAM_URL,
                    headers=REQUEST_HEADERS,
                    params=params,
                    cookies=REQUEST_COOKIES,
                )
            except Exception as e:
                print(f"❌ خطأ في الاتصال: {e}")
                break

            if response.status_code == 200:
                data = response.json()
                users_in_page = data.get("users", [])
                all_users.extend(users_in_page)

                print(f"✅ تم جلب {len(users_in_page)} مستخدم. الإجمالي: {len(all_users)}")

                has_more = data.get("has_more", False)
                next_max_id = data.get("next_max_id")

                if has_more and next_max_id:
                    params["max_id"] = str(next_max_id)
                    page_num += 1
                    sleep_time = random.uniform(3.0, 7.0)
                    print(f"⏳ الانتظار غير المتزامن لمدة {sleep_time:.2f} ثوانٍ...")
                    await asyncio.sleep(sleep_time)
                    print("-" * 40)
                else:
                    print("🎉 تم جلب جميع البيانات بنجاح!")
                    break

            elif response.status_code == 429:
                print("⚠️ تم الوصول إلى حد الطلبات (429).")
                break
            else:
                print(f"❌ فشل الطلب، كود الخطأ: {response.status_code}")
                break

    if not all_users:
        await bot.edit_message_text(
            "❌ لم يتم العثور على أي بيانات أو فشلت عملية الجلب.",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
        )
        return

    extracted_data = []
    for idx, user in enumerate(all_users, 1):
        extracted_data.append(
            {
                "الرقم": idx,
                "اسم المستخدم (Username)": user.get("username", "unknown"),
                "الاسم الكامل (Full Name)": user.get("full_name", ""),
                "معرف الحساب (ID)": user.get("pk", ""),
            }
        )

    df = pd.DataFrame(extracted_data)
    file_path = f"instagram_users_{message.chat.id}.xlsx"
    df.to_excel(file_path, index=False)

    await bot.edit_message_text(
        f"🎉 تم جلب البيانات بنجاح!\n📊 إجمالي العناصر المستخرجة: {len(all_users)}\n📂 جاري إرسال ملف Excel...",
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
    )

    try:
        with open(file_path, "rb") as excel_file:
            await bot.send_document(message.chat.id, excel_file, caption="📊 ملف الحسابات المستخرجة")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    print("⚡ البوت المطوّر (Async) يعمل الآن ومستعد لاستقبال الأوامر...")
    asyncio.run(bot.infinity_polling())
