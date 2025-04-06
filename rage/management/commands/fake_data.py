import random
import datetime
import uuid
from faker import Faker
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from rage.models import DistrictSanitaire, ProtocoleVaccination, EmployeeUser, Commune, Patient, Preexposition, \
    PostExposition, RageHumaineNotification

fake = Faker(["fr_FR"])  # Faker en français


class Command(BaseCommand):
    help = "Génère des données fictives pour les patients, expositions et notifications"

    def add_arguments(self, parser):
        parser.add_argument("--patients", type=int, default=50, help="Nombre de patients à créer")
        parser.add_argument("--preexpo", type=int, default=30, help="Nombre de cas de pré-exposition")
        parser.add_argument("--postexpo", type=int, default=30, help="Nombre de cas de post-exposition")
        parser.add_argument("--notifications", type=int, default=30, help="Nombre de notifications de rage")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Début de la génération des données..."))

        # Obtenir les objets nécessaires pour les FK
        communes = list(Commune.objects.filter(is_in="Côte d'Ivoire"))
        districts = list(DistrictSanitaire.objects.all())
        protocoles = list(ProtocoleVaccination.objects.all())
        users = list(EmployeeUser.objects.all())

        patients = self.create_patients(options["patients"], communes, users)
        self.create_preexpositions(patients, options["preexpo"], protocoles, users)
        self.create_postexpositions(patients, options["postexpo"], communes, users)
        self.create_rage_notifications(patients, options["notifications"], communes, districts, users)

        self.stdout.write(self.style.SUCCESS("✅ Génération terminée avec succès !"))

    def random_date(self, past_years=5):
        """Générer une date aléatoire entre aujourd'hui et N années en arrière."""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=past_years * 365)
        return fake.date_between(start_date=start_date, end_date=end_date)

    def create_patients(self, n, communes, users):
        """Créer des patients fictifs."""
        patients = []
        for _ in range(n):
            patient = Patient.objects.create(
                code_patient=f"{uuid.uuid4().hex[:8].upper()}",
                nom=fake.last_name(),
                prenoms=fake.first_name(),
                contact=fake.phone_number(),
                date_naissance=self.random_date(40),
                sexe=random.choice(["M", "F"]),
                secteur_activite=fake.job(),
                niveau_etude=random.choice(["Primaire", "Secondaire", "Universitaire", "Aucun"]),
                commune=random.choice(communes) if communes else None,
                quartier=fake.street_name(),
                village=fake.city(),
                centre_ar=None,
                proprietaire_animal=fake.boolean(),
                typeanimal=random.choice(["Chien", "Chat", "Singe", "Autre"]),
                patient_mineur=fake.boolean(),
                accompagnateur=fake.name() if fake.boolean() else "",
                accompagnateur_contact=fake.phone_number() if fake.boolean() else "",
                accompagnateur_adresse=fake.address() if fake.boolean() else "",
                accompagnateur_nature=random.choice(["Pere/Mere", "Ami", "Voisin du quartier", "Autre"]),
                accompagnateur_niveau_etude=random.choice(["Primaire", "Secondaire", "Universitaire", "Aucun"]),
                status=random.choice(["Aucun", "Suivi", "Guéri"]),
                gueris=fake.boolean(),
                decede=fake.boolean(),
                cause_deces=fake.sentence() if fake.boolean() else "",
                date_deces=self.random_date() if fake.boolean() else None,
                created_by=random.choice(users) if users else None
            )
            patients.append(patient)
        self.stdout.write(self.style.SUCCESS(f"✅ {n} patients créés"))
        return patients

    def create_preexpositions(self, patients, n, protocoles, users):
        """Créer des cas de pré-exposition fictifs."""
        for _ in range(n):
            Preexposition.objects.create(
                client=random.choice(patients),
                codeexpo=f"PREX-{uuid.uuid4().hex[:8].upper()}",
                voyage=fake.boolean(),
                mise_a_jour=fake.boolean(),
                protection_rage=fake.boolean(),
                chien_voisin=fake.boolean(),
                chiens_errants=fake.boolean(),
                autre=fake.boolean(),
                autre_motif=fake.sentence() if fake.boolean() else "",
                tele=fake.boolean(),
                radio=fake.boolean(),
                sensibilisation=fake.boolean(),
                proche=fake.boolean(),
                presse=fake.boolean(),
                passage_car=fake.boolean(),
                diff_canal=fake.boolean(),
                canal_infos=fake.sentence() if fake.boolean() else "",
                aime_animaux=fake.boolean(),
                type_animal_aime=random.choice(["Chien", "Chat", "Autre"]),
                protocole_vaccination=random.choice(protocoles) if protocoles else None,
                created_by=random.choice(users) if users else None
            )
        self.stdout.write(self.style.SUCCESS(f"✅ {n} cas de pré-exposition créés"))

    def create_postexpositions(self, patients, n, communes, users):
        """Créer des cas de post-exposition fictifs."""
        for _ in range(n):
            PostExposition.objects.create(
                client=random.choice(patients),
                date_exposition=self.random_date(),
                lieu_exposition=fake.city(),
                exposition_commune=random.choice(communes) if communes else None,
                exposition_quartier=fake.street_name(),
                circonstance=random.choice(["Attaque provoquée", "Agression", "Attaque collective", "Professionnel"]),
                surveillance_veterinaire=fake.boolean(),
                created_by=random.choice(users) if users else None
            )
        self.stdout.write(self.style.SUCCESS(f"✅ {n} cas de post-exposition créés"))

    def create_rage_notifications(self, patients, n, communes, districts, users):
        """Créer des notifications de rage fictives."""
        for _ in range(n):
            RageHumaineNotification.objects.create(
                client=random.choice(patients),
                date_notification=self.random_date(),
                hopital=fake.company(),
                service=fake.job(),
                agent_declarant=fake.name(),
                adresse=fake.address(),
                telephone=fake.phone_number(),
                cel=fake.phone_number(),
                email=fake.email(),
                date_exposition=self.random_date(),
                lieu_exposition=fake.city(),
                pays="Côte d'Ivoire",
                exposition_commune=random.choice(communes) if communes else None,
                district_sanitaire_exposition=random.choice(districts) if districts else None,
                nature_exposition=random.choice(["Morsure", "Griffure", "Léchage", "Simple manipulation", "Autres"]),
                siege_lesion=random.choice(["Tête et cou", "Membre supérieur", "Tronc", "OGE", "Membre inférieur"]),
                categorie_lesion=random.choice(["I", "II", "III"]),
                animal_responsable=random.choice(["Chien", "Chat", "Autre"]),
                devenir_animal=random.choice(["Vivant", "Errant", "Mort", "Abattu", "Disparu"]),
                prelevement_animal=fake.boolean(),
                soins_locaux=fake.boolean(),
                desinfection=fake.boolean(),
                vaccination_antirabique=fake.boolean(),
                protocole_vaccination=random.choice(["Essen", "Zagreb", "ID"]),
                evolution=random.choice(["Encore malade", "Décédé(e)"]),
                date_deces=self.random_date() if fake.boolean() else None,
                signature_agent=fake.name()
            )
        self.stdout.write(self.style.SUCCESS(f"✅ {n} notifications de rage créées"))
