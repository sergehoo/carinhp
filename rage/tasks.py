import json
import logging

from celery import shared_task
from django.conf import settings

from twilio.rest import Client

from django.utils import timezone

from rage.models import Vaccination, WhatsAppMessageLog

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_sms_postvaccination(self, vaccination_id):
    from .models import Vaccination
    from twilio.rest import Client

    vac = Vaccination.objects.select_related("patient").get(pk=vaccination_id)
    patient = vac.patient
    numero = getattr(patient, "contact", None)

    if not numero:
        logger.warning(f"⚠️ Pas de numéro SMS pour patient {patient.pk}")
        return

    message_text = (
        f"Bonjour {patient.nom}, Nous confirmons que votre vaccination effectuée le {vac.date_effective.strftime('%d/%m/%Y à %H:%M')} a été enregistrée avec succès.Prenez soin de vous,L\'équipe de vaccination"

    )

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
        body=message_text,
        # from_=settings.TWILIO_SMS_NUMBER,
        to=f"+{numero}"
    )

    logger.info(f"📲 SMS post-vaccination envoyé - SID: {message.sid}")
    return message.sid



@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_whatsapp_followup(self, vaccination_id):
    logger.info(f"📨 Envoi WhatsApp pour vaccination #{vaccination_id}")
    try:
        vac = Vaccination.objects.select_related('patient').get(pk=vaccination_id)

        if not vac.date_effective:
            logger.warning("⚠️ Vaccination sans date effective.")
            return

        patient = vac.patient
        numero = getattr(patient, "contact", None)

        if not numero:
            logger.warning(f"⚠️ Patient #{patient.pk} sans numéro.")
            return

        date_str = vac.date_effective.strftime('%d/%m/%Y à %H:%M')
        body = (
            f"Bonjour {patient.nom},\n\n"
            f"Votre vaccination du {date_str} est terminée.\n"
            "Merci pour votre confiance et prenez soin de vous."
        )

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        logger.info(f"📤 Envoi à {numero} via WhatsApp avec le message :\n{body}")
        message = client.messages.create(
            to=f"whatsapp:{numero}",
            messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
            content_sid=settings.TWILIO_CONTENT_SID,
            content_variables=json.dumps({
                "1": patient.nom,
                "2": vac.date_effective.strftime("%d/%m/%Y"),
                "3": vac.date_effective.strftime("%H:%M"),
            })
        )
        # message = client.messages.create(
        #     messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,  # facultatif si tu l'utilises
        #     to=f"whatsapp:+{numero}",
        #     from_=settings.TWILIO_WHATSAPP_NUMBER,
        #     content_sid="",
        #     provide_feedback=True,
        #     content_variables=json.dumps({
        #         "1": patient.nom,
        #         "2": vac.date_effective.strftime("%d/%m/%Y"),
        #         "3": vac.date_effective.strftime("%H:%M"),
        #     }),
        # )

        WhatsAppMessageLog.objects.create(
            vaccination=vac,
            sid=message.sid,
            to=message.to,
            status=message.status,
            body=message.body
        )

        logger.info(
            f"✅ WhatsApp envoyé - SID: {message.sid} 📤 Numéro Twilio utilisé : {settings.TWILIO_WHATSAPP_NUMBER}")

    except Vaccination.DoesNotExist:
        logger.error(f"❌ Vaccination #{vaccination_id} introuvable.")
        # logger.info(f"📤 Numéro Twilio utilisé : {settings.TWILIO_WHATSAPP_NUMBER}")
        logger.exception("❌ Erreur d'envoi WhatsApp, tentative fallback SMS...")
        logger.info(f"📤 Content SID utilisé : {settings.TWILIO_CONTENT_SID}")
        send_sms_fallback.apply_async(args=[vaccination_id], countdown=60)
        raise self.retry(exc=Exception('Vaccination introuvable'))

    except Exception as e:
        logger.exception("❌ Erreur d'envoi WhatsApp")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_sms_fallback(self, vaccination_id):
    from .models import Vaccination
    try:
        vac = Vaccination.objects.select_related("patient").get(pk=vaccination_id)
        patient = vac.patient
        numero = getattr(patient, "contact", None)

        if not numero or vac.relance_sms_envoyee:
            return

        body = (
            f"Bonjour {patient.nom}, votre vaccination du "
            f"{vac.date_effective.strftime('%d/%m/%Y à %H:%M')} est enregistrée. "
            "Merci de prendre soin de vous."
        )

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            to=f"{numero}",
            from_=settings.TWILIO_SMS_NUMBER,
            body=body
        )

        # Marquer comme relancé
        vac.relance_sms_envoyee = True
        vac.save(update_fields=["relance_sms_envoyee"])

        logger.info(f"📲 SMS de secours envoyé à {numero} - SID: {message.sid}")

    except Vaccination.DoesNotExist:
        logger.error(f"Vaccination #{vaccination_id} introuvable pour relance SMS")
        raise self.retry(exc=Exception("Vaccination introuvable"))
    except Exception as e:
        logger.exception("Erreur lors de l’envoi SMS fallback")
        raise self.retry(exc=e)
