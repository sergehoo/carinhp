import os
import requests
from dotenv import load_dotenv
from django.conf import settings

from rage.models import WhatsAppMessageLog

load_dotenv()


class WhatsAppService:
    BASE_URL = f"https://graph.facebook.com/{os.getenv('WHATSAPP_API_VERSION', 'v19.0')}"

    @classmethod
    def send_template_message(cls, phone_number, template_name, language_code="fr", components=None):
        """Envoie un message template via l'API WhatsApp"""
        url = f"{cls.BASE_URL}/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }

        if components:
            payload["template"]["components"] = components

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erreur d'envoi WhatsApp: {e}")
            return None

    @classmethod
    def send_custom_message(cls, phone_number, message):
        """Envoie un message personnalisé via l'API WhatsApp"""
        url = f"{cls.BASE_URL}/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erreur d'envoi WhatsApp: {e}")
            return None

@classmethod
def log_message(cls, phone_number, template_name=None, message=None, response=None):
    WhatsAppMessageLog.objects.create(
        numero=phone_number,
        template=template_name,
        contenu_message=message,
        statut='Success' if response else 'Failed',
        response=response,
    )