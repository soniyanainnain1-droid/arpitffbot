import requests
import json
import time


# =========================
# Configuration
# =========================

BOT_TOKEN = ""
EXTERNAL_API_URL = ""

TELEGRAM_API_URL = "https://api.telegram.org/bot" + BOT_TOKEN


# =========================
# Telegram API helper
# =========================

def telegram_request(method, data):
    url = TELEGRAM_API_URL + "/" + method

    try:
        response = requests.post(
            url,
            data=data,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        print("Telegram API error:", error)
        return None

    except ValueError:
        print("Telegram returned invalid JSON.")
        return None


# =========================
# Send message
# =========================

def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup is not None:
        data["reply_markup"] = json.dumps(reply_markup)

    return telegram_request("sendMessage", data)


# =========================
# Custom keyboard
# =========================

def phone_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "📱 Phone Lookup"
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


# =========================
# Welcome message
# =========================

def send_welcome(chat_id):
    welcome_text = (
        "👋 Welcome!\n\n"
        "Use the button below to start a phone lookup."
    )

    send_message(
        chat_id,
        welcome_text,
        phone_keyboard()
    )


# =========================
# External API request
# =========================

def lookup_phone(phone_number):
    if not EXTERNAL_API_URL:
        return {
            "error": "External API URL is not configured."
        }

    try:
        # Educational example:
        # The phone number is sent as a query parameter.
        response = requests.get(
            EXTERNAL_API_URL,
            params={
                "phone": phone_number
            },
            timeout=30
        )

        response.raise_for_status()

        # Convert the external API response into JSON.
        return response.json()

    except requests.RequestException as error:
        return {
            "error": "External API request failed.",
            "details": str(error)
        }

    except ValueError:
        return {
            "error": "External API did not return valid JSON."
        }


# =========================
# Dummy HTTPS server
# =========================
#
# This is intentionally only a placeholder.
# Python's built-in HTTP server cannot be used here
# because the requirement restricts imports to:
# requests, json, and time.
#
# If you have an HTTPS endpoint elsewhere, place its
# URL in EXTERNAL_API_URL.
#
# Example:
#
# EXTERNAL_API_URL = "https://example.com/api/lookup"
#
# No local server is required for Telegram long polling.
# =========================


# =========================
# Process Telegram message
# =========================

def process_message(message):
    if "chat" not in message:
        return

    chat_id = message["chat"]["id"]

    if "text" not in message:
        return

    text = message["text"].strip()

    # /start command
    if text == "/start":
        send_welcome(chat_id)
        return

    # Phone lookup button
    if text == "📱 Phone Lookup":
        send_message(
            chat_id,
            "📞 Send 10 digit mobile number:"
        )
        return

    # Validate 10-digit numeric mobile number
    if text.isdigit() and len(text) == 10:
        send_message(
            chat_id,
            "⏳ Looking up the number..."
        )

        result = lookup_phone(text)

        # Convert the Python object to formatted JSON.
        formatted_json = json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )

        # Telegram HTML <pre> formatting.
        output = "<pre>" + formatted_json + "</pre>"

        send_message(
            chat_id,
            output
        )
        return

    # Invalid input
    send_message(
        chat_id,
        "❌ Invalid input.\n\n"
        "Please send exactly 10 numeric digits."
    )


# =========================
# Long polling
# =========================

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is empty.")
        print("Add your Telegram bot token to BOT_TOKEN.")
        return

    offset = 0

    print("Bot started.")
    print("Waiting for Telegram updates...")

    while True:
        try:
            response = telegram_request(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 30
                }
            )

            if not response:
                time.sleep(2)
                continue

            if not response.get("ok"):
                print("getUpdates failed:", response)
                time.sleep(3)
                continue

            updates = response.get("result", [])

            for update in updates:
                update_id = update.get("update_id")

                if update_id is not None:
                    offset = update_id + 1

                if "message" in update:
                    process_message(update["message"])

        except KeyboardInterrupt:
            print("\nBot stopped.")
            break

        except Exception as error:
            print("Unexpected error:", error)
            time.sleep(3)


if __name__ == "__main__":
    main()
