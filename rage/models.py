import inspect
import json
import random
import string
import uuid
import datetime as dt
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import now, make_aware
from djgeojson.fields import PointField
from django.contrib.gis.db import models
# from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords
from tinymce.models import HTMLField
from datetime import datetime, date
from rage_INHP.services import synchroniser_avec_mpi
from rage_INHP.utils.phone import nettoyer_numero, formater_numero_local

import logging

logger = logging.getLogger(__name__)
# Create your models here.
# User = get_user_model()
Provenance_choices = [
    ('Urbaine', 'Urbaine'),
    ('Rurale', 'Rurale'),
]

Sexe_choices = [('Masculin', 'Masculin'), ('Feminin', 'Féminin')]

Resultat_choices = [
    ('POSITIF', 'POSITIF'),
    ('NEGATIF', 'NEGATIF'),
]

typeAnimal_choices = [
    ('Singe', 'Singe'),
    ('Chien', 'Chien'),
    ('Chat', 'Chat'),
    ('Autre', 'Autre'),

]

situation_matrimoniales_choices = [
    ('Celibataire', 'Celibataire'),
    ('Concubinage', 'Concubinage'),
    ('Marie', 'Marié'),
    ('Divorce', 'Divorcé'),
    ('Veuf', 'Veuf'),
    ('Autre', 'Autre'),
]
Goupe_sanguin_choices = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
]
Patient_statut_choices = [
    ('Admis', 'Admis'),
    ('Sorti', 'Sorti'),
    ('Transféré', 'Transféré'),
    ('Décédé', 'Décédé'),
    ('Sous observation', 'Sous observation'),
    ('Sous traitement', 'Sous traitement'),
    ('Chirurgie programmée', 'Chirurgie programmée'),
    ('En chirurgie', 'En chirurgie'),
    ('Récupération post-opératoire', 'Récupération post-opératoire'),
    ('USI', 'Unité de soins intensifs (USI)'),
    ('Urgence', 'Urgence'),
    ('Consultation externe', 'Consultation externe'),
    ('Réhabilitation', 'Réhabilitation'),
    ('En attente de diagnostic', 'En attente de diagnostic'),
    ('Traitement en cours', 'Traitement en cours'),
    ('Suivi programmé', 'Suivi programmé'),
    ('Consultation', 'Consultation'),
    ('Sortie en attente', 'Sortie en attente'),
    ('Isolement', 'Isolement'),
    ('Ambulantoire', 'Ambulantoire'),
    ('Aucun', 'Aucun')
]
NIVEAU_ETUDE_CHOICES = [
    ('Non scolarisé', 'Non scolarisé'),
    ('Préscolaire', 'Préscolaire'),
    ('Primaire', 'Primaire'),
    ('Secondaire', 'Secondaire'),
    ('Supérieur', 'Supérieur'),
]
ESPECE_CHOICES = [('Chien', 'Chien'), ('Chat', 'Chat'), ('Singe', 'Singe'),
                  ('Autre', 'Autre')]
STATUT_CHOICES = [('Connu', 'Connu'), ('Disponible', 'Disponible'), ('Disparu', 'Disparu'), ('Mort', 'Mort'),
                  ('Abattu', 'Abattu'), ('Errant', 'Errant')]

nbr_lesions_CHOICES = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8'),
    ('9', '9'),
    ('10', '10'),
    ('11-15', '11-15'),
    ('16-20', '16-20'),
    ('21 et plus', '21 et plus '),
]
OUI_NON_CHOICES = [
    # ('Inconnu', 'Inconnu'),
    ('Oui', 'Oui'),
    ('Non', 'Non'),

]

Retour_CHOICES = [
    ('AVIS', 'AVIS'),
    ('PROFILAXIE', 'PROFILAXIE'),
]
Membre_Superieur_CHOICES = [
    ('epaule', 'Épaule'),
    ('bras', 'Bras'),
    ('coude', 'Coude'),
    ('avant_bras', 'Avant-bras'),
    ('poignet', 'Poignet'),
    ('main', 'Main'),
    # ('doigts', 'Doigts'),
]
Tronc_CHOICES = [
    ('Zone Clavicule', 'Zone Clavicule'),
    ('Zone Sternum', 'Zone Sternum'),
    ('Zone Côtes', 'Zone Côtes'),
    ('Poitrine', 'Poitrine'),
    ('Seins', 'Seins'),
    ('Abdomen', 'Abdomen'),
    ('Dos', 'Dos'),
    # ('Flancs', 'Flancs'),
    # ('Muscles obliques', 'Muscles obliques'),
    # ('Omoplates', 'Omoplates'),
    # ('Colonne vertébrale thoracique', 'Colonne vertébrale thoracique'),
    # ('Colonne vertébrale lombaire', 'Colonne vertébrale lombaire'),
    # ('Muscles lombaires', 'Muscles lombaires'),
]
Tete_Cou_CHOICES = [
    ('Cuire chevelure', 'Cuire chevelure'),
    ('Front', 'Front'),
    ('Tempe', 'Tempe'),
    ('Yeux/paupieres', 'Yeux/paupieres'),
    ('Joues', 'Joues'),
    ('Nez', 'Nez'),
    ('Bouche/lèvres', 'Bouche/lèvres'),
    ('Oreilles', 'Oreilles'),
    ('Mâchoire', 'Mâchoire'),
    ('Menton', 'Menton'),
    ('Nuque', 'Nuque'),
    ('Cou', 'Cou'),

]
Membre_Inferieur_CHOICES = [
    ('Hanche', 'Hanche'),
    ('Fesse', 'Fesse'),
    ('Cuisse', 'Cuisse'),
    ('Genou', 'Genou'),
    ('Jambe', 'Jambe'),
    ('Cheville', 'Cheville'),

    ('Talon', 'Talon'),
    ('Pied', 'Pied'),
    # ('Plante du pied', 'Plante du pied'),
    # ('Dos du pied', 'Dos du pied'),
    # ('Orteils', 'Orteils'),
]

site_injection = [
    ('epaule', 'Épaule'),
    ('bras', 'Bras'),
    ('coude', 'Coude'),
    ('avant_bras', 'Avant-bras'),
    ('poignet', 'Poignet'),
    ('main', 'Main'),
    ('Zone Clavicule', 'Zone Clavicule'),
    ('Zone Sternum', 'Zone Sternum'),
    ('Zone Côtes', 'Zone Côtes'),
    ('Poitrine', 'Poitrine'),
    ('Seins', 'Seins'),
    ('Abdomen', 'Abdomen'),
    ('Dos', 'Dos'),
    ('Cuire chevelure', 'Cuire chevelure'),
    ('Front', 'Front'),
    ('Tempe', 'Tempe'),
    ('Yeux/paupieres', 'Yeux/paupieres'),
    ('Joues', 'Joues'),
    ('Nez', 'Nez'),
    ('Bouche/lèvres', 'Bouche/lèvres'),
    ('Oreilles', 'Oreilles'),
    ('Mâchoire', 'Mâchoire'),
    ('Menton', 'Menton'),
    ('Nuque', 'Nuque'),
    ('Cou', 'Cou'),

    ('Hanche', 'Hanche'),
    ('Fesse', 'Fesse'),
    ('Cuisse', 'Cuisse'),
    ('Genou', 'Genou'),
    ('Jambe', 'Jambe'),
    ('Cheville', 'Cheville'),

    ('Talon', 'Talon'),
    ('Pied', 'Pied'),
    ('Organes_genitaux_externe', 'Organes génitaux externes'),
]
Grossesse_SEMAINES_CHOICES = [
    ('1', 'Semaine 1'),
    ('2', 'Semaine 2'),
    ('3', 'Semaine 3'),
    ('4', 'Semaine 4'),
    ('5', 'Semaine 5'),
    ('6', 'Semaine 6'),
    ('7', 'Semaine 7'),
    ('8', 'Semaine 8'),
    ('9', 'Semaine 9'),
    ('10', 'Semaine 10'),
    ('11', 'Semaine 11'),
    ('12', 'Semaine 12'),
    ('13', 'Semaine 13'),
    ('14', 'Semaine 14'),
    ('15', 'Semaine 15'),
    ('16', 'Semaine 16'),
    ('17', 'Semaine 17'),
    ('18', 'Semaine 18'),
    ('19', 'Semaine 19'),
    ('20', 'Semaine 20'),
    ('21', 'Semaine 21'),
    ('22', 'Semaine 22'),
    ('23', 'Semaine 23'),
    ('24', 'Semaine 24'),
    ('25', 'Semaine 25'),
    ('26', 'Semaine 26'),
    ('27', 'Semaine 27'),
    ('28', 'Semaine 28'),
    ('29', 'Semaine 29'),
    ('30', 'Semaine 30'),
    ('31', 'Semaine 31'),
    ('32', 'Semaine 32'),
    ('33', 'Semaine 33'),
    ('34', 'Semaine 34'),
    ('35', 'Semaine 35'),
    ('36', 'Semaine 36'),
    ('37', 'Semaine 37'),
    ('38', 'Semaine 38'),
    ('39', 'Semaine 39'),
    ('40', 'Semaine 40'),
    ('41', 'Semaine 41'),
]

delai_CHOICES = [
    ('Immediat', 'Immediat'),
    ('J1', 'J1'),
    ('J3', 'J2'),
    ('J3', 'J3'),
    ('J3+', 'Au dela de J3'),

]

# Connaissance & attitude
conduite_CHOICES = [
    ('Abattage', 'Abattage'),
    ('Surveillance vétérinaire', 'Surveillance vétérinaire'),
    ('Ne rien faire', 'Ne rien faire'),
    ('Autre', 'Autre')
]
# mesure_CHOICES = [
#     ('Abattage des chiens', 'Abattage des chiens'),
#     ('Eviter d’avoir un chien', 'Eviter d’avoir un chien'),
#     ('Eviter la divagation des chiens ', 'Eviter la divagation des chiens'),
#     ('Organiser des séances de CCC', 'Organiser des séances de CCC'),
#     ('Vacciner la population contre la rage', 'Vacciner la population contre la rage'),
#     ('Sensibiliser particulièrement les propriétaires de chien',
#      'Sensibiliser particulièrement les propriétaires de chien'),
#     ('Intégrer rage dans le programme des cours au primaire', 'Intégrer rage dans le programme des cours au primaire'),
# ]
appreciation_CHOICES = [
    ('Elevé', 'Elevé'),
    ('Acceptable', 'Acceptable'),
    ('Pas à la portée de tous', 'Pas à la portée de tous'),
    ('Moins couteux', 'Moins couteux')
]

CARACASSE_CHOICES = [
    ('Carcasse disponible', 'Carcasse disponible'),
    ('Carcasse non disponible', 'Carcasse non disponible'),
    ('Non', 'Non')
]

STATUT_VACCINAL_CHOICES = [
    ('Animal non vacciné', 'Animal non vacciné'),
    ('Statut vaccinal Inconnu', 'Statut vaccinal Inconnu'),
    ('Non à jour', 'Non à jour'),
    ('Oui', 'Correctement vacciné')
]


class EmployeeUser(AbstractUser):
    ROLE_CHOICES = [
        ('National', 'National'),
        ('Regional', 'Régional'),
        ('DistrictSanitaire', 'District Sanitaire'),
        ('CentreAntirabique', 'Centre Antirabique'),
    ]
    CIVILITE_CHOICES = [
        ('Monsieur', 'Monsieur'),
        ('Madame', 'Madame'),
        ('Docteur', 'Docteur'),
        ('Professeur', 'Professeur'),
        ('Excellence', 'Excellence'),
        ('Honorable', 'Honorable'),
    ]
    civilite = models.CharField(max_length=10, choices=CIVILITE_CHOICES, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    fonction = models.CharField(max_length=255, blank=True, null=True)
    roleemployee = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CentreAntirabique')
    centre = models.ForeignKey('CentreAntirabique', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"

    def __str__(self):
        return f"{self.username} - {self.roleemployee}"


# Modèle des Pôles Régionaux
class PolesRegionaux(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Pole"


# Modèle des Régions Sanitaires
class HealthRegion(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    poles = models.ForeignKey(PolesRegionaux, on_delete=models.SET_NULL, null=True, blank=True, related_name='regions')

    def __str__(self):
        return f"{self.name}-{self.poles}"


# Modèle des Districts Sanitaires
class DistrictSanitaire(models.Model):
    nom = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    region = models.ForeignKey(HealthRegion, on_delete=models.CASCADE, null=True, blank=True, related_name='districts')
    geom = PointField(null=True, blank=True)
    geojson = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.nom} -> {self.region}'


class TypeServiceSanitaire(models.Model):
    nom = models.CharField(max_length=500, null=True, blank=True)
    acronyme = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.acronyme}"


class ServiceSanitaire(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    type = models.ForeignKey(TypeServiceSanitaire, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True, )
    geom = models.PointField(srid=4326, null=True, blank=True)
    upstream = models.CharField(max_length=255, null=True, blank=True)
    date_modified = models.DateTimeField(null=True, blank=True)
    source_url = models.URLField(max_length=500, null=True, blank=True)
    completeness = models.CharField(max_length=100, null=True, blank=True)
    uuid = models.UUIDField(null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    what3words = models.CharField(max_length=255, null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom}- {self.district} {self.geom}"


# Modèle des Centres Antirabiques
class CentreAntirabique(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='centres')
    geom = PointField(null=True, blank=True)
    upstream = models.CharField(max_length=255, null=True, blank=True)
    date_modified = models.DateTimeField(default=now, null=True, blank=True)
    source_url = models.URLField(max_length=500, null=True, blank=True)
    completeness = models.CharField(max_length=100, null=True, blank=True)
    uuid = models.UUIDField(unique=True, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    what3words = models.CharField(max_length=255, null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} - {self.district}"


# Modèle des Employés
class EmployeeProfile(models.Model):
    Sexe_choices = [('M', 'Masculin'), ('F', 'Féminin')]
    situation_matrimoniales_choices = [
        ('Célibataire', 'Célibataire'),
        ('Marié(e)', 'Marié(e)'),
        ('Divorcé(e)', 'Divorcé(e)'),
        ('Veuf(ve)', 'Veuf(ve)')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee")
    gender = models.CharField(choices=Sexe_choices, max_length=100, null=True, blank=True)
    situation_matrimoniale = models.CharField(choices=situation_matrimoniales_choices, max_length=100, null=True,
                                              blank=True)
    phone = models.CharField(null=True, blank=True, max_length=20, default='+22507070707')
    birthdate = models.DateField(null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, verbose_name="District Sanitaire",
                                 blank=True, null=True, related_name='employees')
    service = models.ForeignKey(CentreAntirabique, on_delete=models.CASCADE, verbose_name="Service Sanitaire",
                                blank=True, null=True, related_name='employees')
    job_title = models.CharField(null=True, blank=True, max_length=50, verbose_name="Titre du poste")

    slug = models.SlugField(null=True, blank=True, unique=True, editable=False, help_text="Slug field",
                            verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        permissions = (
            ("access_all", "Peut accéder à toutes les données"),
            ("access_region", "Peut accéder aux données régionales"),
            ("access_district", "Peut accéder aux données de district"),
            ("can_assign_roles", "Peut assigner des rôles aux employés"),
        )
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.user.first_name} {self.user.last_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.username)
        super().save(*args, **kwargs)


type_localite_choices = [
    ('Commune', 'Commune'),
    ('Village', 'Village'),
    ('Ville', 'Ville'),
    ('Quartier', 'Quartier'),
]
Pays_choice = [
    ('Afghanistan', 'Afghanistan'),
    ('Albanie', 'Albanie'),
    ('Algérie', 'Algérie'),
    ('Allemagne', 'Allemagne'),
    ('Andorre', 'Andorre'),
    ('Angola', 'Angola'),
    ('Antigua-et-Barbuda', 'Antigua-et-Barbuda'),
    ('Arabie saoudite', 'Arabie saoudite'),
    ('Argentine', 'Argentine'),
    ('Arménie', 'Arménie'),
    ('Australie', 'Australie'),
    ('Autriche', 'Autriche'),
    ('Azerbaïdjan', 'Azerbaïdjan'),
    ('Bahamas', 'Bahamas'),
    ('Bahreïn', 'Bahreïn'),
    ('Bangladesh', 'Bangladesh'),
    ('Barbade', 'Barbade'),
    ('Belgique', 'Belgique'),
    ('Belize', 'Belize'),
    ('Bénin', 'Bénin'),
    ('Bhoutan', 'Bhoutan'),
    ('Biélorussie', 'Biélorussie'),
    ('Birmanie', 'Birmanie'),
    ('Bolivie', 'Bolivie'),
    ('Bosnie-Herzégovine', 'Bosnie-Herzégovine'),
    ('Botswana', 'Botswana'),
    ('Brésil', 'Brésil'),
    ('Brunei', 'Brunei'),
    ('Bulgarie', 'Bulgarie'),
    ('Burkina Faso', 'Burkina Faso'),
    ('Burundi', 'Burundi'),
    ('Cambodge', 'Cambodge'),
    ('Cameroun', 'Cameroun'),
    ('Canada', 'Canada'),
    ('Cap-Vert', 'Cap-Vert'),
    ('Chili', 'Chili'),
    ('Chine', 'Chine'),
    ('Chypre', 'Chypre'),
    ('Colombie', 'Colombie'),
    ('Comores', 'Comores'),
    ('Congo (Brazzaville)', 'Congo (Brazzaville)'),
    ('Congo (RDC)', 'Congo (RDC)'),
    ('Corée du Nord', 'Corée du Nord'),
    ('Corée du Sud', 'Corée du Sud'),
    ('Costa Rica', 'Costa Rica'),
    ('Côte d’Ivoire', 'Côte d’Ivoire'),
    ('Croatie', 'Croatie'),
    ('Cuba', 'Cuba'),
    ('Danemark', 'Danemark'),
    ('Djibouti', 'Djibouti'),
    ('Dominique', 'Dominique'),
    ('Égypte', 'Égypte'),
    ('Émirats arabes unis', 'Émirats arabes unis'),
    ('Équateur', 'Équateur'),
    ('Érythrée', 'Érythrée'),
    ('Espagne', 'Espagne'),
    ('Estonie', 'Estonie'),
    ('Eswatini', 'Eswatini'),
    ('États-Unis', 'États-Unis'),
    ('Éthiopie', 'Éthiopie'),
    ('Fidji', 'Fidji'),
    ('Finlande', 'Finlande'),
    ('France', 'France'),
    ('Gabon', 'Gabon'),
    ('Gambie', 'Gambie'),
    ('Géorgie', 'Géorgie'),
    ('Ghana', 'Ghana'),
    ('Grèce', 'Grèce'),
    ('Grenade', 'Grenade'),
    ('Guatemala', 'Guatemala'),
    ('Guinée', 'Guinée'),
    ('Guinée équatoriale', 'Guinée équatoriale'),
    ('Guinée-Bissau', 'Guinée-Bissau'),
    ('Guyana', 'Guyana'),
    ('Haïti', 'Haïti'),
    ('Honduras', 'Honduras'),
    ('Hongrie', 'Hongrie'),
    ('Inde', 'Inde'),
    ('Indonésie', 'Indonésie'),
    ('Irak', 'Irak'),
    ('Iran', 'Iran'),
    ('Irlande', 'Irlande'),
    ('Islande', 'Islande'),
    ('Israël', 'Israël'),
    ('Italie', 'Italie'),
    ('Jamaïque', 'Jamaïque'),
    ('Japon', 'Japon'),
    ('Jordanie', 'Jordanie'),
    ('Kazakhstan', 'Kazakhstan'),
    ('Kenya', 'Kenya'),
    ('Kirghizistan', 'Kirghizistan'),
    ('Kiribati', 'Kiribati'),
    ('Koweït', 'Koweït'),
    ('Laos', 'Laos'),
    ('Lesotho', 'Lesotho'),
    ('Lettonie', 'Lettonie'),
    ('Liban', 'Liban'),
    ('Libéria', 'Libéria'),
    ('Libye', 'Libye'),
    ('Liechtenstein', 'Liechtenstein'),
    ('Lituanie', 'Lituanie'),
    ('Luxembourg', 'Luxembourg'),
    ('Macédoine du Nord', 'Macédoine du Nord'),
    ('Madagascar', 'Madagascar'),
    ('Malaisie', 'Malaisie'),
    ('Malawi', 'Malawi'),
    ('Maldives', 'Maldives'),
    ('Mali', 'Mali'),
    ('Malte', 'Malte'),
    ('Maroc', 'Maroc'),
    ('Îles Marshall', 'Îles Marshall'),
    ('Maurice', 'Maurice'),
    ('Mauritanie', 'Mauritanie'),
    ('Mexique', 'Mexique'),
    ('Micronésie', 'Micronésie'),
    ('Moldavie', 'Moldavie'),
    ('Monaco', 'Monaco'),
    ('Mongolie', 'Mongolie'),
    ('Monténégro', 'Monténégro'),
    ('Mozambique', 'Mozambique'),
    ('Namibie', 'Namibie'),
    ('Nauru', 'Nauru'),
    ('Népal', 'Népal'),
    ('Nicaragua', 'Nicaragua'),
    ('Niger', 'Niger'),
    ('Nigéria', 'Nigéria'),
    ('Norvège', 'Norvège'),
    ('Nouvelle-Zélande', 'Nouvelle-Zélande'),
    ('Oman', 'Oman'),
    ('Ouganda', 'Ouganda'),
    ('Ouzbékistan', 'Ouzbékistan'),
    ('Pakistan', 'Pakistan'),
    ('Palaos', 'Palaos'),
    ('Palestine', 'Palestine'),
    ('Panama', 'Panama'),
    ('Papouasie-Nouvelle-Guinée', 'Papouasie-Nouvelle-Guinée'),
    ('Paraguay', 'Paraguay'),
    ('Pays-Bas', 'Pays-Bas'),
    ('Pérou', 'Pérou'),
    ('Philippines', 'Philippines'),
    ('Pologne', 'Pologne'),
    ('Portugal', 'Portugal'),
    ('Qatar', 'Qatar'),
    ('Roumanie', 'Roumanie'),
    ('Royaume-Uni', 'Royaume-Uni'),
    ('Russie', 'Russie'),
    ('Rwanda', 'Rwanda'),
    ('Saint-Christophe-et-Niévès', 'Saint-Christophe-et-Niévès'),
    ('Sainte-Lucie', 'Sainte-Lucie'),
    ('Saint-Marin', 'Saint-Marin'),
    ('Saint-Vincent-et-les-Grenadines', 'Saint-Vincent-et-les-Grenadines'),
    ('Salomon', 'Salomon'),
    ('Salvador', 'Salvador'),
    ('Samoa', 'Samoa'),
    ('São Tomé-et-Príncipe', 'São Tomé-et-Príncipe'),
    ('Sénégal', 'Sénégal'),
    ('Serbie', 'Serbie'),
    ('Seychelles', 'Seychelles'),
    ('Sierra Leone', 'Sierra Leone'),
    ('Singapour', 'Singapour'),
    ('Slovaquie', 'Slovaquie'),
    ('Slovénie', 'Slovénie'),
    ('Somalie', 'Somalie'),
    ('Soudan', 'Soudan'),
    ('Soudan du Sud', 'Soudan du Sud'),
    ('Sri Lanka', 'Sri Lanka'),
    ('Suède', 'Suède'),
    ('Suisse', 'Suisse'),
    ('Suriname', 'Suriname'),
    ('Syrie', 'Syrie'),
    ('Tadjikistan', 'Tadjikistan'),
    ('Tanzanie', 'Tanzanie'),
    ('Tchad', 'Tchad'),
    ('République tchèque', 'République tchèque'),
    ('Thaïlande', 'Thaïlande'),
    ('Timor oriental', 'Timor oriental'),
    ('Togo', 'Togo'),
    ('Tonga', 'Tonga'),
    ('Trinité-et-Tobago', 'Trinité-et-Tobago'),
    ('Tunisie', 'Tunisie'),
    ('Turkménistan', 'Turkménistan'),
    ('Turquie', 'Turquie'),
    ('Tuvalu', 'Tuvalu'),
    ('Ukraine', 'Ukraine'),
    ('Uruguay', 'Uruguay'),
    ('Vanuatu', 'Vanuatu'),
    ('Vatican', 'Vatican'),
    ('Venezuela', 'Venezuela'),
    ('Viêt Nam', 'Viêt Nam'),
    ('Yémen', 'Yémen'),
    ('Zambie', 'Zambie'),
    ('Zimbabwe', 'Zimbabwe'),
]


class Commune(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True, unique=True, db_index=True)
    type = models.CharField(choices=type_localite_choices, max_length=100, null=True, blank=True)
    population = models.CharField(max_length=100, null=True, blank=True)
    is_in = models.CharField(max_length=255, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True, )
    geom = models.PointField(null=True, blank=True)

    def __str__(self):
        if self.district:
            return f"{self.name}"
        return self.name or "Commune sans nom"


class Patient(models.Model):
    nature_acompagnateur_CHOICES = [
        ('Pere', 'Père'),
        ('Mere', 'Mère'),
        ('Oncle', 'Oncle'),
        ('Tante', 'Tante'),
        ('Frere', 'Frère'),
        ('Soeur', 'Soeur'),
        ('Cousin', 'Cousin'),
        ('Cousine', 'Cousine'),
        ('Connaissance du quartier', 'Connaissance du quartier'),
        ('Voisin du quartier', 'Voisin du quartier'),
        ('Propriétaire animal', 'Propriétaire animal')
    ]
    code_patient = models.CharField(max_length=225, blank=True, unique=True, editable=False, db_index=True)
    mpi_upi = models.UUIDField(null=True, blank=True, unique=True, db_index=True)
    nom = models.CharField(max_length=225, db_index=True)
    prenoms = models.CharField(max_length=225, db_index=True)
    contact = PhoneNumberField(region='CI', blank=True, null=True, db_index=True)

    date_naissance = models.DateField(db_index=True)
    sexe = models.CharField(max_length=10, choices=Sexe_choices, )
    provenance = models.CharField(max_length=10, choices=Provenance_choices, blank=True, null=True)
    num_cmu = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    cni_num = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    cni_nni = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    secteur_activite = models.CharField(max_length=200, null=True, blank=True)
    niveau_etude = models.CharField(choices=NIVEAU_ETUDE_CHOICES, max_length=500, null=True, blank=True)
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    quartier = models.CharField(max_length=255, blank=True, null=True)
    village = models.CharField(max_length=255, blank=True, null=True)
    poids = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(250)],
        help_text="Poids du patient (1 à 250 kg)",
        null=True, blank=True
    )

    centre_ar = models.ForeignKey(CentreAntirabique, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.SET_NULL, null=True, blank=True)
    proprietaire_animal = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, default='Non',
                                           db_index=True)
    typeanimal = models.CharField(choices=typeAnimal_choices, max_length=255, blank=True, null=True)
    autretypeanimal = models.CharField(max_length=255, blank=True, null=True)

    patient_mineur = models.BooleanField(default=False)
    accompagnateur = models.CharField(max_length=255, blank=True, null=True)

    accompagnateurcontact = PhoneNumberField(region='CI', blank=True, null=True)

    accompagnateur_adresse = models.CharField(max_length=255, blank=True, null=True)
    accompagnateur_nature = models.CharField(choices=nature_acompagnateur_CHOICES, max_length=255, blank=True,
                                             null=True)
    accompagnateur_niveau_etude = models.CharField(choices=NIVEAU_ETUDE_CHOICES, max_length=255, blank=True, null=True)

    status = models.CharField(choices=Patient_statut_choices, max_length=100, default='Aucun', null=True, blank=True)
    gueris = models.BooleanField(default=False)
    decede = models.BooleanField(default=False)

    cause_deces = models.TextField(blank=True, null=True)
    date_deces = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=now)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        permissions = (('voir_patient', 'Peut voir patient'),)

    def save(self, *args, **kwargs):
        # Nettoyage des numéros avant sauvegarde
        self.contact = nettoyer_numero(self.contact)
        self.accompagnateurcontact = nettoyer_numero(self.accompagnateurcontact)

        # Générer un code_patient unique constitué de chiffres et de caractères alphabétiques
        if not self.code_patient:
            # Générer 16 chiffres à partir de l'UUID
            digits = ''.join(filter(str.isdigit, str(uuid.uuid4().int)))[:8]
            # Générer 4 caractères alphabétiques aléatoires
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            # Combiner les chiffres et les lettres pour former le code_patient
            self.code_patient = digits + letters

        # 🔁 Synchronisation MPI
        if not self.mpi_upi:  # seulement si pas encore synchronisé
            try:
                self.mpi_upi = synchroniser_avec_mpi(self)
            except Exception as e:
                print(f"⚠️ Erreur MPI: {e}")

        super(Patient, self).save(*args, **kwargs)

    @property
    def contact_formatte(self):
        return formater_numero_local(self.contact)

    @property
    def dose_immunoglobuline_ui(self):
        """
        Calcule la dose à injecter en UI : 40 UI par kg
        """
        if self.poids:
            return round(Decimal(self.poids) * Decimal('40.0'), 2)
        return None

    @property
    def accompagnateurcontact_formatte(self):
        return formater_numero_local(self.accompagnateurcontact)

    @property
    def calculate_age(self):
        if self.date_naissance:
            today = date.today()
            age = today.year - self.date_naissance.year - (
                    (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
            return age
        else:
            return None

    @property
    def latest_constante(self):
        return self.constantes.order_by('-created_at').first()

    def __str__(self):
        return f'{self.nom} {self.prenoms} -- {self.code_patient}'


class Animal(models.Model):
    prorietaire = models.ForeignKey(Patient, on_delete=models.CASCADE)
    espece = models.CharField(max_length=20, choices=ESPECE_CHOICES)
    precisions = models.CharField(max_length=255, blank=True, null=True)
    domestique = models.BooleanField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)
    proprietaire_nom = models.CharField(max_length=255, blank=True, null=True)
    proprietaire_contact = models.CharField(max_length=255, blank=True, null=True)
    statut_vaccinal = models.CharField(max_length=50, blank=True, null=True)
    date_derniere_vaccination = models.DateField(blank=True, null=True)

    gueris = models.BooleanField(default=False)
    decede = models.BooleanField(default=False)

    cause_deces = models.TextField(blank=True, null=True)
    date_deces = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=now)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.espece} - {self.statut}"


class Preexposition(models.Model):
    # Motif de vaccination
    client = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    codeexpo = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    voyage = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    mise_a_jour = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    protection_rage = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    chien_voisin = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    chiens_errants = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    autre = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    autre_motif = models.CharField(blank=True, null=True, db_index=True)

    # Information sur la vaccination
    tele = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    radio = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', db_index=True)
    sensibilisation = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    proche = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    presse = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    passage_car = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    diff_canal = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    canal_infos = models.TextField(blank=True, null=True)

    aime_animaux = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    type_animal_aime = models.CharField(choices=ESPECE_CHOICES, max_length=255, blank=True, null=True)
    conduite_animal_mordeur = models.CharField(choices=conduite_CHOICES, max_length=255, null=True, blank=True)

    connait_protocole_var = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non')
    dernier_var_animal_type = models.CharField(max_length=255, blank=True, null=True)
    dernier_var_animal_date = models.DateField(blank=True, null=True)
    mesures_elimination_rage = models.CharField(null=True, blank=True)
    appreciation_cout_var = models.CharField(choices=appreciation_CHOICES, max_length=255, null=True, blank=True)
    protocole_vaccination = models.ForeignKey('ProtocoleVaccination', on_delete=models.CASCADE, null=True, blank=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="employeer")
    created_at = models.DateTimeField(auto_now_add=True)
    fin_protocole = models.CharField(max_length=3, choices=OUI_NON_CHOICES, default='Non', null=True, blank=True, )

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.codeexpo:
            self.codeexpo = f"PREP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class PostExposition(models.Model):
    # Identification du patient
    client = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, db_index=True,
                               related_name="patientpep")

    # Exposition
    date_exposition = models.DateField(db_index=True)
    lieu_exposition = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    exposition_commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    exposition_quartier = models.CharField(max_length=255, null=True, blank=True)

    circonstance = models.CharField(
        max_length=255,
        choices=[
            ('Attaque provoquée', 'Attaque provoquée'),
            ('Agression', 'Agression'),
            ('Contact patient suspect/positif de rage ', 'Contact patient suspect/positif de rage'),
            # ('Attaque collective', 'Attaque collective'),
            # ('Professionnel', 'Professionnel')
        ],
        null=True, blank=True
    )
    attaque_provoquee = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True)
    agression = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True)
    attaque_collective = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    professionnel = models.CharField(max_length=10, choices=OUI_NON_CHOICES)

    type_professionnel = models.CharField(
        max_length=50,
        choices=[('Manipulation / Soins', 'Manipulation / Soins'), ('Laboratoire', 'Laboratoire')],
        null=True, blank=True
    )

    morsure = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    griffure = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    lechage_saine = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    lechage_lesee = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    contactanimalpositif = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    contactpatientpositif = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    autre = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    autre_nature_exposition = models.CharField(max_length=10, null=True, blank=True, db_index=True)

    # Siège de l’exposition
    tete_cou = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    preciser_tetecou = models.JSONField(null=True, blank=True)
    membre_superieur = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)

    preciser_membre_sup = models.JSONField(null=True, blank=True)
    tronc = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    preciser_tronc = models.JSONField(null=True, blank=True)
    organes_genitaux_externes = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    membre_inferieur = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    preciser_membre_inf = models.JSONField(null=True, blank=True)
    saignement_immediat = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    vetements_presents = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    dechires = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)

    siege_exposition = models.TextField(null=True, blank=True)
    vetements_dechires = models.CharField(max_length=10, choices=OUI_NON_CHOICES, blank=True, null=True, db_index=True)
    nbrlesions = models.CharField(max_length=300, choices=nbr_lesions_CHOICES, null=True, blank=True)

    # Animal
    espece = models.CharField(
        max_length=50,
        choices=[('Chien', 'Chien'), ('Chat', 'Chat'), ('Singe', 'Singe'), ('Chauve-souris', 'Chauve-souris'),
                 ('Autre', 'Autre')],
        null=True, blank=True
    )

    autre_animal = models.CharField(max_length=255, null=True, blank=True)
    domestic = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)

    connais_proprio = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    nom_proprietaire = models.CharField(max_length=255, null=True, blank=True)
    contact_proprietaire = models.CharField(max_length=255, null=True, blank=True)
    info_proprietaire = models.CharField(max_length=50, choices=OUI_NON_CHOICES, null=True, blank=True)
    retour_info_proprietaire = models.CharField(max_length=50, choices=OUI_NON_CHOICES, null=True, blank=True)

    avis = models.BooleanField(default=False)
    convocation = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    prophylaxie = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)

    correctement_vaccine = models.CharField(max_length=50, choices=STATUT_VACCINAL_CHOICES, null=True, blank=True,
                                            db_index=True)
    non_vaccine = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    nonajours = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    vacinconnu = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    carnet_Vaccin = models.FileField(upload_to='carnets/', null=True, blank=True)

    connu = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    disponible = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    errant = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    disparu = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    mort = models.CharField(max_length=30, choices=CARACASSE_CHOICES, null=True, blank=True, db_index=True)
    abatu = models.CharField(max_length=30, choices=CARACASSE_CHOICES, null=True, blank=True, db_index=True)
    autre_statut = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    autre_statut_precis = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    date_derniere_vaccination = models.DateField(null=True, blank=True)

    # Gravité et Surveillance
    gravite_oms = models.CharField(max_length=10, choices=[('I', 'I'), ('II', 'II'), ('III', 'III')], null=True,
                                   blank=True)
    surveillance_veterinaire = models.CharField(max_length=10, null=True, blank=True, choices=OUI_NON_CHOICES,
                                                db_index=True)

    certificat = models.CharField(max_length=50, null=True, blank=True)
    piece_jointe = models.FileField(upload_to="certifiatVaccin", null=True, blank=True)
    date_etablissement = models.DateField(null=True, blank=True)
    Date_depot_car = models.DateField(null=True, blank=True)
    Decision_de_poursuite_tar = models.CharField(max_length=50, null=True, blank=True)
    Decision_d_arrete_tar = models.CharField(max_length=50, null=True, blank=True)

    # Diagnostic et Prise en charge
    prelevement_animal = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    diagnostic_laboratoire = models.CharField(max_length=50, choices=[('Positif', 'Positif'), ('Negatif', 'Négatif')],
                                              null=True, blank=True)
    date_diagnostic = models.DateField(null=True, blank=True)

    # Dossier Médical
    antecedents_medicaux = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    details_antecedents = models.JSONField(null=True, blank=True)
    probleme_coagulation = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    details_problemes = models.JSONField(null=True, blank=True)
    immunodepression = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    details_immo = models.JSONField(null=True, blank=True)
    grossesse = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    details_grosesse = models.CharField(max_length=10, null=True, blank=True, choices=Grossesse_SEMAINES_CHOICES,
                                        db_index=True)
    allergies = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    details_allergies = models.JSONField(null=True, blank=True)
    traitements_en_cours = models.CharField(max_length=10, choices=OUI_NON_CHOICES, db_index=True)
    details_traitements = models.TextField(null=True, blank=True)

    # Antécédents vaccinaux
    vat_dernier_injection = models.DateField(null=True, blank=True)
    vat_rappel = models.DateField(null=True, blank=True)
    vat_lot = models.CharField(max_length=255, null=True, blank=True)
    vaccin_antirabique = models.CharField(max_length=10, null=True, blank=True, choices=OUI_NON_CHOICES, db_index=True)
    carnet_vaccinal = models.FileField(upload_to='carnets/', null=True, blank=True)
    carnet_vaccinal_verso = models.FileField(upload_to='carnets/', null=True, blank=True)

    # Prise en charge
    lavage_plaies = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    desinfection_plaies = models.CharField(max_length=10, null=True, blank=True, choices=OUI_NON_CHOICES, db_index=True)
    delai_apres_exposition = models.CharField(max_length=50, choices=delai_CHOICES, null=True, blank=True)
    delai_apres_desinfection = models.CharField(max_length=50, choices=delai_CHOICES, null=True, blank=True)
    produits_utilises = models.CharField(max_length=50, null=True, blank=True)

    sutures = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    serum_antitetanique = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)

    antibiotiques = models.CharField(max_length=10, choices=OUI_NON_CHOICES, null=True, blank=True, db_index=True)
    details_antibiotiques = models.TextField(null=True, blank=True)

    # Vaccination Antirabique
    delai_traitement = models.TextField(null=True, blank=True)
    immunoglobulines = models.TextField(null=True, blank=True)

    details_vaccination = models.TextField(null=True, blank=True)

    # Sérologie
    serologie = models.BooleanField(default=False)
    details_serologie = models.TextField(null=True, blank=True)

    # Issue de la prise en charge
    issue = models.CharField(max_length=50,
                             choices=[('Perdu de vue', 'Perdu de vue'), ('Arrêté', 'Arrêté'), ('Terminé', 'Terminé')],
                             null=True, blank=True)
    observance = models.CharField(max_length=10, null=True, blank=True, choices=OUI_NON_CHOICES, db_index=True)
    evolution_patient = models.CharField(max_length=50, choices=[('Vivant', 'Vivant'), ('Décédé', 'Décédé'),
                                                                 ('Non précisé', 'Non précisé')], null=True, blank=True)
    cause_deces = models.TextField(null=True, blank=True)
    date_deces = models.DateField(null=True, blank=True)
    protocole_vaccination = models.ForeignKey('ProtocoleVaccination', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    temps_saisie = models.PositiveIntegerField(null=True, blank=True,
                                               help_text="Temps de saisie du formulaire (en secondes)")
    history = HistoricalRecords()

    def determiner_gravite_oms(self):
        # Catégorie III - Risque grave
        if (self.saignement_immediat == "Oui" or
                self.tete_cou == "Oui" or
                self.organes_genitaux_externes == "Oui" or
                self.espece == "Chauve-souris"):
            return "III"

        # Catégorie II - Risque modéré
        if (self.griffure == "Oui" or
                self.lechage_lesee == "Oui" or
                self.contactpatientpositif == "Oui"):
            return "II"

        # Catégorie I - Pas de risque
        if self.lechage_saine == "Oui":
            return "I"

        return None

    def save(self, *args, **kwargs):

        if not self.gravite_oms:
            self.gravite_oms = self.determiner_gravite_oms()

        # Only set these fields if they're not already set
        if self.client and not self.connais_proprio and self.client.accompagnateur_nature == 'Propriétaire animal':
            self.connais_proprio = "Oui"
            self.retour_info_proprietaire = "Oui"
            self.avis = True

        if self.client and not self.nom_proprietaire and self.client.accompagnateur:
            self.nom_proprietaire = self.client.accompagnateur

        if self.client and not self.contact_proprietaire and self.client.accompagnateurcontact:
            self.contact_proprietaire = self.client.accompagnateurcontact

        # Use force_insert or force_update if needed
        if 'force_insert' not in kwargs and 'force_update' not in kwargs:
            if self.pk:
                kwargs['force_update'] = True
            else:
                kwargs['force_insert'] = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.nom} {self.client.prenoms} - {self.date_exposition}"


class RageHumaineNotification(models.Model):
    # Identification du patient
    client = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True,
                               related_name="notifications_rage", db_index=True)
    # Informations générales
    date_notification = models.DateField("Date de la notification", db_index=True, null=True, blank=True)
    hopital = models.ForeignKey("ServiceSanitaire", on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    service = models.CharField("Service", max_length=100, null=True, blank=True)
    district_declarant = models.ForeignKey("DistrictSanitaire", on_delete=models.SET_NULL,
                                           related_name='district_declarant', null=True, blank=True, db_index=True)
    agent_declarant = models.CharField("Agent déclarant", max_length=100, null=True, blank=True)
    adresse = models.CharField("Adresse", max_length=200, null=True, blank=True)
    telephone = models.CharField("Téléphone", max_length=20, null=True, blank=True)
    fonction = models.CharField("fonction", max_length=20, null=True, blank=True)
    email = models.EmailField("E-mail", null=True, blank=True)

    # Origine possible de la contamination
    exposition = models.ForeignKey(PostExposition, on_delete=models.CASCADE, null=True, blank=True, db_index=True)

    date_exposition = models.DateField("Date de l’exposition")
    pays = models.CharField("Pays", choices=Pays_choice, max_length=100)
    lieu_exposition = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    district_expo = models.ForeignKey("DistrictSanitaire", on_delete=models.SET_NULL,
                                      related_name='district_dexposition', null=True, blank=True, db_index=True)

    commune = models.CharField("Commune", max_length=100)
    localite = models.CharField("Localite", max_length=100)

    nature_exposition = models.CharField("Nature de l’exposition", max_length=20, choices=[
        ('Morsure', 'Morsure'), ('Griffure', 'Griffure'), ('Léchage', 'Léchage'),
        ('Simple manipulation', 'Simple manipulation'), ('Autres', 'Autres')
    ])
    autre_nature_exposition = models.CharField("Autres nature", max_length=120, )

    siege_lesion = models.CharField("Siège de la lésion", max_length=20, choices=[
        ('Tête et cou', 'Tête et cou'), ('Membre supérieur', 'Membre supérieur'),
        ('Tronc', 'Tronc'), ('OGE', 'OGE'), ('Membre inférieur', 'Membre inférieur')
    ])
    precision_siege = models.CharField("Précision siège", max_length=100, blank=True, null=True)
    categorie_lesion = models.CharField("Catégorie de la lésion", max_length=10,
                                        choices=[('I', 'I'), ('II', 'II'), ('III', 'III')])
    animal_responsable = models.CharField("Animal responsable", max_length=10,
                                          choices=[('Chien', 'Chien'), ('Chat', 'Chat'), ('Autre', 'Autre')])
    precis_animal_responsable = models.CharField("Préciser animal responsable", max_length=100, blank=True, null=True)
    animal_suspect_rage = models.CharField("Animal suspect de rage", max_length=50,
                                           choices=[('Oui', 'Oui'), ('Non', 'Non'), ('Ne sait pas', 'Ne sait pas')])
    devenir_animal = models.CharField("Devenir de l’animal", max_length=10,
                                      choices=[('Vivant', 'Vivant'), ('Errant', 'Errant'), ('Mort', 'Mort'),
                                               ('Abattu', 'Abattu'), ('Disparu', 'Disparu')])
    prelevement_animal = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    resultat_analyse = models.CharField("Résultat analyse", max_length=10,
                                        choices=[('Positif', 'Positif'), ('Negatif', 'Négatif')],
                                        blank=True, null=True)
    labo_pathologie_animale = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    autres_labos = models.CharField("Autres laboratoires", max_length=100, blank=True, null=True)

    # Prophylaxie post-exposition
    soins_locaux = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    desinfection = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    produit_desinfection = models.CharField("Produit utilisé pour la désinfection", max_length=100, blank=True,
                                            null=True)

    serotherapie_antitetanique = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    dateserotherapie = models.DateField("Date de la sérothérapie antitétanique ", blank=True, null=True)
    vaccination_antirabique = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    date_debut_vaccination = models.DateField("Date de début de la vaccination antirabique", blank=True, null=True)
    protocole_vaccination = models.CharField("Protocole utilisé", max_length=10,
                                             choices=[('Essen', 'Essen'), ('Zagreb', 'Zagreb'), ('ID', 'ID')],
                                             blank=True, null=True)
    nbr_dose_recu = models.CharField("Nombre de dose recu", max_length=10,
                                     choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')],
                                     blank=True, null=True)
    lieu_vaccination = models.CharField(max_length=100)
    raison_absence_vaccination = models.CharField("Raison d'absence de vaccination", max_length=30,
                                                  choices=[('Ignorance', 'Ignorance'), ('Négligence', 'Négligence'),
                                                           ('Difficultés financières', 'Difficultés financières'),
                                                           ('Manque de temps', 'Manque de temps'),
                                                           ('Refus soutiennpropriétaire', 'Refus soutiennpropriétaire'),
                                                           ('Centre de vaccination éloigné',
                                                            'Centre de vaccination éloigné'),
                                                           ('Motif Inconnu ', 'Motif Inconnu '), ('Autre', 'Autre')],
                                                  blank=True, null=True)
    autreraison = models.CharField("Préciser la raison", max_length=150, blank=True, null=True)

    # Période de la maladie
    date_premiers_signes = models.DateField("Date des premiers signes", blank=True, null=True)
    trouble_comportement = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    hyper_salivation = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    hydrophobie = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    aerophobie = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    photophobie = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    troubles_respiratoires = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    coma = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    agitation = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    hospitalisation = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    date_hospitalisation = models.DateField("Date d’hospitalisation", blank=True, null=True)
    lieu_hospitalisation = models.CharField(max_length=50)
    evolution = models.CharField("Évolution", max_length=20,
                                 choices=[('Encore malade', 'Encore malade'), ('Décédé(e)', 'Décédé(e)')], blank=True,
                                 null=True)
    prelevement_patient = models.CharField(max_length=10, choices=OUI_NON_CHOICES)
    type_echantillon = models.CharField("Préciser le type d'échantillon", max_length=30,
                                        choices=[('Salive', 'Salive'), ('Peau', 'Peau')], blank=True, null=True)
    date_prelevement = models.DateField("Date de prélèvement", blank=True, null=True)

    date_deces = models.DateField("Date de décès", blank=True, null=True)
    lieu_deces = models.CharField("Lieu de décès", max_length=100,
                                  choices=[('Hôpital', 'Hôpital'), ('Domicile', 'Domicile'),
                                           ('Chez un guérisseur', 'Chez un guérisseur'),
                                           ('dans un camp de prière', 'dans un camp de prière'),
                                           ('au cours du transfert', 'au cours du transfert'),
                                           ('Autre lieu de décès', 'Autre lieu de décès')], blank=True, null=True)

    resultat_virologie = models.CharField("Résultat analyse", max_length=100,
                                          choices=[('Positif', 'Positif'), ('Negatif', 'Négatif'),
                                                   ('Echantillon inadéquat', 'Echantillon inadéquat'),
                                                   ('Echantillon non trouvé', 'Echantillon non trouvé')], blank=True,
                                          null=True)
    date_confirmation_IPCI = models.DateField("Date de confirmation IPCI", blank=True, null=True)

    # Signature
    signature_agent = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.nom} {self.client.prenoms} - {self.date_notification}"


class DossierMedical(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)
    antecedents_medicaux = models.TextField(blank=True, null=True)
    coagulation = models.BooleanField(default=False)
    immunodepression = models.BooleanField(default=False)
    grossesse = models.BooleanField(default=False)
    terme_grossesse = models.IntegerField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    traitements_en_cours = models.TextField(blank=True, null=True)
    vaccin_antirabique_precedent = models.BooleanField(default=False)
    carnet_vaccination = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"Dossier Médical - {self.patient.nom}"


class TypeProtocole(models.Model):
    nom_protocole = models.CharField(max_length=255)
    nombre_dose = models.IntegerField()
    prix = models.IntegerField()

    def __str__(self):
        return f"{self.nom_protocole} - {self.nombre_dose} doses- ({self.prix})"


class Technique(models.Model):
    nom = models.CharField(max_length=155, unique=True, null=False, blank=False)

    def __str__(self):
        return f"{self.nom}"


class ProtocoleVaccination(models.Model):
    type = models.ForeignKey(TypeProtocole, on_delete=models.CASCADE, help_text="Type de protocole", null=True,
                             blank=True)

    nom = models.CharField(max_length=255,
                           help_text="Nom du Protocole",
                           null=True, blank=True)

    duree = models.IntegerField(help_text="Durée du protocole en jours", null=True, blank=True)
    intervale_visite1_2 = models.CharField(max_length=255,
                                           help_text="Intervalle entre la premiere visite et la seconde visite (ex: 3Jours)",
                                           null=True, blank=True)
    intervale_visite2_3 = models.CharField(max_length=255,
                                           help_text="Intervalle entre la seconde visite et la troisiemme visite (ex: 4Jours)",
                                           null=True, blank=True)
    intervale_visite3_4 = models.CharField(max_length=255,
                                           help_text="Intervalle entre la troisiemme visite et la quatrieme visite (ex: 7Jours)",
                                           null=True, blank=True)
    intervale_visite4_5 = models.CharField(max_length=255,
                                           help_text="Intervalle entre la quatrieme visite et la cinquieme  visite (ex: 14Jours)",
                                           null=True, blank=True)
    nombre_visite = models.IntegerField(help_text="Le nombre maximal de visite ", null=True, blank=True)
    nombre_doses = models.IntegerField(help_text="Nombre total de doses", null=True, blank=True)
    nbr_dose_par_rdv = models.IntegerField(help_text="Nombre de dose par", null=True, blank=True)
    technique = models.ForeignKey(Technique, on_delete=models.SET_NULL, null=True, blank=True)
    volume_doses = models.DecimalField(decimal_places=2, max_digits=5, help_text="le volume par dose en ml", null=True,
                                       blank=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Protocole de Vaccination"
        verbose_name_plural = "Protocoles de Vaccination"

        # Création de la facture

    def __str__(self):
        return f"{self.nom if self.nom else 'Aucun nom'} (OMS)"


# def generer_rendez_vous(protocole):
#     """
#     Génère automatiquement plusieurs rendez-vous de vaccination et les enregistre en base de données.
#     Prend en compte :
#     - Le nombre total de doses (`nombre_doses`)
#     - L'intervalle défini entre chaque dose (`intervale_date`, ex: 7 jours)
#     - La durée maximale du protocole (`duree`)
#     """
#
#     if not protocole.intervale_date or not protocole.nombre_doses:
#         return  # Aucune information sur l'intervalle ou le nombre de doses
#
#     date_debut = datetime.date.today()  # Premier rendez-vous aujourd'hui
#     rendez_vous_list = []
#
#     for i in range(protocole.nombre_doses):
#         date_rendez_vous = date_debut + datetime.timedelta(days=(i * protocole.intervale_date))
#
#         # Vérifier que la date ne dépasse pas la durée totale
#         if protocole.duree and (date_rendez_vous - date_debut).days > protocole.duree:
#             break  # Stopper si on dépasse la durée maximale
#
#         # Création de l'objet rendez-vous
#         rendez_vous = RendezVousVaccination(
#             patient=protocole.patient,
#             # exposition=protocole.patient,
#             protocole=protocole,
#             date_rendez_vous=date_rendez_vous,
#             dose_numero=i + 1,
#             created_by=protocole.created_by
#         )
#         rendez_vous_list.append(rendez_vous)
#
#     # Enregistrement en batch pour optimiser les requêtes SQL
#     if rendez_vous_list:
#         RendezVousVaccination.objects.bulk_create(rendez_vous_list)


class RendezVousVaccination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="rendez_vous_vaccination",
                                db_index=True)
    preexposition = models.ForeignKey(Preexposition, null=True, blank=True, on_delete=models.CASCADE,
                                      related_name="rendez_vous_pre_expo", db_index=True)
    postexposition = models.ForeignKey(PostExposition, null=True, blank=True, on_delete=models.CASCADE,
                                       related_name="rendez_vous_post_expo", db_index=True)
    protocole = models.ForeignKey(ProtocoleVaccination, on_delete=models.CASCADE, related_name="protocole_rendez_vous",
                                  db_index=True)
    date_rendez_vous = models.DateField(help_text="Date prévue du rendez-vous", db_index=True)
    dose_numero = models.IntegerField(help_text="Numéro de la dose dans le protocole", db_index=True)
    ordre_rdv = models.IntegerField(help_text="Numéro d’ordre du RDV pour ce patient", null=True, blank=True,
                                    db_index=True)
    est_effectue = models.BooleanField(default=False, help_text="Le vaccin a-t-il été administré ?", db_index=True)
    statut_rdv = models.CharField(
        choices=[('Passé', 'Passé'), ('Aujourd\'hui', 'Aujourd\'hui'), ('À venir', 'À venir')],
        max_length=100, null=True, blank=True)
    rappel_envoye = models.BooleanField(default=False)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['date_rendez_vous']
        verbose_name = "Rendez-vous Vaccination"
        verbose_name_plural = "Rendez-vous Vaccinations"

    def __str__(self):
        return f"Rendez-vous {self.dose_numero} - {self.patient.nom} ({self.date_rendez_vous})"


class Vaccins(models.Model):
    UNITE_CHOICES = [
        ('ml', 'Millilitres'),
        ('dose', 'Doses'),
        ('flacon', 'Flacons')
    ]

    nom = models.CharField(max_length=255, help_text="Nom du vaccin", db_index=True)
    nbr_dose = models.PositiveIntegerField(help_text="Nombre de dose recquis", null=True, blank=True, db_index=True)
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES, help_text="Unité de mesure")
    prix = models.PositiveIntegerField(help_text="Quantité en stock", null=True, blank=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Ajouté par")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()  # Pour le suivi des modifications

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Vaccin"
        verbose_name_plural = "Vaccins"

    def __str__(self):
        # Vérifie si `date_expiration` n'est pas `None` avant de la formater
        return f"{self.nom}"


class LotVaccin(models.Model):
    numero_lot = models.CharField(max_length=100, unique=True, db_index=True)
    vaccin = models.ForeignKey(Vaccins, on_delete=models.CASCADE, related_name='lotsvaccin', db_index=True)
    date_fabrication = models.DateField(null=True, blank=True, db_index=True)
    date_expiration = models.DateField(null=True, blank=True, db_index=True)
    quantite_initiale = models.PositiveIntegerField()
    quantite_disponible = models.PositiveIntegerField()
    centre = models.ForeignKey(CentreAntirabique, on_delete=models.CASCADE, related_name='lots_centre')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Ajouté par")

    def __str__(self):
        # Vérifie si `date_expiration` n'est pas `None` avant de la formater
        date_formatee = self.date_expiration.strftime('%d-%m-%Y') if self.date_expiration else "Non défini"
        return f"{self.numero_lot}-{self.vaccin} - Expire le {date_formatee}"


class Facture(models.Model):
    STATUT_CHOICES = [
        ('non_payee', 'Non Payée'),
        ('partiellement_payee', 'Partiellement Payée'),
        ('payee', 'Payée')
    ]

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="factures")
    protocole = models.ForeignKey("ProtocoleVaccination", on_delete=models.CASCADE, null=True, blank=True,
                                  related_name="protocolevacc")
    vaccination = models.ForeignKey("Vaccination", on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="factures")
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Montant total de la facture")
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Montant déjà payé")
    reste_a_payer = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Montant restant")
    statut_paiement = models.CharField(max_length=20, choices=STATUT_CHOICES, default="non_payee",
                                       help_text="Statut du paiement")
    date_facture = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True, help_text="Créé par")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_facture']
        verbose_name = "Facture"
        verbose_name_plural = "Factures"

    def __str__(self):
        return f"Facture {self.id} - {self.patient.nom} ({self.get_statut_paiement_display()})"

    def save(self, *args, **kwargs):
        # Mettre à jour le montant restant
        self.reste_a_payer = self.montant_total - self.montant_paye

        # Mettre à jour le statut du paiement
        if self.reste_a_payer <= 0:
            self.statut_paiement = "payee"
        elif self.montant_paye > 0:
            self.statut_paiement = "partiellement_payee"
        else:
            self.statut_paiement = "non_payee"

        super().save(*args, **kwargs)


class Caisse(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('espece', 'Espèces'),
        ('carte', 'Carte Bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Chèque')
    ]

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=10, decimal_places=2, help_text="Montant payé")
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, help_text="Mode de paiement utilisé")
    date_paiement = models.DateTimeField(default=timezone.now, help_text="Date du paiement")
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Paiement enregistré par")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_paiement']
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement de {self.montant}€ pour {self.facture.patient.nom} ({self.get_mode_paiement_display()})"

    def save(self, *args, **kwargs):
        # Mettre à jour le montant payé sur la facture
        # self.facture.montant_paye += self.montant
        # self.facture.save()
        super().save(*args, **kwargs)


class Vaccination(models.Model):
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    date_prevue = models.DateField()
    date_effective = models.DateTimeField(null=True, blank=True)
    dose_ml = models.FloatField()
    dose_numero = models.IntegerField(help_text="Numéro de la dose dans le protocole")
    nombre_dose = models.IntegerField()
    vaccin = models.ForeignKey("Vaccins", on_delete=models.CASCADE, null=True, blank=True)
    lot = models.ForeignKey("LotVaccin", on_delete=models.SET_NULL, null=True, blank=True)
    voie_injection = models.CharField(max_length=5, choices=[('ID', 'Intradermique')])
    protocole = models.ForeignKey("ProtocoleVaccination", on_delete=models.CASCADE, max_length=255)
    lieu = models.CharField(max_length=255)
    created_by = models.ForeignKey("EmployeeUser", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=timezone.now)

    history = HistoricalRecords()

    def __str__(self):
        return f"Vaccination - {self.patient.nom} ({self.date_effective})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if self.date_effective:
            self._schedule_sms_notification()
            self._create_observation()

            if self.date_effective.date() != self.date_prevue:
                self.mettre_a_jour_rendez_vous()

    def _schedule_sms_notification(self):
        from .tasks import send_sms_postvaccination
        eta = self.date_effective + dt.timedelta(minutes=15)
        if eta > timezone.now():
            from .tasks import send_sms_postvaccination
            send_sms_postvaccination.apply_async(args=[self.pk], eta=eta)
        else:
            send_sms_postvaccination.delay(self.pk)

    def _create_observation(self):
        from .models import ObservationPostVaccination
        debut = timezone.now()
        fin = debut + dt.timedelta(minutes=15)
        ObservationPostVaccination.objects.update_or_create(
            vaccination=self,
            defaults={"heure_debut": debut, "heure_fin": fin}
        )

    def mettre_a_jour_rendez_vous(self):
        from .models import RendezVousVaccination
        with transaction.atomic():
            rendez_vous = RendezVousVaccination.objects.filter(
                patient=self.patient,
                protocole=self.protocole,
                date_rendez_vous__gte=self.date_prevue,
                est_effectue=False
            ).order_by('date_rendez_vous')

            if not rendez_vous.exists():
                return

            intervals = self._get_protocol_intervals()
            nouvelle_date = self.date_effective.date()
            date_fin_max = self._get_protocol_end_date()

            for i, rdv in enumerate(rendez_vous):
                if date_fin_max and nouvelle_date > date_fin_max:
                    break

                rdv.date_rendez_vous = nouvelle_date
                rdv.save()

                if i < len(intervals) and intervals[i]:
                    nouvelle_date += dt.timedelta(days=intervals[i])

    def _get_protocol_intervals(self):
        raw = [
            self.protocole.intervale_visite1_2,
            self.protocole.intervale_visite2_3,
            self.protocole.intervale_visite3_4,
            self.protocole.intervale_visite4_5,
        ]
        try:
            return [int(i.replace("Jours", "").strip()) if i else None for i in raw]
        except Exception:
            return [None] * len(raw)

    def _get_protocol_end_date(self):
        if self.protocole.duree:
            return self.date_effective.date() + dt.timedelta(days=self.protocole.duree)
        return None


VOIE_CHOICES = [
    ('IM', 'Intramusculaire'),
    ('ID', 'Intradermique'),
    ('SC', 'Sous-cutanée'),
]


class InjectionImmunoglobuline(models.Model):
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="patients_immuno")
    date_injection = models.DateTimeField(default=now)

    refus_injection = models.BooleanField(default=False, help_text="Le patient a-t-il refusé l'injection ?")
    motif_refus = models.TextField(blank=True, null=True, help_text="Motif du refus (si refusé)")

    type_produit = models.CharField(max_length=100, blank=True, null=True)
    dose_ui = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True,
                                  help_text="Volume injecté en Unite International")
    dose_a_injecter = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True,
                                          help_text="Dose à prescrire en UI ")
    voie_injection = models.CharField(max_length=10, choices=VOIE_CHOICES, blank=True, null=True)
    site_injection = models.TextField(blank=True, null=True,
                                      help_text="Sites anatomiques d'injection (ex: bras gauche, cuisse droite...)")
    numero_lot = models.CharField(max_length=100, blank=True, null=True)
    date_peremption = models.DateField(blank=True, null=True)
    laboratoire_fabricant = models.CharField(max_length=100, blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_injection']

    def clean(self):
        errors = {}

        # Vérification dose_a_injecter ≥ 0
        if self.dose_a_injecter is not None and self.dose_a_injecter < 0:
            errors['dose_a_injecter'] = "La dose à injecter ne peut pas être négative."

        # Vérification dose_ui ≤ dose_a_injecter
        if (
                self.dose_ui is not None and
                self.dose_a_injecter is not None and
                self.dose_ui > self.dose_a_injecter
        ):
            errors['dose_ui'] = "La dose injectée (UI) ne peut pas dépasser la dose à injecter."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Calcul automatique dose_a_injecter si vide et poids dispo
        if not self.dose_a_injecter and self.patient and self.patient.poids:
            self.dose_a_injecter = round(Decimal(self.patient.poids) * Decimal('40.0'), 2)

        self.full_clean()  # Appelle clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.refus_injection:
            return f"Refus d'immunoglobuline - {self.patient}"
        return f"Injection de {self.type_produit} à {self.patient} le {self.date_injection.strftime('%d/%m/%Y')}"


class ObservationPostVaccination(models.Model):
    vaccination = models.OneToOneField(Vaccination, on_delete=models.CASCADE, related_name="observation")
    heure_debut = models.DateTimeField()
    heure_fin = models.DateTimeField()
    est_terminee = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def temps_restant(self):
        return max(dt.timedelta(), self.heure_fin - timezone.now())


class MAPI(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="mapi")
    vaccination = models.ForeignKey(Vaccination, on_delete=models.CASCADE, related_name="mapi")
    titre = models.CharField(max_length=255, null=True, blank=True)

    date_apparition = models.DateTimeField(help_text="Date d'apparition des symptômes")
    description = models.TextField(help_text="Description des symptômes observés")

    gravite_choices = [
        ('léger', 'Léger'),
        ('modéré', 'Modéré'),
        ('sévère', 'Sévère')
    ]
    gravite = models.CharField(max_length=10, choices=gravite_choices, help_text="Gravité des symptômes")

    traitement_administre = models.TextField(blank=True, null=True, help_text="Traitement administré au patient")
    evolution = models.CharField(max_length=255, choices=[
        ('guéri', 'Guéri'),
        ('en observation', 'En observation'),
        ('complications', 'Complications')
    ], default='en observation', help_text="Évolution de la maladie")

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-date_apparition']
        verbose_name = "MAPI (Maladie Post Injection)"
        verbose_name_plural = "MAPI (Maladies Post Injection)"

    def __str__(self):
        return f"MAPI - {self.patient.nom} ({self.date_apparition})"


class Symptom(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.nom}'


class PreleveMode(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nom


class Epidemie(models.Model):
    nom = models.CharField(max_length=100)
    description = HTMLField(blank=True, null=True)
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    thumbnails = models.ImageField(null=True, blank=True, upload_to='epidemie/thumbnails')
    symptomes = models.ManyToManyField(Symptom, related_name='épidémies')

    class Meta:
        permissions = (('voir_epidemie', 'peut voir epidemie'),)

    @property
    def regions_impactees(self):
        # Récupère toutes les régions impactées par cette épidémie
        regions = HealthRegion.objects.filter(city__commune__echantillons__maladie=self).distinct().count()
        return regions

    @property
    def personnes_touchees(self):
        # Compte le nombre de personnes ayant des échantillons positifs pour cette épidémie
        nombre_personnes_touchees = Patient.objects.filter(
            echantillons__maladie=self,
            echantillons__resultat=True
        ).distinct().count()
        return nombre_personnes_touchees

    @property
    def personnes_decedees(self):
        # Compte le nombre de personnes décédées ayant des échantillons positifs pour cette épidémie
        nombre_personnes_decedees = Patient.objects.filter(
            echantillons__maladie=self,
            echantillons__resultat=True,
            decede=True
        ).distinct().count()
        return nombre_personnes_decedees

    @property
    def nombre_patients_positifs_ce_mois(self):
        current_month = now().month
        current_year = now().year
        return self.echantillon_set.filter(
            resultat=True,
            date_collect__month=current_month,
            date_collect__year=current_year
        ).count()

    def is_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.date_debut <= today and (self.date_fin is None or self.date_fin >= today)

    def __str__(self):
        return self.nom


class Echantillon(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="echantillons", null=True, blank=True, )
    code_echantillon = models.CharField(null=True, blank=True, max_length=12, unique=True)
    maladie = models.ForeignKey('Epidemie', null=True, blank=True, on_delete=models.CASCADE)
    mode_preleve = models.ForeignKey('PreleveMode', null=True, blank=True, on_delete=models.CASCADE)
    date_collect = models.DateTimeField(null=True, blank=True)
    site_collect = models.CharField(null=True, blank=True, max_length=500)
    agent_collect = models.ForeignKey(EmployeeUser, null=True, blank=True, on_delete=models.CASCADE)
    status_echantillons = models.CharField(null=True, blank=True, max_length=10)
    resultat = models.BooleanField(default=False)
    linked = models.BooleanField(default=False)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # Générer un code_patient unique uniquement avec des chiffres
        if not self.code_echantillon:
            # Utiliser uuid4 pour générer un identifiant unique et extraire les chiffres
            self.code_echantillon = ''.join(filter(str.isdigit, str(uuid.uuid4().int)))[
                                    :12]  # Limiter à 20 chiffres maximum
        super(Echantillon, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.code_echantillon}- {self.patient}-{self.maladie}"


class City(models.Model):
    name = models.CharField(max_length=200)
    region = models.ForeignKey(HealthRegion, on_delete=models.CASCADE)
    geom = models.MultiPolygonField()

    def __str__(self):
        return self.name


class WhatsAppMessageLog(models.Model):
    vaccination = models.ForeignKey(
        'Vaccination',
        on_delete=models.CASCADE,
        related_name='whatsapp_logs'
    )
    sid = models.CharField(
        max_length=64,
        help_text="Twilio Message SID",
        unique=True
    )
    to = models.CharField(max_length=32, help_text="Numéro destinataire")
    status = models.CharField(
        max_length=32,
        help_text="Statut du message (queued, sent, delivered, failed…)"
    )
    body = models.TextField(help_text="Contenu du message")
    date_sent = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_sent']
        verbose_name = "Log message WhatsApp"
        verbose_name_plural = "Logs messages WhatsApp"

    def __str__(self):
        return f"{self.to} – {self.status} @ {self.date_sent:%Y-%m-%d %H:%M}"

class SMSLog(models.Model):
    STATUS_CHOICES = (
        ("SUCCESS", "Succès"),
        ("FAILED", "Échec"),
    )

    phone_number = models.CharField(max_length=30)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    response_content = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    error = models.TextField(null=True, blank=True)
    task_id = models.CharField(max_length=100, null=True, blank=True)
    message_length = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "sent_at"]),
            models.Index(fields=["phone_number", "sent_at"]),
        ]
        ordering = ["-sent_at"]
        verbose_name = "Log SMS"
        verbose_name_plural = "Logs SMS"

    def save(self, *args, **kwargs):
        if self.message:
            self.message_length = len(self.message)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sent_at}] {self.phone_number} - {self.status}"