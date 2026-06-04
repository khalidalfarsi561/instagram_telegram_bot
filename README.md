# Instagram Bot

بوت تيليجرام مبني بـ Python لجلب بيانات من Instagram API وإرسال النتائج عبر Telegram.

## المتطلبات

- Python 3.10+
- حساب Telegram Bot Token
- قيم Instagram API المطلوبة عبر متغيرات البيئة

## التثبيت

```bash
pip install -r requirements.txt
```

## الإعداد

أنشئ ملف `.env` أو عيّن متغيرات البيئة التالية:

- `BOT_TOKEN` — توكن بوت تيليجرام
- `INSTAGRAM_URL` — رابط Instagram API
- `INSTAGRAM_HEADERS_JSON` — هيدرز بصيغة JSON
- `INSTAGRAM_COOKIES_JSON` — كوكيز بصيغة JSON
- `INSTAGRAM_PARAMS_JSON` — باراميترز اختيارية بصيغة JSON

مثال:

```bash
BOT_TOKEN=your_telegram_bot_token
INSTAGRAM_URL=https://www.instagram.com/api/v1/example/
INSTAGRAM_HEADERS_JSON={"user-agent":"Mozilla/5.0"}
INSTAGRAM_COOKIES_JSON={"sessionid":"your_session"}
INSTAGRAM_PARAMS_JSON={"count":"12","hl":"ar"}
```

## التشغيل

```bash
python main.py
```

## ملاحظات

- لا تضع أي أسرار داخل الكود.
- تأكد من أن ملف `.env` غير مرفوع إلى GitHub.
- يمكن تعديل الهيدرز والكوكيز والباراميترز من خلال متغيرات البيئة فقط.

## هيكل المشروع

- `main.py` — منطق البوت
- `requirements.txt` — الحزم المطلوبة
- `.gitignore` — الملفات المستثناة من Git
