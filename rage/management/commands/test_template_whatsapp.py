import json
from django.core.management.base import BaseCommand
from django.conf import settings
from twilio.rest import Client


class Command(BaseCommand):
    help = "Teste l'envoi d'un message WhatsApp via Twilio ContentSid"

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, required=True, help='Numéro du destinataire (ex: +22507xxxxxxx)')
        parser.add_argument('--template', type=str, required=True, help='ContentSid à utiliser')
        parser.add_argument('--params', type=str, required=True, help='Paramètres séparés par des virgules (ex: "Jean,09/05/2025,10:00")')

    def handle(self, *args, **options):
        to = options['to']
        content_sid = options['template']
        raw_params = options['params']

        try:
            params = [p.strip() for p in raw_params.split(',')]
            content_vars = {str(i + 1): val for i, val in enumerate(params)}

            self.stdout.write(f"📤 Envoi à {to} avec Content SID {content_sid}")
            self.stdout.write(f"📦 Paramètres : {json.dumps(content_vars)}")

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                to=f"whatsapp:{to}",
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                content_sid=content_sid,
                content_variables=json.dumps(content_vars)
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Message envoyé - SID: {message.sid}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Erreur lors de l’envoi : {e}"))