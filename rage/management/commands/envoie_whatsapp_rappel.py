from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from rage.models import RendezVousVaccination


class Command(BaseCommand):
    help = "Envoie des rappels WhatsApp aux patients ayant un rendez-vous de vaccination demain"

    def handle(self, *args, **options):
        demain = timezone.now().date() + timedelta(days=1)
        rendez_vous = RendezVousVaccination.objects.filter(date_rendez_vous=demain, est_effectue=False)

        if not rendez_vous.exists():
            self.stdout.write("Aucun rendez-vous pour demain.")
            return

        for rdv in rendez_vous:
            patient = rdv.patient
            if not patient.contact:
                continue

            numero = str(patient.contact)

            components = [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": patient.nom},
                    {"type": "text", "text": rdv.date_rendez_vous.strftime("%d/%m/%Y")},
                    {"type": "text", "text": str(rdv.dose_numero)}
                ]
            }]

            response = WhatsAppService.send_template_message(
                phone_number=numero,
                template_name="rappel_rendez_vous",  # nom du template Meta
                components=components
            )

            if response:
                self.stdout.write(self.style.SUCCESS(f"✅ Rappel envoyé à {patient} ({numero})"))
            else:
                self.stdout.write(self.style.WARNING(f"❌ Échec de l'envoi à {patient} ({numero})"))