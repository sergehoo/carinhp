
import requests
import os
from django.conf import settings

ORANGE_TOKEN_URL = "https://api.orange.com/oauth/v3/token"
ORANGE_SMS_URL = "https://api.orange.com/smsmessaging/v1/outbound/{}/requests"


def get_orange_sms_token():
    client_id = os.getenv("ORANGE_SMS_CLIENT_ID")
    client_secret = os.getenv("ORANGE_SMS_CLIENT_SECRET")

    response = requests.post(
        ORANGE_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret)
    )
    response.raise_for_status()
    return response.json()["access_token"]


def send_sms_to_patient(phone_number, message):
    sender = os.getenv("ORANGE_SMS_SENDER")
    access_token = get_orange_sms_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "outboundSMSMessageRequest": {
            "address": f"tel:{phone_number}",
            "senderAddress": sender,
            "outboundSMSTextMessage": {
                "message": message
            }
        }
    }

    url = ORANGE_SMS_URL.format(sender.replace("tel:", ""))
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
