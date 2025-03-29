from django.core.management import BaseCommand
from django.db import transaction

from rage.models import DistrictSanitaire, Commune, HealthRegion


class Command(BaseCommand):
    help = 'Met à jour les relations géographiques entre les communes, les districts sanitaires et les régions de santé.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.update_commune_district_relations()
        self.update_district_region_relations()

    def update_commune_district_relations(self):
        communes = Commune.objects.all()
        for commune in communes:
            if commune.district is None:
                try:
                    district = DistrictSanitaire.objects.get(nom__iexact=commune.name)
                    commune.district = district
                    commune.save()
                    self.stdout.write(self.style.SUCCESS(f'Commune "{commune.name}" mise à jour avec le district "{district.nom}".'))
                except DistrictSanitaire.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Pas de district trouvé pour la commune "{commune.name}".'))
                except DistrictSanitaire.MultipleObjectsReturned:
                    self.stdout.write(self.style.ERROR(f'Plusieurs districts trouvés pour la commune "{commune.name}".'))

    def update_district_region_relations(self):
        districts = DistrictSanitaire.objects.all()
        for district in districts:
            if district.region is None:
                try:
                    region = HealthRegion.objects.get(name__iexact=district.nom)
                    district.region = region
                    district.save()
                    self.stdout.write(self.style.SUCCESS(f'District "{district.nom}" mis à jour avec la région "{region.name}".'))
                except HealthRegion.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Pas de région trouvée pour le district "{district.nom}".'))
                except HealthRegion.MultipleObjectsReturned:
                    self.stdout.write(self.style.ERROR(f'Plusieurs régions trouvées pour le district "{district.nom}".'))