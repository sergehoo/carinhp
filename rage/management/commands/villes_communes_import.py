import concurrent
import time

import requests
from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand
from rage.models import Commune, DistrictSanitaire, HealthRegion


class Command(BaseCommand):
    help = "Importe les villes et communes de Côte d'Ivoire depuis Wikipédia et ajoute leurs coordonnées GPS."

    def handle(self, *args, **kwargs):
        url = "https://fr.wikipedia.org/wiki/Liste_des_communes_de_C%C3%B4te_d%27Ivoire"
        response = requests.get(url, timeout=10)  # Timeout plus long

        if response.status_code != 200:
            self.stderr.write(self.style.ERROR(f"Erreur Wikipédia : {response.status_code}"))
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        communes = [li.get_text(strip=True) for li in soup.select('div.mw-parser-output ul li') if
                    li.get_text(strip=True)]

        # Tester avec seulement 50 communes (enlever la ligne pour tout traiter)
        # communes = communes[:50]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(self.get_coordinates, communes))

        # Insérer les communes dans la base de données
        for name, geom in zip(communes, results):
            try:
                Commune.objects.get_or_create(
                    name=name,
                    defaults={'type': 'Commune', 'geom': geom}
                )
                self.stdout.write(self.style.SUCCESS(f'Commune "{name}" importée avec succès.'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Erreur insertion {name}: {e}"))

        self.stdout.write(self.style.SUCCESS('Importation des communes terminée.'))

    def get_coordinates(self, commune_name):
        """Récupère les coordonnées GPS via OpenStreetMap"""
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={commune_name}, Côte d'Ivoire"
        headers = {"User-Agent": "DjangoApp/1.0 (contact@email.com)"}  # Remplace par ton email

        for _ in range(3):  # Essayer jusqu'à 3 fois
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and data:
                    return Point(float(data[0]['lon']), float(data[0]['lat']))
            except requests.exceptions.RequestException as e:
                self.stderr.write(self.style.ERROR(f"Erreur API pour {commune_name}: {e}"))
                time.sleep(2)  # Pause pour éviter le blocage OSM

        return None  # Retourne None si aucune coordonnée trouvée

# class Command(BaseCommand):
#     help = "Importe les Régions Sanitaires et les Districts Sanitaires avec géolocalisation."
#
#     def handle(self, *args, **kwargs):
#         url = "https://fr.wikipedia.org/wiki/Liste_des_r%C3%A9gions_sanitaires_et_districts_sanitaires_de_C%C3%B4te_d%27Ivoire"
#         response = requests.get(url, timeout=10)  # Timeout plus long
#
#         if response.status_code != 200:
#             self.stderr.write(self.style.ERROR(f"Erreur Wikipédia : {response.status_code}"))
#             return
#
#         soup = BeautifulSoup(response.content, 'html.parser')
#
#         # ✅ 1. Extraire les Régions Sanitaires et les Districts
#         data = self.extract_regions_districts(soup)
#
#         # ✅ 2. Récupérer les coordonnées GPS avec OpenStreetMap (OSM)
#         with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
#             results = list(executor.map(self.get_coordinates, data["districts"]))
#
#         # ✅ 3. Insérer les données en base
#         self.save_to_db(data, results)
#
#         self.stdout.write(self.style.SUCCESS('Importation des Régions et Districts Sanitaires terminée.'))
#
#     def extract_regions_districts(self, soup):
#         """Parcourt le tableau Wikipédia pour extraire les Régions et Districts Sanitaires."""
#         data = {"regions": {}, "districts": []}
#
#         table = soup.find("table", {"class": "wikitable"})
#         if not table:
#             self.stderr.write(self.style.ERROR("Tableau non trouvé sur la page Wikipédia."))
#             return data
#
#         for row in table.find_all("tr")[1:]:  # Sauter l'en-tête
#             cols = row.find_all("td")
#             if len(cols) < 2:
#                 continue
#
#             region_name = cols[0].get_text(strip=True)
#             district_name = cols[1].get_text(strip=True)
#
#             if region_name not in data["regions"]:
#                 data["regions"][region_name] = region_name
#
#             data["districts"].append((region_name, district_name))
#
#         return data
#
#     def get_coordinates(self, district_data):
#         """Récupère les coordonnées GPS via OpenStreetMap"""
#         region_name, district_name = district_data
#         url = f"https://nominatim.openstreetmap.org/search?format=json&q={district_name}, Côte d'Ivoire"
#         headers = {"User-Agent": "DjangoApp/1.0 (contact@email.com)"}  # Remplace par ton email
#
#         for _ in range(3):  # Essayer jusqu'à 3 fois
#             try:
#                 response = requests.get(url, headers=headers, timeout=10)
#                 response.raise_for_status()
#                 data = response.json()
#
#                 if isinstance(data, list) and data:
#                     return region_name, district_name, Point(float(data[0]['lon']), float(data[0]['lat']))
#             except requests.exceptions.RequestException as e:
#                 self.stderr.write(self.style.ERROR(f"Erreur API pour {district_name}: {e}"))
#                 time.sleep(2)  # Pause pour éviter le blocage OSM
#
#         return region_name, district_name, None  # Retourne None si aucune coordonnée trouvée
#
#     def save_to_db(self, data, results):
#         """Insère les Régions et Districts Sanitaires dans la base de données."""
#         # ✅ Enregistrer les Régions
#         for region_name in data["regions"].values():
#             region, _ = HealthRegion.objects.get_or_create(name=region_name)
#
#         # ✅ Enregistrer les Districts avec géolocalisation
#         for region_name, district_name, geom in results:
#             region = HealthRegion.objects.filter(name=region_name).first()
#             if not region:
#                 self.stderr.write(self.style.ERROR(f"Région {region_name} introuvable."))
#                 continue
#
#             DistrictSanitaire.objects.get_or_create(
#                 nom=district_name,
#                 defaults={"region": region, "geom": geom},
#             )
#             self.stdout.write(self.style.SUCCESS(f'District "{district_name}" importé avec succès.'))