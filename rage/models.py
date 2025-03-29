import random
import string
import uuid
import datetime as dt
from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import now, make_aware
from djgeojson.fields import PointField
from django.contrib.gis.db import models
from phonenumber_field.formfields import PhoneNumberField
from simple_history.models import HistoricalRecords
from tinymce.models import HTMLField
from datetime import datetime, date

from rage_INHP.utils.phone import nettoyer_numero, formater_numero_local

# Create your models here.

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
    ('plus de 10 ', 'plus de 10'),
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
    centre = models.ForeignKey('CentreAntirabique', on_delete=models.CASCADE)

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


class Commune(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True, unique=True)
    type = models.CharField(choices=type_localite_choices, max_length=100, null=True, blank=True)
    population = models.CharField(max_length=100, null=True, blank=True)
    is_in = models.CharField(max_length=255, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True, )
    geom = models.PointField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.district}"


class Patient(models.Model):
    nature_acompagnateur_CHOICES = [
        ('Pere', 'Pere'),
        ('Mere', 'Mere'),
        ('Oncle', 'Oncle'),
        ('Tante', 'Tante'),
        ('Frère', 'Frère'),
        ('Soeure', 'Soeure'),
        ('Cousin', 'Cousin'),
        ('Cousine', 'Cousine'),
        ('Connaissance du quartier', 'Connaissance du quartier'),
        ('Voisin du quartier', 'Voisin du quartier'),
        ('Propriétaire animal ', 'Propriétaire animal ')
    ]
    code_patient = models.CharField(max_length=225, blank=True, unique=True, editable=False)
    nom = models.CharField(max_length=225)
    prenoms = models.CharField(max_length=225)
    contact = models.CharField(max_length=20)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=Sexe_choices, )
    secteur_activite = models.CharField(max_length=200, null=True, blank=True)
    niveau_etude = models.CharField(choices=NIVEAU_ETUDE_CHOICES, max_length=500, null=True, blank=True)
    residence_commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    quartier = models.CharField(max_length=255, blank=True, null=True)
    village = models.CharField(max_length=255, blank=True, null=True)
    centre_ar = models.ForeignKey(CentreAntirabique, on_delete=models.SET_NULL, null=True, blank=True)
    proprietaire_animal = models.BooleanField(default=False)
    typeanimal = models.CharField(choices=typeAnimal_choices, max_length=255, blank=True, null=True)
    autretypeanimal = models.CharField(max_length=255, blank=True, null=True)
    patient_mineur = models.BooleanField(default=False)
    accompagnateur = models.CharField(max_length=255, blank=True, null=True)
    accompagnateur_contact = models.CharField(max_length=20, blank=True, null=True)
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
        self.accompagnateur_contact = nettoyer_numero(self.accompagnateur_contact)

        # Générer un code_patient unique constitué de chiffres et de caractères alphabétiques
        if not self.code_patient:
            # Générer 16 chiffres à partir de l'UUID
            digits = ''.join(filter(str.isdigit, str(uuid.uuid4().int)))[:8]
            # Générer 4 caractères alphabétiques aléatoires
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            # Combiner les chiffres et les lettres pour former le code_patient
            self.code_patient = digits + letters

        super(Patient, self).save(*args, **kwargs)

    @property
    def contact_formatte(self):
        return formater_numero_local(self.contact)

    @property
    def accompagnateur_contact_formatte(self):
        return formater_numero_local(self.accompagnateur_contact)

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
    #MotifVaccination
    client = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    codeexpo = models.CharField(max_length=255, blank=True, null=True, unique=True)
    voyage = models.BooleanField(default=False)
    mise_a_jour = models.BooleanField(default=False)
    protection_rage = models.BooleanField(default=False)
    chien_voisin = models.BooleanField(default=False)
    chiens_errants = models.BooleanField(default=False)
    autre = models.BooleanField(default=False)
    autre_motif = models.TextField(blank=True, null=True)
    #InformationVaccination
    tele = models.BooleanField(default=False)
    radio = models.BooleanField(default=False)
    sensibilisation = models.BooleanField(default=False)
    proche = models.BooleanField(default=False)
    presse = models.BooleanField(default=False)
    passage_car = models.BooleanField(default=False)
    diff_canal = models.BooleanField(default=False)
    canal_infos = models.TextField(blank=True, null=True)
    #ConnaissanceAttitude
    conduite_CHOICES = [('Abattage', 'Abattage'), ('Surveillance vétérinaire', 'Surveillance vétérinaire'),
                        ('Ne rien faire', 'Ne rien faire'),
                        ('Autre', 'Autre')]
    mesure_CHOICES = [('Abattage des chiens', 'Abattage des chiens'),
                      ('Eviter d’avoir un chien', 'Eviter d’avoir un chien'),
                      ('Eviter la divagation des chiens ', 'Eviter la divagation des chiens'),
                      ('Organiser des séances de CCC', 'Organiser des séances de CCC'),
                      ('Vacciner la population contre la rage', 'Vacciner la population contre la rage'),
                      ('Sensibiliser particulièrement les propriétaires de chien',
                       'Sensibiliser particulièrement les propriétaires de chien'),
                      ('Intégrer rage dans le programme des cours au primaire',
                       'Intégrer rage dans le programme des cours au primaire'),
                      ]
    appreciation_CHOICES = [('Elevé', 'Elevé'), ('Acceptable', 'Acceptable'),
                            ('Pas à la portée de tous', 'Pas à la portée de tous'),
                            ('Moins couteux', 'Moins couteux')]

    aime_animaux = models.BooleanField(default=False)
    type_animal_aime = models.CharField(choices=ESPECE_CHOICES, max_length=255, blank=True, null=True)
    conduite_animal_mordeur = models.CharField(choices=conduite_CHOICES, max_length=255, null=True, blank=True)
    connait_protocole_var = models.BooleanField(default=False)
    dernier_var_animal_type = models.CharField(max_length=255, blank=True, null=True)
    dernier_var_animal_date = models.DateField(blank=True, null=True)
    mesures_elimination_rage = models.CharField(null=True, blank=True)
    appreciation_cout_var = models.CharField(choices=appreciation_CHOICES, max_length=255, null=True, blank=True)
    protocole_vaccination = models.ForeignKey('ProtocoleVaccination', on_delete=models.CASCADE, null=True, blank=True, )

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="employeer")
    created_at = models.DateTimeField(auto_now_add=True)
    fin_protocole = models.BooleanField(default=False)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.codeexpo:
            self.codeexpo = f"PREP-{uuid.uuid4().hex[:8].upper()}"  # EXPO-8CARACTERES
        super().save(*args, **kwargs)


class PostExposition(models.Model):
    # Identification du patient
    client = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)

    # Exposition
    date_exposition = models.DateField(null=True, blank=True)
    lieu_exposition = models.CharField(max_length=255, null=True, blank=True)
    exposition_commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    exposition_quartier = models.CharField(max_length=255, null=True, blank=True)

    circonstance = models.CharField(
        max_length=255,
        choices=[
            ('Attaque provoquée', 'Attaque provoquée'),
            ('Agression', 'Agression'),
            ('Attaque collective', 'Attaque collective'),
            ('Professionnel', 'Professionnel')
        ],
        null=True, blank=True
    )

    attaque_provoquee = models.BooleanField(default=False)
    agression = models.BooleanField(default=False)
    attaque_collective = models.BooleanField(default=False)
    professionnel = models.BooleanField(default=False)

    type_professionnel = models.CharField(
        max_length=50,
        choices=[('Manipulation / Soins', 'Manipulation / Soins'), ('Laboratoire', 'Laboratoire')],
        null=True, blank=True
    )

    morsure = models.BooleanField(default=False)
    griffure = models.BooleanField(default=False)
    lechage_saine = models.BooleanField(default=False)
    lechage_lesee = models.BooleanField(default=False)
    contactanimalpositif = models.BooleanField(default=False)
    contactpatientpositif = models.BooleanField(default=False)
    autre = models.BooleanField(default=False)
    autre_nature_exposition = models.TextField(null=True, blank=True)

    # Siège de l’exposition
    tete = models.BooleanField(default=False)
    cou = models.BooleanField(default=False)
    membre_superieur = models.BooleanField(default=False)
    preciser_membre_sup = models.CharField(max_length=255, null=True, blank=True)
    tronc = models.BooleanField(default=False)
    preciser_tronc = models.CharField(max_length=255, null=True, blank=True)
    organes_genitaux_externes = models.BooleanField(default=False)
    membre_inferieur = models.BooleanField(default=False)
    preciser_membre_inf = models.CharField(max_length=255, null=True, blank=True)
    saignement_immediat = models.BooleanField(default=False)
    vetements_presents = models.BooleanField(default=False)
    dechires = models.BooleanField(default=False)

    siege_exposition = models.TextField(null=True, blank=True)
    vetements_dechires = models.BooleanField(default=False)
    nbrlesions = models.CharField(max_length=300, null=True, blank=True)

    # Animal
    espece = models.CharField(
        max_length=50,
        choices=[('Chien', 'Chien'), ('Chat', 'Chat'), ('Singe', 'Singe'), ('Chauve-souris', 'Chauve-souris'),
                 ('Autre', 'Autre')],
        null=True, blank=True
    )
    autre_animal = models.CharField(max_length=255, null=True, blank=True)
    domestic = models.BooleanField(default=False, )

    connais_proprio = models.BooleanField(default=False)
    nom_proprietaire = models.CharField(max_length=255, null=True, blank=True)
    contact_proprietaire = models.CharField(max_length=255, null=True, blank=True)
    info_proprietaire = models.IntegerField(null=True, blank=True)
    retour_info_proprietaire = models.CharField(max_length=50, null=True, blank=True)

    avis = models.BooleanField(default=False)
    convocation = models.BooleanField(default=False)
    prophylaxie = models.BooleanField(default=False)

    correctement_vaccine = models.BooleanField(default=False)
    non_vaccine = models.BooleanField(default=False)
    nonajours = models.BooleanField(default=False)
    vacinconnu = models.BooleanField(default=False)

    inconnu = models.BooleanField(default=False, verbose_name='connu')
    errant = models.BooleanField(default=False, verbose_name='errant')
    disparu = models.BooleanField(default=False)
    mort = models.BooleanField(default=False)
    abatu = models.BooleanField(default=False)
    date_derniere_vaccination = models.DateField(null=True, blank=True)

    # Gravité et Surveillance
    gravite_oms = models.CharField(max_length=10, choices=[('I', 'I'), ('II', 'II'), ('III', 'III')], null=True,
                                   blank=True)
    surveillance_veterinaire = models.BooleanField(default=False)

    certificat = models.CharField(max_length=50, null=True, blank=True)
    piece_jointe = models.FileField(upload_to="certifiatVaccin", null=True, blank=True)
    date_etablissement = models.DateField(null=True, blank=True)
    Date_depot_car = models.DateField(null=True, blank=True)
    Decision_de_poursuite_tar = models.CharField(max_length=50, null=True, blank=True)
    Decision_d_arrete_tar = models.CharField(max_length=50, null=True, blank=True)

    # Diagnostic et Prise en charge
    prelevement_animal = models.BooleanField(default=False)
    diagnostic_laboratoire = models.CharField(max_length=50, choices=[('Positif', 'Positif'), ('Negatif', 'Négatif')],
                                              null=True, blank=True)
    date_diagnostic = models.DateField(null=True, blank=True)

    # Dossier Médical
    antecedents_medicaux = models.TextField(null=True, blank=True)
    probleme_coagulation = models.BooleanField(default=False)
    details_problemes = models.CharField(max_length=50, null=True, blank=True)
    immunodepression = models.BooleanField(default=False)
    details_immo = models.CharField(max_length=50, null=True, blank=True)
    grossesse = models.BooleanField(default=False)
    details_grosesse = models.CharField(max_length=50, null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)
    traitements_en_cours = models.TextField(null=True, blank=True)

    # Antécédents vaccinaux
    vat_dernier_injection = models.DateField(null=True, blank=True)
    vat_rappel = models.DateField(null=True, blank=True)
    vat_lot = models.CharField(max_length=255, null=True, blank=True)
    vaccin_antirabique = models.BooleanField(default=False)
    carnet_vaccinal = models.TextField(null=True, blank=True)

    # Prise en charge
    lavage_plaies = models.BooleanField(default=False)
    desinfection_plaies = models.BooleanField(default=False)
    delai_apres_exposition = models.CharField(max_length=50, null=True, blank=True)
    produits_utilises = models.CharField(max_length=50, null=True, blank=True)

    sutures = models.BooleanField(default=False)
    serum_antitetanique = models.BooleanField(default=False)

    antibiotiques = models.BooleanField(default=False)
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
    observance = models.BooleanField(default=False)
    evolution_patient = models.CharField(max_length=50, choices=[('Vivant', 'Vivant'), ('Décédé', 'Décédé'),
                                                                 ('Non précisé', 'Non précisé')], null=True, blank=True)
    cause_deces = models.TextField(null=True, blank=True)
    date_deces = models.DateField(null=True, blank=True)
    protocole_vaccination = models.ForeignKey('ProtocoleVaccination', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.client.nom} {self.client.prenoms} - {self.date_exposition}"


class RageHumaineNotification(models.Model):
    # Identification du patient
    client = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True,
                               related_name="notifications_rage")
    # Informations générales
    date_notification = models.DateField("Date de la notification")
    hopital = models.CharField("Hôpital", max_length=100)
    service = models.CharField("Service", max_length=100)
    agent_declarant = models.CharField("Agent déclarant", max_length=100)
    adresse = models.CharField("Adresse", max_length=200)
    telephone = models.CharField("Téléphone", max_length=20)
    cel = models.CharField("Cel", max_length=20)
    email = models.EmailField("E-mail")

    # Origine possible de la contamination
    date_exposition = models.DateField("Date de l’exposition")
    lieu_exposition = models.CharField("Lieu de l’exposition", max_length=200)
    pays = models.CharField("Pays", max_length=100)
    exposition_commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    district_sanitaire_exposition = models.ForeignKey(DistrictSanitaire, on_delete=models.SET_NULL, null=True,
                                                      blank=True)
    nature_exposition = models.CharField("Nature de l’exposition", max_length=20, choices=[
        ('Morsure', 'Morsure'), ('Griffure', 'Griffure'), ('Léchage', 'Léchage'),
        ('Simple manipulation', 'Simple manipulation'), ('Autres', 'Autres')
    ])
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
    prelevement_animal = models.BooleanField("Prélèvement d’échantillons chez l’animal mordeur", default=False)
    resultat_analyse = models.CharField("Résultat analyse", max_length=10, choices=[('Oui', 'Oui'), ('Non', 'Non')],
                                        blank=True, null=True)
    labo_pathologie_animale = models.BooleanField("Laboratoire de pathologie Animale", default=False)
    autres_labos = models.CharField("Autres laboratoires", max_length=100, blank=True, null=True)

    # Prophylaxie post-exposition
    soins_locaux = models.BooleanField("Soins locaux : lavage de la plaie", default=False)
    desinfection = models.BooleanField("Désinfection", default=False)
    produit_desinfection = models.CharField("Produit utilisé pour la désinfection", max_length=100, blank=True,
                                            null=True)
    vaccination_antirabique = models.BooleanField("Vaccination antirabique", default=False)
    date_debut_vaccination = models.DateField("Date de début de la vaccination antirabique", blank=True, null=True)
    protocole_vaccination = models.CharField("Protocole utilisé", max_length=10,
                                             choices=[('Essen', 'Essen'), ('Zagreb', 'Zagreb'), ('ID', 'ID')],
                                             blank=True, null=True)

    # Période de la maladie
    date_premiers_signes = models.DateField("Date des premiers signes", blank=True, null=True)
    trouble_comportement = models.BooleanField("Trouble du comportement", default=False)
    agitation = models.BooleanField("Agitation", default=False)
    hospitalisation = models.BooleanField("Hospitalisation", default=False)
    date_hospitalisation = models.DateField("Date d’hospitalisation", blank=True, null=True)
    lieu_hospitalisation = models.CharField("Lieu d’hospitalisation", max_length=100, blank=True, null=True)
    evolution = models.CharField("Évolution", max_length=20,
                                 choices=[('Encore malade', 'Encore malade'), ('Décédé(e)', 'Décédé(e)')], blank=True,
                                 null=True)
    date_deces = models.DateField("Date de décès", blank=True, null=True)

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
    volume_doses = models.DecimalField(decimal_places=2, max_digits=2, help_text="le volume par dose en ml", null=True,
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
        return f"{self.nom if self.nom else 'Aucun nom'} ({self.technique})"


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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="rendez_vous_vaccination")
    preexposition = models.ForeignKey(Preexposition, null=True, blank=True, on_delete=models.CASCADE,
                                      related_name="rendez_vous_pre_expo")
    postexposition = models.ForeignKey(PostExposition, null=True, blank=True, on_delete=models.CASCADE,
                                       related_name="rendez_vous_post_expo")
    protocole = models.ForeignKey(ProtocoleVaccination, on_delete=models.CASCADE, related_name="protocole_rendez_vous")
    date_rendez_vous = models.DateField(help_text="Date prévue du rendez-vous")
    dose_numero = models.IntegerField(help_text="Numéro de la dose dans le protocole")
    est_effectue = models.BooleanField(default=False, help_text="Le vaccin a-t-il été administré ?")
    statut_rdv = models.CharField(
        choices=[('Passé', 'Passé'), ('Aujourd\'hui', 'Aujourd\'hui'), ('À venir', 'À venir')],
        max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['date_rendez_vous']
        verbose_name = "Rendez-vous Vaccination"
        verbose_name_plural = "Rendez-vous Vaccinations"

    def __str__(self):
        return f"Rendez-vous {self.dose_numero} - {self.patient.nom} ({self.date_rendez_vous})"


class StockVaccin(models.Model):
    UNITE_CHOICES = [
        ('ml', 'Millilitres'),
        ('dose', 'Doses'),
        ('flacon', 'Flacons')
    ]

    nom = models.CharField(max_length=255, help_text="Nom du vaccin")
    lot = models.CharField(max_length=50, unique=True, help_text="Numéro du lot")
    quantite = models.PositiveIntegerField(help_text="Quantité en stock")
    nbr_dose = models.PositiveIntegerField(help_text="Nombre de dose recquis", null=True, blank=True)
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES, help_text="Unité de mesure")
    date_expiration = models.DateField(help_text="Date d'expiration du vaccin")
    fournisseur = models.CharField(max_length=255, null=True, blank=True, help_text="Nom du fournisseur")
    prix = models.PositiveIntegerField(help_text="Quantité en stock", null=True, blank=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Ajouté par")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()  # Pour le suivi des modifications

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Stock de Vaccin"
        verbose_name_plural = "Stocks de Vaccins"

    def __str__(self):
        # Vérifie si `date_expiration` n'est pas `None` avant de la formater
        date_formatee = self.date_expiration.strftime('%d-%m-%Y') if self.date_expiration else "Non défini"
        return f"{self.nom} - Lot {self.lot} - Expire le {date_formatee}"


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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date_prevue = models.DateField()
    date_effective = models.DateField(null=True, blank=True)
    dose_ml = models.FloatField()
    dose_numero = models.IntegerField(help_text="Numéro de la dose dans le protocole")
    nombre_dose = models.IntegerField()
    vaccin = models.ForeignKey(StockVaccin, on_delete=models.CASCADE, null=True, blank=True)
    voie_injection = models.CharField(max_length=5, choices=[('ID', 'Intradermique')])
    protocole = models.ForeignKey(ProtocoleVaccination, on_delete=models.CASCADE, max_length=255)
    lieu = models.CharField(max_length=255)
    reactions = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=now)

    history = HistoricalRecords()

    def __str__(self):
        return f"Vaccination - {self.patient.nom} ({self.date_effective})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Sauvegarde de la vaccination

        if self.date_effective:
            # Crée une observation de 15 minutes
            from django.utils import timezone
            debut = timezone.now()
            fin = debut + dt.timedelta(minutes=15)

            # Créer ou mettre à jour une éventuelle observation liée
            ObservationPostVaccination.objects.update_or_create(
                vaccination=self,
                defaults={'heure_debut': debut, 'heure_fin': fin}
            )

        # Vérifier si la date effective est différente de la date prévue
        if self.date_effective and self.date_effective != self.date_prevue:
            self.mettre_a_jour_rendez_vous()
            # Vérifier si la date effective est différente de la date prévue

    def mettre_a_jour_rendez_vous(self):
        """
        Met à jour les rendez-vous restants si la date effective diffère de la date prévue.
        """
        with transaction.atomic():
            # Récupérer les rendez-vous restants pour ce patient et ce protocole
            rendez_vous_restants = RendezVousVaccination.objects.filter(
                patient=self.patient,
                protocole=self.protocole,
                date_rendez_vous__gte=self.date_prevue,
                est_effectue=False
            ).order_by('date_rendez_vous')

            if not rendez_vous_restants.exists():
                return  # Aucun rendez-vous à mettre à jour

            # Récupération des intervalles définis dans le protocole
            intervals = [
                self.protocole.intervale_visite1_2,
                self.protocole.intervale_visite2_3,
                self.protocole.intervale_visite3_4,
                self.protocole.intervale_visite4_5
            ]

            # Convertir les intervalles en jours (gérer les cas où les valeurs sont None)
            try:
                intervals = [int(i.replace("Jours", "").strip()) if i else None for i in intervals]
            except ValueError:
                intervals = [None] * len(intervals)  # Définit des valeurs nulles si conversion impossible

            # Nouvelle date de départ basée sur la date effective de la vaccination
            nouvelle_date_rdv = self.date_effective
            duree_max = dt.timedelta(days=self.protocole.duree) if self.protocole.duree else None
            date_fin_max = self.date_effective + duree_max if duree_max else None  # Date limite du protocole

            for i, rdv in enumerate(rendez_vous_restants):
                # Vérifier si on ne dépasse pas la durée maximale du protocole
                if date_fin_max and nouvelle_date_rdv > date_fin_max:
                    break  # Stopper la mise à jour si la nouvelle date dépasse la durée max

                # Mise à jour de la date du rendez-vous
                rdv.date_rendez_vous = nouvelle_date_rdv
                rdv.save()

                # Mise à jour de la date pour le prochain rendez-vous
                if i < len(intervals) and intervals[i]:
                    nouvelle_date_rdv += dt.timedelta(days=intervals[i])


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
