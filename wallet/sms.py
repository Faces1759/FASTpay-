import requests
from django.conf import settings


def send_sms(phone_number, message):
    url = "https://api.ng.termii.com/api/sms/send"

    payload = {
        "api_key": settings.TERMII_API_KEY,
        "to": phone_number,
        "from": settings.TERMII_SENDER_ID,
        "sms": message,
        "type": "plain",
        "channel": "generic",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )
        print(response.json())
    except Exception as e:
        print("SMS Error:", e)