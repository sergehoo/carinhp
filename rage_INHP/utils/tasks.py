import logging
from datetime import timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now

from rage.models import RendezVousVaccination, SMSLog
from rage_INHP.utils.whatsapp_service import WhatsAppService


@shared_task
def envoyer_rappels_whatsapp():
    demain = timezone.now().date() + timedelta(days=1)
    rendez_vous = RendezVousVaccination.objects.filter(date_rendez_vous=demain, est_effectue=False)

    for rdv in rendez_vous:
        patient = rdv.patient
        if not patient.contact:
            continue

        components = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": patient.nom},
                {"type": "text", "text": rdv.date_rendez_vous.strftime("%d/%m/%Y")},
                {"type": "text", "text": str(rdv.dose_numero)}
            ]
        }]

        WhatsAppService.send_template_message(
            phone_number=str(patient.contact),
            template_name="rappel_rendez_vous",
            components=components
        )


logger = logging.getLogger(__name__)

ORANGE_TOKEN_URL = "https://api.orange.com/oauth/v3/token"
ORANGE_SMS_URL = "https://api.orange.com/smsmessaging/v1/outbound/tel:{}/requests"


def get_orange_token():
    client_id = settings.ORANGE_SMS_CLIENT_ID
    client_secret = settings.ORANGE_SMS_CLIENT_SECRET
    # print(f'✅ client id: {client_id}')
    # print(f'✅ client secret: {client_secret}')

    response = requests.post(
        ORANGE_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=10
    )
    response.raise_for_status()
    return response.json()["access_token"]


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_analysis_sms(self, phone_number, message):
    task_id = self.request.id
    try:
        sender = settings.ORANGE_SMS_SENDER  # ✅ lire depuis settings
        access_token = get_orange_token()
        client_id = settings.ORANGE_SMS_CLIENT_ID
        client_secret = settings.ORANGE_SMS_CLIENT_SECRET
        # print(f'✅ client id: {client_id}')
        # print(f'✅ client secret: {client_secret}')
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
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        try:
            SMSLog.objects.create(
                phone_number=phone_number,
                message=message,
                status="SUCCESS",
                response_content=response.text,
                task_id=task_id,
            )
            print("✅ Log SUCCESS enregistré")
            logger.warning("✅ Log SUCCESS enregistré")

        except Exception as log_error:
            print(f"❌ Échec enregistrement log SUCCESS: {log_error}")

        logger.info(f"✅ SMS envoyé à {phone_number} : {message}")
        return response.json()

    except requests.RequestException as e:
        try:
            SMSLog.objects.create(
                phone_number=phone_number,
                message=message,
                status="FAILED",
                error=str(e),
                task_id=task_id,
            )
            print("✅ Log FAILED enregistré")
            logger.warning("✅ Log FAILED enregistré")
        except Exception as log_error:
            print(f"❌ Échec enregistrement log FAILED: {log_error}")

        logger.error(f"⛔ Échec envoi SMS à {phone_number}: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def envoyer_rappels_rdv_vaccination():
    demain = now().date() + timedelta(days=1)
    rendez_vous = RendezVousVaccination.objects.filter(
        date_rendez_vous=demain,
        est_effectue=False,
        rappel_envoye=False
    ).select_related('patient')

    for rdv in rendez_vous:
        patient = rdv.patient
        message = (
            f"Rappel INHP : vous avez un rendez-vous de vaccination le {rdv.date_rendez_vous.strftime('%d/%m/%Y')}."
            "\nMerci d’être à l’heure. L’équipe INHP est à vos côtés ! 💉"
        )
        try:
            send_analysis_sms.delay(patient.contact_information, message)
            rdv.rappel_envoye = True
            rdv.save(update_fields=['rappel_envoye'])
        except Exception as e:
            print(f"[❌] Échec envoi SMS à {patient.contact_information} : {e}")
