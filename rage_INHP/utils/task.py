from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from rage.models import RendezVousVaccination
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