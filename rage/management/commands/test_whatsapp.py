from django.core.management.base import BaseCommand
from rage.tasks import send_whatsapp_followup
from rage.models import Vaccination


class Command(BaseCommand):
    help = "Test d'envoi WhatsApp à partir de la dernière vaccination"

    def handle(self, *args, **kwargs):
        try:
            vac = Vaccination.objects.latest('created_at')
            self.stdout.write(f"✅ Vaccination #{vac.pk} sélectionnée pour test")
            send_whatsapp_followup.delay(vac.pk)
        except Vaccination.DoesNotExist:
            self.stdout.write("❌ Aucune vaccination trouvée.")
