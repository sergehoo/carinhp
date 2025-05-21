from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.gis.admin import OSMGeoAdmin
from django.db import transaction
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportMixin
from leaflet.admin import LeafletGeoAdmin
from pandas.tests.tseries.offsets.test_custom_business_month import dt
from simple_history.admin import SimpleHistoryAdmin

from rage.models import EmployeeUser, PolesRegionaux, HealthRegion, DistrictSanitaire, CentreAntirabique, Commune, \
    EmployeeProfile, Patient, Animal, DossierMedical, Vaccination, Symptom, \
    PreleveMode, Epidemie, RendezVousVaccination, Echantillon, Vaccins, Facture, Caisse, TypeProtocole, \
    Preexposition, RageHumaineNotification, PostExposition, Technique, ProtocoleVaccination, MAPI, LotVaccin, \
    InjectionImmunoglobuline, ObservationPostVaccination, WhatsAppMessageLog
from rage_INHP.resources import RageHumaineNotificationResource, ProtocoleVaccinationResource, VaccinsResource, \
    LotVaccinResource
from rage_INHP.services import synchroniser_avec_mpi

admin.site.site_header = 'INHP CAR BACK-END CONTROLER'
admin.site.site_title = 'INHP CAR  Super Admin Pannel'
admin.site.site_url = 'http://carinhp.com/'
admin.site.index_title = 'INHP CAR '
admin.empty_value_display = '**Empty**'


# 🔹 Définition des ressources pour l'import/export
class CommuneResource(resources.ModelResource):
    class Meta:
        model = Commune
        fields = ('id', 'name', 'type', 'population', 'is_in', 'district__nom', 'geom')


class DistrictSanitaireResource(resources.ModelResource):
    class Meta:
        model = DistrictSanitaire
        fields = ('id', 'nom', 'region', 'geom', 'geojson')


class HealthRegionResource(resources.ModelResource):
    class Meta:
        model = HealthRegion
        fields = ('id', 'name', 'poles')


# 🔹 Ajout du module ImportExportModelAdmin
@admin.register(Commune)
class CommuneAdmin(ImportExportModelAdmin, LeafletGeoAdmin):
    resource_class = CommuneResource
    list_display = ('name', 'district', 'population')
    search_fields = ('name', 'district__nom')
    list_filter = ('district',)
    ordering = ('name',)
    autocomplete_fields = ['district']

    # Personnalisation de Leaflet pour afficher les cartes correctement
    settings_overrides = {
        'DEFAULT_ZOOM': 7,
        'MIN_ZOOM': 5,
        'MAX_ZOOM': 28,
    }


@admin.register(DistrictSanitaire)
class DistrictSanitaireAdmin(ImportExportModelAdmin, LeafletGeoAdmin):
    resource_class = DistrictSanitaireResource
    list_display = ('nom', 'region')
    search_fields = ('nom', 'region__name')
    list_filter = ('region',)


@admin.register(CentreAntirabique)
class CentreAntirabiqueAdmin(OSMGeoAdmin):
    list_display = ('nom', 'type', 'district', 'completeness', 'version', 'date_modified')
    search_fields = ('nom', 'district__nom')
    list_filter = ('type', 'district')
    ordering = ('-date_modified',)
    default_lon = 0  # Coordonnée par défaut pour la carte
    default_lat = 5
    default_zoom = 6
    autocomplete_fields = ['district']


@admin.register(RageHumaineNotification)
class RageHumaineNotificationAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        'date_notification', 'hopital', 'agent_declarant', 'nature_exposition', 'categorie_lesion', 'evolution')
    list_filter = ('hopital', 'nature_exposition', 'categorie_lesion', 'evolution', 'date_notification')
    search_fields = ('hopital', 'agent_declarant', 'lieu_exposition')
    ordering = ('-date_notification',)
    date_hierarchy = 'date_exposition'
    list_per_page = 25
    resource_class = RageHumaineNotificationResource  # Ajout de l'exportation


class PolesRegionauxResource(resources.ModelResource):
    class Meta:
        model = PolesRegionaux
        fields = ('id', 'name')


#
@admin.register(PolesRegionaux)
class PolesRegionauxAdmin(ImportExportModelAdmin):
    resource_class = PolesRegionauxResource
    list_display = ['name']
    search_fields = ['name']


@admin.register(HealthRegion)
class HealthRegionAdmin(ImportExportModelAdmin):
    resource_class = HealthRegionResource
    list_display = ('name', 'poles')
    search_fields = ('name',)
    list_filter = ('poles',)


# Register your models here.
@admin.register(EmployeeUser)
class EmployeeUserAdmin(UserAdmin):
    model = EmployeeUser
    list_display = ('username', 'civilite', 'email', 'fonction', 'roleemployee', 'centre', 'is_active')
    list_filter = ('roleemployee', 'centre', 'civilite', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'fonction', 'centre__nom')  # adapte selon ton modèle CentreAntirabique
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': ('civilite', 'email', 'contact', 'fonction', 'roleemployee', 'centre')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'civilite', 'email', 'contact', 'fonction', 'roleemployee',
                'centre'),
        }),
    )


def synchroniser_patients_mpi(modeladmin, request, queryset):
    patients_synchronises = 0
    erreurs = []

    for patient in queryset.filter(mpi_upi__isnull=True):
        try:
            with transaction.atomic():
                mpi_upi = synchroniser_avec_mpi(patient)
                if mpi_upi:
                    if Patient.objects.filter(mpi_upi=mpi_upi).exists():
                        erreurs.append(f"⚠️ Doublon UPI {mpi_upi} ({patient})")
                        continue
                    patient.mpi_upi = mpi_upi
                    patient.save(update_fields=['mpi_upi'])
                    patients_synchronises += 1
        except Exception as e:
            erreurs.append(f"❌ Erreur {patient}: {e}")

    if patients_synchronises:
        messages.success(request, f"✅ {patients_synchronises} patients synchronisés avec succès.")

    if erreurs:
        for erreur in erreurs:
            messages.warning(request, erreur)


synchroniser_patients_mpi.short_description = "🔄 Synchroniser patients sélectionnés avec MPI"


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'code_patient', 'nom', 'prenoms',
        'contact', 'accompagnateurcontact', 'date_naissance',
        'calculate_age', 'poids', 'mpi_upi', 'created_at'
    )
    list_filter = ('status', 'gueris', 'decede', 'centre_ar', 'commune', 'created_at')
    search_fields = ('nom', 'prenoms', 'code_patient', 'contact', 'accompagnateurcontact')
    readonly_fields = ('code_patient', 'calculate_age', 'created_at')
    fieldsets = (
        ("Identité du patient", {
            'fields': (
                ('nom', 'prenoms', 'sexe'),
                ('date_naissance', 'calculate_age', 'poids'),
                ('contact', 'status'),
            )
        }),
        ("Informations complémentaires", {
            'fields': (
                'secteur_activite', 'niveau_etude',
                'commune', 'quartier', 'village',
                'centre_ar', 'num_cmu',
                'cni_num', 'cni_nni',
                'proprietaire_animal', 'typeanimal', 'autretypeanimal'
            )
        }),
        ("Accompagnateur", {
            'classes': ('collapse',),
            'fields': (
                'patient_mineur',
                ('accompagnateur', 'accompagnateurcontact'),
                ('accompagnateur_nature', 'accompagnateur_niveau_etude'),
                'accompagnateur_adresse',
            )
        }),
        ("Statut de santé", {
            'fields': (
                ('gueris', 'decede'),
                ('date_deces', 'cause_deces'),
            )
        }),
        ("Informations système", {
            'fields': ('code_patient', 'created_by', 'created_at'),
        }),
    )
    actions = [synchroniser_patients_mpi]

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True


# class VaccinationAdmin(admin.ModelAdmin):
#     list_display = ('patient', 'date_prevue', 'date_effective', 'dose_ml', 'protocole', 'lieu')
#     search_fields = ('patient__nom', 'patient__prenoms', 'protocole')
#     list_filter = ('date_prevue', 'date_effective', 'protocole')

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date_effective', 'test_sms_link')
    actions = ['envoyer_test_sms']

    def test_sms_link(self, obj):
        return format_html(
            '<a class="button" href="/admin/rage/vaccination/{}/send-sms/" target="_blank">📲 Test SMS</a>',
            obj.pk
        )
    test_sms_link.short_description = "Test SMS"
    test_sms_link.allow_tags = True

    def envoyer_test_sms(self, request, queryset):
        from .tasks import send_sms_postvaccination
        for vac in queryset:
            send_sms_postvaccination.delay(vac.pk)
        self.message_user(request, f"{queryset.count()} envois SMS planifiés.")
    envoyer_test_sms.short_description = "📲 Envoyer SMS (test)"

class EpidemieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_debut', 'date_fin', 'is_active')
    search_fields = ('nom',)
    list_filter = ('date_debut', 'date_fin')


# admin.site.register(EmployeeUser, EmployeeUserAdmin)

# admin.site.register(CentreAntirabique)
# admin.site.register(EmployeeProfile)
# admin.site.register(Patient, PatientAdmin)
admin.site.register(Animal)
admin.site.register(DossierMedical)
# admin.site.register(Vaccination, VaccinationAdmin)
admin.site.register(PreleveMode)
admin.site.register(Epidemie, EpidemieAdmin)


# @admin.register(Exposition)
# class ExpositionAdmin(admin.ModelAdmin):
#     list_display = ('id', 'patient', 'date_exposition', 'type_exposition', 'animal_concerne')
#     search_fields = ('patient__nom', 'patient__prenoms', 'lieu_exposition')
#     list_filter = ('type_exposition', 'animal_concerne', 'created_at')


# @admin.register(ProtocoleVaccination)
# class ProtocoleVaccinationAdmin(admin.ModelAdmin):
#     list_display = ('nom', 'patient', 'nombre_doses', 'intervale_jours', 'voie_administration', 'duree', 'created_at')
#     search_fields = ('patient__nom', 'nom')
#     list_filter = ('nom', 'voie_administration')
#     ordering = ('-created_at',)


@admin.register(RendezVousVaccination)
class RendezVousVaccinationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date_rendez_vous', 'dose_numero', 'est_effectue', 'protocole', 'created_at')
    search_fields = ('patient__nom', 'protocole__nom')
    list_filter = ('est_effectue', 'protocole__nom')
    ordering = ('date_rendez_vous',)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


@admin.register(Echantillon)
class EchantillonAdmin(admin.ModelAdmin):
    list_display = ('code_echantillon', 'patient', 'maladie', 'date_collect', 'site_collect', 'resultat', 'created_at')
    search_fields = ('code_echantillon', 'patient__nom', 'maladie__nom')
    list_filter = ('resultat', 'maladie')


@admin.register(Vaccins)
class VaccinsAdmin(ImportExportModelAdmin):
    resource_class = VaccinsResource
    list_display = ('nom', 'unite', 'created_by', 'created_at')
    search_fields = ['nom']
    list_filter = ['unite']
    ordering = ('-created_at',)


@admin.register(LotVaccin)
class LotVaccinAdmin(ImportExportModelAdmin):
    resource_class = LotVaccinResource
    list_display = (
        'numero_lot',
        'vaccin',
        'centre',
        'date_fabrication',
        'date_expiration',
        'quantite_initiale',
        'quantite_disponible',
    )
    list_filter = ('vaccin', 'centre', 'date_expiration')
    search_fields = ('numero_lot', 'vaccin__nom')
    date_hierarchy = 'date_expiration'
    ordering = ('-date_expiration',)


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'montant_total', 'montant_paye', 'reste_a_payer', 'statut_paiement', 'date_facture')
    search_fields = ('patient__nom',)
    list_filter = ('statut_paiement', 'date_facture')
    ordering = ('-date_facture',)


@admin.register(Caisse)
class CaisseAdmin(admin.ModelAdmin):
    list_display = ('facture', 'montant', 'mode_paiement', 'date_paiement', 'created_by')
    search_fields = ('facture__patient__nom',)
    list_filter = ('mode_paiement', 'date_paiement')
    ordering = ('-date_paiement',)


class PreexpositionInline(admin.StackedInline):
    """
    Affichage des enregistrements Preexposition directement dans l'admin Patient.
    """
    model = Preexposition
    extra = 1  # Nombre de formulaires vides à afficher par défaut


@admin.register(Preexposition)
class PreexpositionAdmin(admin.ModelAdmin):
    list_display = ('client', 'codeexpo', 'voyage', 'mise_a_jour', 'protection_rage', 'created_at')
    list_filter = ('voyage', 'mise_a_jour', 'protection_rage', 'chien_voisin', 'chiens_errants')
    search_fields = ('client__nom', 'client__prenoms', 'client__code_patient', 'dernier_var_animal_type')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'created_by', 'codeexpo',)

    fieldsets = (
        ("Patient", {"fields": ("client", "created_by")}),
        ("Motif de Vaccination", {"fields": (
            "voyage", "mise_a_jour", "protection_rage", "chien_voisin", "chiens_errants", "autre", "autre_motif")}),
        ("Canaux d'Information", {"fields": (
            "tele", "radio", "sensibilisation", "proche", "presse", "passage_car", "diff_canal", "canal_infos")}),
        ("Connaissance et Attitude", {"fields": (
            "aime_animaux", "type_animal_aime", "connait_protocole_var", "dernier_var_animal_type",
            "dernier_var_animal_date")}),
        ("Évaluation", {"fields": ("mesures_elimination_rage", "appreciation_cout_var")}),
        ("Informations Générales", {"fields": ("created_at", "codeexpo")}),
    )

    def save_model(self, request, obj, form, change):
        """Attribuer automatiquement l'utilisateur qui crée l'enregistrement."""
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()


class PatientAdmin(admin.ModelAdmin):
    """
    Personnalisation de l'affichage du modèle Patient.
    """
    list_display = ('nom', 'prenoms', 'contact', 'date_naissance', 'sexe', 'created_at')
    search_fields = ('nom', 'prenoms', 'contact')
    list_filter = ('sexe', 'created_at')
    inlines = [PreexpositionInline]  # Ajoute Preexposition directement dans Patient


@admin.register(ProtocoleVaccination)
class ProtocoleVaccinationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ProtocoleVaccinationResource

    list_display = ('nom', 'nombre_doses', 'duree', 'created_at')
    list_filter = ('nom',)
    search_fields = ('nom',)
    ordering = ('-created_at',)


@admin.register(TypeProtocole)
class TypeProtocoleAdmin(admin.ModelAdmin):
    list_display = ('nom_protocole', 'nombre_dose', 'prix')
    search_fields = ('nom_protocole',)


@admin.register(Technique)
class TechniqueAdmin(admin.ModelAdmin):
    list_display = ('nom',)


@admin.register(PostExposition)
class PostExpositionAdmin(admin.ModelAdmin):
    list_display = ('client', 'date_exposition', 'lieu_exposition', 'gravite_oms', 'created_at')
    list_filter = ('gravite_oms',)
    search_fields = ('client__nom',)
    date_hierarchy = 'date_exposition'


@admin.register(MAPI)
class MAPIAdmin(admin.ModelAdmin):
    list_display = ('patient', 'vaccination', 'date_apparition', 'gravite', 'evolution', 'created_at')
    list_filter = ('gravite', 'evolution', 'date_apparition')
    search_fields = ('patient__nom', 'patient__prenoms', 'description')
    date_hierarchy = 'date_apparition'
    ordering = ('-date_apparition',)
    raw_id_fields = ('patient', 'vaccination')  # Useful if you have many patients/vaccinations

    fieldsets = (
        ('Informations patient', {
            'fields': ('patient', 'vaccination')
        }),
        ('Détails MAPI', {
            'fields': ('date_apparition', 'description', 'gravite')
        }),
        ('Suivi médical', {
            'fields': ('traitement_administre', 'evolution')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Make created_by and created_at read-only
        if obj:  # editing an existing object
            return ('created_by', 'created_at')
        return ()


@admin.register(InjectionImmunoglobuline)
class InjectionImmunoglobulineAdmin(admin.ModelAdmin):
    list_display = ('patient', 'injection_status', 'date_injection', 'dose_ui', 'voie_injection', 'created_by')
    list_filter = ('type_produit', 'voie_injection', 'date_injection', 'refus_injection')
    search_fields = ('patient__nom', 'patient__prenom', 'type_produit', 'numero_lot', 'motif_refus')
    date_hierarchy = 'date_injection'
    readonly_fields = ('created_by', 'created_at')
    list_select_related = ('patient', 'created_by')

    fieldsets = (
        ('Informations de base', {
            'fields': ('patient', 'date_injection', 'created_by', 'created_at')
        }),
        ('Statut de l\'injection', {
            'fields': ('refus_injection', 'motif_refus'),
            'classes': ('collapse', 'wide')
        }),
        ('Détails de l\'injection', {
            'fields': ('type_produit', 'dose_ui', 'voie_injection','dose_a_injecter', 'site_injection'),
            'classes': ('collapse',)
        }),
        ('Information produit', {
            'fields': ('numero_lot', 'date_peremption', 'laboratoire_fabricant'),
            'classes': ('collapse',)
        }),
        ('Commentaires', {
            'fields': ('commentaire',),
            'classes': ('collapse',)
        }),
    )

    def injection_status(self, obj):
        if obj.refus_injection:
            return format_html(
                '<span class="badge badge-danger">Refusé</span> - {}'.format(obj.motif_refus or "Pas de motif précisé"))
        return format_html('<span class="badge badge-success">Injecté</span> - {}'.format(obj.type_produit))

    injection_status.short_description = "Statut"
    injection_status.admin_order_field = 'refus_injection'

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.refus_injection:
            # Réorganise les fieldsets si c'est un refus
            return (
                fieldsets[0],  # Informations de base
                fieldsets[1],  # Statut (qui devient plus visible)
                fieldsets[4]  # Commentaires
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # Si l'objet existe déjà
            readonly_fields.extend(['patient', 'refus_injection'])
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Si c'est une nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'created_by')


class WhatsAppMessageLogInline(admin.TabularInline):
    model = WhatsAppMessageLog
    extra = 0
    readonly_fields = ('sid', 'to', 'status', 'body', 'date_sent')
    can_delete = False
    verbose_name = "Log WhatsApp"
    verbose_name_plural = "Logs WhatsApp"


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = ('vaccination', 'to', 'status', 'date_sent')
    list_filter = ('status',)
    search_fields = ('to', 'sid')
    date_hierarchy = 'date_sent'
