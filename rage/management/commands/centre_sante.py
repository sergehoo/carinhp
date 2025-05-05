import pandas as pd
import requests
from django.core.management.base import BaseCommand

from rage.models import PolesRegionaux, HealthRegion, DistrictSanitaire, TypeServiceSanitaire, ServiceSanitaire


# ------------Premier
# class Command(BaseCommand):
#     help = 'Importe les centres de santé depuis un fichier Excel et les géocode'
#
#     # Fonction pour remplacer les acronymes par leurs équivalents
#     def expand_acronyms(self, nom_centre):
#         acronyms = {
#             'CHR': 'Centre de Santé Régional',
#             'CHU': 'Centre de Santé Universitaire',
#             'HG': 'Hopital Général',
#             'CSR': 'Centre de Santé Régional',
#             'CSU': 'Centre de Sante Urbain'
#         }
#         # Remplacer chaque acronyme dans le nom du centre
#         for acronym, full_name in acronyms.items():
#             nom_centre = nom_centre.replace(acronym, full_name)
#         return nom_centre
#
#     def handle(self, *args, **kwargs):
#         file_path = 'static/centre_sante.xlsx'  # Chemin vers le fichier Excel
#         data = pd.read_excel(file_path, sheet_name='Feuil1')
#
#         # Utiliser Nominatim pour géocoder
#         geolocator = Nominatim(user_agent="geoapiExercises")
#
#         def geocode_location(nom_centre):
#             try:
#                 location = geolocator.geocode(nom_centre + ", Côte d'Ivoire")
#                 if location:
#                     return (location.latitude, location.longitude)
#                 return None
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Erreur lors du géocodage de {nom_centre}: {e}"))
#                 return None
#
#         # Boucler sur les centres de santé pour les ajouter à la base de données
#         for index, row in data.iterrows():
#             nom_centre = row['CENTRES DE SANTÉ']
#
#             # Remplacer les acronymes avant de faire le géocodage
#             nom_centre_expanded = self.expand_acronyms(nom_centre)
#
#             # Géocoder l'adresse
#             coords = geocode_location(nom_centre_expanded)
#
#             if coords:
#                 latitude, longitude = coords
#                 geom_point = f"POINT({longitude} {latitude})"
#
#                 # Chercher un district correspondant (à adapter si nécessaire)
#                 district_name = "Nom du district"  # Vous pouvez ajuster cette partie si des districts existent
#                 district, created = DistrictSanitaire.objects.get_or_create(nom=district_name)
#
#                 # Créer le ServiceSanitaire et l'enregistrer dans la base de données
#                 ServiceSanitaire.objects.create(
#                     nom=nom_centre,
#                     geom=geom_point,
#                     district=district,  # Associer le district si pertinent
#                     completeness="partiel",  # À ajuster selon vos besoins
#                     version=1  # Exemple de version initiale
#                 )
#
#                 self.stdout.write(self.style.SUCCESS(f"Centre {nom_centre} ajouté avec succès!"))
#             else:
#                 self.stdout.write(self.style.WARNING(f"Coordonnées introuvables pour {nom_centre}."))

#---------second fonctionnel
# class Command(BaseCommand):
#     help = 'Importe les centres de santé depuis un fichier Excel et les géocode'
#
#     # Fonction pour remplacer les acronymes par leurs équivalents
#     def expand_acronyms(self, nom_centre):
#         acronyms = {
#             'CHR': 'Centre de Santé Régional',
#             'CHU': 'Centre de Santé Universitaire',
#             'HG': 'Hopital Général',
#             'CSR': 'Centre de Santé Régional',
#             'CSU': 'Centre de Sante Urbain'
#         }
#         # Remplacer chaque acronyme dans le nom du centre
#         for acronym, full_name in acronyms.items():
#             nom_centre = nom_centre.replace(acronym, full_name)
#         return nom_centre
#
#     def handle(self, *args, **kwargs):
#         file_path = 'static/centre_sante.xlsx'  # Chemin vers le fichier Excel
#         data = pd.read_excel(file_path, sheet_name='Feuil1')
#
#         # Utiliser Nominatim pour géocoder
#         geolocator = Nominatim(user_agent="geoapiExercises")
#
#         def geocode_location(nom_centre):
#             try:
#                 location = geolocator.geocode(nom_centre + ", Côte d'Ivoire")
#                 if location:
#                     return (location.latitude, location.longitude)
#                 return None
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Erreur lors du géocodage de {nom_centre}: {e}"))
#                 return None
#
#         # Boucler sur les centres de santé pour les ajouter à la base de données
#         for index, row in data.iterrows():
#             nom_centre = row['CENTRES DE SANTÉ']
#
#             # Remplacer les acronymes avant de faire le géocodage
#             nom_centre_expanded = self.expand_acronyms(nom_centre)
#
#             # Géocoder l'adresse
#             coords = geocode_location(nom_centre_expanded)
#
#             # Si le géocodage a fonctionné, définir le geom
#             if coords:
#                 latitude, longitude = coords
#                 geom_point = f"POINT({longitude} {latitude})"
#             else:
#                 geom_point = None  # Si pas de coordonnées trouvées, laisser geom à None
#
#             # Chercher un district correspondant (vous pouvez ajuster cette partie si nécessaire)
#             district_name = "Nom du district"  # Remplacez par la logique de récupération du nom de district
#             district, created = DistrictSanitaire.objects.get_or_create(nom=district_name)
#
#             # Vérifier si le centre existe déjà
#             existing_service = ServiceSanitaire.objects.filter(nom=nom_centre, district=district).first()
#
#             if existing_service:
#                 # Si le service existe, mettre à jour ses coordonnées
#                 existing_service.geom = geom_point  # Mettre à jour geom
#                 existing_service.completeness = "partiel"  # Ajustez si nécessaire
#                 existing_service.save()
#                 self.stdout.write(self.style.WARNING(f"Centre {nom_centre} mis à jour avec succès!"))
#             else:
#                 # Créer le ServiceSanitaire et l'enregistrer dans la base de données
#                 ServiceSanitaire.objects.create(
#                     nom=nom_centre,
#                     geom=geom_point,  # Peut être None si géocodage échoué
#                     district=district,  # Associer le district si pertinent
#                     completeness="partiel",  # À ajuster selon vos besoins
#                     version=1  # Exemple de version initiale
#                 )
#                 self.stdout.write(self.style.SUCCESS(f"Centre {nom_centre} ajouté avec succès!"))

# class Command(BaseCommand):
#     help = 'Importe les centres de santé depuis un fichier Excel et les géocode'
#
#     # Fonction pour remplacer les acronymes par leurs équivalents
#     def expand_acronyms(self, nom_centre):
#         acronyms = {
#             'CHR': 'Centre de Santé Régional',
#             'CHU': 'Centre de Santé Universitaire',
#             'HG': 'Hopital Général',
#             'CSR': 'Centre de Santé Régional',
#             'CSU': 'Centre de Sante Urbain'
#         }
#         # Remplacer chaque acronyme dans le nom du centre
#         for acronym, full_name in acronyms.items():
#             nom_centre = nom_centre.replace(acronym, full_name)
#         return nom_centre
#
#     def handle(self, *args, **kwargs):
#         file_path = 'static/centre_sante.xlsx'  # Chemin vers le fichier Excel
#         data = pd.read_excel(file_path, sheet_name='Feuil1')
#
#         # Utiliser Nominatim pour géocoder
#         geolocator = Nominatim(user_agent="geoapiExercises")
#
#         def geocode_location(nom_centre):
#             try:
#                 location = geolocator.geocode(nom_centre + ", Côte d'Ivoire")
#                 if location:
#                     return (location.latitude, location.longitude)
#                 return None
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Erreur lors du géocodage de {nom_centre}: {e}"))
#                 return None
#
#         # Boucler sur les centres de santé pour les ajouter à la base de données
#         for index, row in data.iterrows():
#             nom_centre = row['CENTRES DE SANTÉ']
#             district_name = row['DISTRICT SANITAIRE']
#             region_name = row['Region sanitaire']
#             type_centre = row['TYPE']
#
#             # Remplacer les acronymes avant de faire le géocodage
#             nom_centre_expanded = self.expand_acronyms(nom_centre)
#
#             # Géocoder l'adresse
#             coords = geocode_location(nom_centre_expanded)
#
#             # Si le géocodage a fonctionné, définir le geom
#             if coords:
#                 latitude, longitude = coords
#                 geom_point = f"POINT({longitude} {latitude})"
#             else:
#                 geom_point = None  # Si pas de coordonnées trouvées, laisser geom à None
#
#             # Chercher ou créer la région sanitaire
#             region, created = HealthRegion.objects.get_or_create(name=region_name)
#
#             # Chercher ou créer le district sanitaire
#             district, created = DistrictSanitaire.objects.get_or_create(nom=district_name, region=region)
#
#             # Vérifier si le centre existe déjà
#             existing_service = ServiceSanitaire.objects.filter(nom=nom_centre, district=district).first()
#
#             if existing_service:
#                 # Si le service existe, mettre à jour ses coordonnées et informations
#                 existing_service.geom = geom_point  # Mettre à jour geom
#                 existing_service.completeness = "partiel"  # Ajustez si nécessaire
#                 existing_service.type = type_centre  # Mettre à jour le type de centre
#                 existing_service.save()
#                 self.stdout.write(self.style.WARNING(f"Centre {nom_centre} mis à jour avec succès!"))
#             else:
#                 # Créer le ServiceSanitaire et l'enregistrer dans la base de données
#                 ServiceSanitaire.objects.create(
#                     nom=nom_centre,
#                     geom=geom_point,  # Peut être None si géocodage échoué
#                     district=district,  # Associer le district
#                     type=type_centre,  # Enregistrer le type de centre
#                     completeness="partiel",  # À ajuster selon vos besoins
#                     version=1  # Exemple de version initiale
#                 )
#                 self.stdout.write(self.style.SUCCESS(f"Centre {nom_centre} ajouté avec succès!"))


#### Map Box

# class Command(BaseCommand):
#     help = 'Importe les centres de santé depuis un fichier Excel et les géocode avec Mapbox'
#
#     MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoib2dhaHNlcmdlIiwiYSI6ImNtMXc0dm91NjA0MW4ycXF5NzdtdThjeGYifQ.f1teke5Xjz5knfuLd0LpDA'  # Replace with your actual Mapbox access token
#
#     # Fonction pour remplacer les acronymes par leurs équivalents
#     def expand_acronyms(self, nom_centre):
#         acronyms = {
#             'CHR': 'Centre de Santé Régional',
#             'CHU': 'Centre de Santé Universitaire',
#             'HG': 'Hopital Général',
#             'CSR': 'Centre de Santé Régional',
#             'CSU': 'Centre de Sante Urbain'
#         }
#         for acronym, full_name in acronyms.items():
#             nom_centre = nom_centre.replace(acronym, full_name)
#         return nom_centre
#
#     def handle(self, *args, **kwargs):
#         file_path = 'static/centre_sante.xlsx'  # Chemin vers le fichier Excel
#         data = pd.read_excel(file_path, sheet_name='Feuil1')
#
#         def geocode_location(nom_centre):
#             try:
#                 url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{nom_centre}.json"
#                 params = {
#                     'access_token': self.MAPBOX_ACCESS_TOKEN,
#                     'country': 'CI',  # Côte d'Ivoire
#                     'autocomplete': True,
#                     'limit': 1
#                 }
#                 response = requests.get(url, params=params)
#                 response.raise_for_status()
#                 location = response.json()['features'][0]
#                 return (location['geometry']['coordinates'][1], location['geometry']['coordinates'][0])
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Erreur lors du géocodage de {nom_centre}: {e}"))
#                 return None
#
#         for index, row in data.iterrows():
#             nom_centre = row['CENTRES DE SANTÉ']
#             district_name = row['DISTRICT SANITAIRE']
#             region_name = row['Region sanitaire']
#             type_centre = row['TYPE']
#
#             nom_centre_expanded = self.expand_acronyms(nom_centre)
#             coords = geocode_location(nom_centre_expanded)
#
#             if coords:
#                 latitude, longitude = coords
#                 geom_point = f"POINT({longitude} {latitude})"
#             else:
#                 geom_point = None
#
#             region, created = HealthRegion.objects.get_or_create(name=region_name)
#             district, created = DistrictSanitaire.objects.get_or_create(nom=district_name, region=region)
#
#             existing_service = ServiceSanitaire.objects.filter(nom=nom_centre, district=district).first()
#
#             if existing_service:
#                 existing_service.geom = geom_point
#                 existing_service.completeness = "partiel"
#                 existing_service.type = type_centre
#                 existing_service.save()
#                 self.stdout.write(self.style.WARNING(f"Centre {nom_centre} mis à jour avec succès!"))
#             else:
#                 ServiceSanitaire.objects.create(
#                     nom=nom_centre,
#                     geom=geom_point,
#                     district=district,
#                     type=type_centre,
#                     completeness="partiel",
#                     version=1
#                 )
#                 self.stdout.write(self.style.SUCCESS(f"Centre {nom_centre} ajouté avec succès!"))

class Command(BaseCommand):
    help = 'Importe les centres de santé depuis un fichier Excel et les géocode avec Mapbox'

    MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoib2dhaHNlcmdlIiwiYSI6ImNtMXc0dm91NjA0MW4ycXF5NzdtdThjeGYifQ.f1teke5Xjz5knfuLd0LpDA'  # Remplacez par votre jeton d'accès Mapbox

    def expand_acronyms(self, nom_centre):
        acronyms = {
            'EPH': 'Établissement Public Hospitalier',
            'EPHN': 'Établissements Publics Hospitalier Nationaux',
            'EPHR': 'Établissements Publics Hospitaliers Régionaux',
            'EPHD': 'Établissements Publics Hospitaliers Départementaux',
            'ESPC': 'Établissements de Santé de Premier Contact',
            'CHR': 'Centre de Santé Régional',
            'CHU': 'Centre de Santé Universitaire',
            'HG': 'Hopital Général',
            'CSR': 'Centre de Santé Régional',
            'CSU': 'Centre de Sante Urbain'
        }
        for acronym, full_name in acronyms.items():
            nom_centre = nom_centre.replace(acronym, full_name)
        return nom_centre

    def handle(self, *args, **kwargs):
        file_path = 'static/centre_sante.xlsx'  # Chemin vers le fichier Excel
        data = pd.read_excel(file_path, sheet_name='Feuil1')

        def geocode_location(nom_centre):
            try:
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{nom_centre}.json"
                params = {
                    'access_token': self.MAPBOX_ACCESS_TOKEN,
                    'country': 'CI',  # Côte d'Ivoire
                    'autocomplete': True,
                    'limit': 1
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                location = response.json()['features'][0]
                return (location['geometry']['coordinates'][1], location['geometry']['coordinates'][0])
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors du géocodage de {nom_centre}: {e}"))
                return None

        for index, row in data.iterrows():
            nom_centre = row['CENTRES DE SANTÉ']
            district_name = row['DISTRICT SANITAIRE']
            region_name = row['Region sanitaire']
            pole_name = row['Pole regional']
            type_centre = row['TYPE']

            # Expand acronyms in centre name
            nom_centre_expanded = self.expand_acronyms(nom_centre)

            # Get or create PoleRegionaux
            pole, _ = PolesRegionaux.objects.get_or_create(name=pole_name)

            # Get or create HealthRegion linked to PoleRegionaux
            region, _ = HealthRegion.objects.get_or_create(name=region_name, poles=pole)

            # Get or create DistrictSanitaire linked to HealthRegion
            district, _ = DistrictSanitaire.objects.get_or_create(nom=district_name, region=region)

            # Geocode the centre if coordinates are missing
            coords = geocode_location(nom_centre_expanded)
            if coords:
                latitude, longitude = coords
                geom_point = f"POINT({longitude} {latitude})"
            else:
                geom_point = None

            # Check if ServiceSanitaire already exists and update or create
            existing_service = ServiceSanitaire.objects.filter(nom=nom_centre, district=district).first()

            # Get or create TypeServiceSanitaire instance
            type_service, created = TypeServiceSanitaire.objects.get_or_create(acronyme=type_centre)

            # Update or set the name based on the acronym
            type_service.nom = self.expand_acronyms(type_centre)  # Utiliser la méthode pour compléter le nom
            type_service.save()  # Enregistrer les modifications

            if existing_service:
                # Update existing service
                existing_service.geom = geom_point
                existing_service.completeness = "partiel"
                existing_service.type = type_service
                existing_service.save()
                self.stdout.write(self.style.WARNING(f"Centre {nom_centre} mis à jour avec succès!"))
            else:
                # Create new ServiceSanitaire
                ServiceSanitaire.objects.create(
                    nom=nom_centre,
                    geom=geom_point,
                    district=district,
                    type=type_service,
                    completeness="partiel",
                    version=1
                )
                self.stdout.write(self.style.SUCCESS(f"Centre {nom_centre} ajouté avec succès!"))

