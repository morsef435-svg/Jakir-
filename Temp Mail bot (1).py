import json
import urllib.request
import time

BOT_TOKEN = "7785587052:8642404739:AAHCTFmz_Z6ENVk5O6d8hQ38iaDvPcB_DC8"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
user_data = {}

def send_message(chat_id, text, buttons=None):
    url = API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    if buttons:
        payload["reply_markup"] = json.dumps({
            "inline_keyboard": buttons
        })

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req) as res:
            print("[✓] Message sent.")
    except urllib.error.HTTPError as e:
        print(f"[✗] HTTP Error {e.code}: {e.reason}")
    except Exception as e:
        print(f"[✗] Unexpected error: {e}")

def get_updates(offset=None):
    url = API_URL + "getUpdates"
    if offset:
        url += f"?offset={offset}"
    try:
        with urllib.request.urlopen(url) as res:
            return json.loads(res.read())
    except Exception as e:
        print(f"[✗] Update fetch error: {e}")
        return {}

def handle_command(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    data = user_data.get(chat_id, {})

    if text == "/start":
        buttons = [
            [{"text": "📧 Generate Email", "callback_data": "generate"}],
            [{"text": "📬 Inbox", "callback_data": "inbox"}],
            [{"text": "🗑 Delete Email", "callback_data": "delete"}],
            [{"text": "📊 Statistics", "callback_data": "statistics"}]
        ]
        send_message(chat_id, "👋 Welcome to *Temp mail Welcome to the bot*\n\nChoose an option:", buttons)

def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    user = user_data.get(chat_id)

    if data == "generate":
        email, token = create_email()
        if email:
            user_data[chat_id] = {"email": email, "token": token}
            send_message(chat_id, f"📧 Your email:\n`{email}`")
        else:
            send_message(chat_id, "❌ Failed to generate email.")
    elif data == "inbox":
        if not user:
            send_message(chat_id, "❌ First use Generate Email")
        else:
            inbox = get_inbox(user["email"])
            if inbox:
                for msg in inbox:
                    sender = msg.get("from", "Unknown")
                    subject = msg.get("subject", "No Subject")
                    body = msg.get("body_text", "[No Body]")
                    message_text = f"📨 From: {sender}\n📌 Subject: {subject}\n💬 Message:\n{body[:1000]}"
                    send_message(chat_id, message_text)
            else:
                send_message(chat_id, "📭 Inbox is empty.")
    elif data == "delete":
        if chat_id in user_data:
            del user_data[chat_id]
            send_message(chat_id, "🗑 Email deleted.")
        else:
            send_message(chat_id, "❌ No email to delete.")
    elif data == "statistics":
        total = len(user_data)
        send_message(chat_id, f"📊 Total Emails Generated: {total}")

def create_email():
    url = "https://api.internal.temp-mail.io/api/v3/email/new"
    data = json.dumps({
        "min_name_length": 10,
        "max_name_length": 10
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            r = json.loads(res.read())
            return r["email"], r["token"]
    except Exception as e:
        print("[✗] Email create error:", e)
        return None, None

def get_inbox(email):
    url = f"https://api.internal.temp-mail.io/api/v3/email/{email}/messages"
    headers = {
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except Exception as e:
        print("[✗] Inbox fetch error:", e)
        return []

def main():
    last_update_id = None
    print("🤖 Bot is running...")
    while True:
        updates = get_updates(last_update_id)
        for update in updates.get("result", []):
            last_update_id = update["update_id"] + 1
            if "message" in update:
                handle_command(update["message"])
            elif "callback_query" in update:
                handle_callback(update["callback_query"])
        time.sleep(1)

if __name__ == "__main__":
    main()