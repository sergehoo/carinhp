import os
import tempfile
from datetime import timedelta, datetime, date
from io import BytesIO
from venv import logger

import qrcode
import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.serializers import serialize
from django.db import transaction, IntegrityError
from django.db.models import Q, Count, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template, render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, DeleteView, CreateView
from django_filters.views import FilterView
from django_tables2 import tables, SingleTableView, SingleTableMixin
from import_export.admin import ExportMixin
from reportlab.lib import colors
from reportlab.lib.colors import lightgrey
from reportlab.lib.pagesizes import A4, A6
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from weasyprint import HTML
from xhtml2pdf import pisa

from rage.models import HealthRegion, PolesRegionaux, Patient, ProtocoleVaccination, Vaccination, Animal, \
    RendezVousVaccination, Facture, Preexposition, PostExposition, Commune, RageHumaineNotification, CentreAntirabique, \
    DistrictSanitaire, LotVaccin, Vaccins, EmployeeUser, InjectionImmunoglobuline
from rage.tables import RendezVousTable, FactureTable, PreExpositionTable, PostExpositionTable, \
    RageHumaineNotificationTable
from rage_INHP.decorators import role_required
from rage_INHP.filters import RendezVousFilter, RageHumaineNotificationFilter
# from rage_INHP.filters import ExpositionFilter
from rage_INHP.forms import EchantillonForm, SymptomForm, \
    VaccinationForm, PaiementForm, ClientForm, PreExpositionForm, PostExpositionForm, ClientPreExpositionForm, \
    ClientPostExpositionForm, PatientRageNotificationForm, RageHumaineNotificationForm, PreExpositionUpdateForm, \
    MAPIForm, VaccinForm, LotVaccinForm, EmployeeUserForm, EmployeeUserUpdateForm, CentreAntirabiqueForm, \
    InjectionImmunoglobulineForm
from rage_INHP.services import synchroniser_avec_mpi
from rage_INHP.utils.whatsapp_service import WhatsAppService
from rage_INHP.utils.tasks import send_analysis_sms

EmployeeUser = get_user_model()


def permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)


@login_required
def menu_view(request):
    user = request.user

    # National : Voir tous les pôles régionaux et leurs régions
    if user.roleemployee == 'National':
        poles = PolesRegionaux.objects.prefetch_related('regions')

    # Régional : Voir uniquement sa région et ses districts
    elif user.roleemployee == 'Regional':
        poles = PolesRegionaux.objects.filter(regions__id=user.region_id).prefetch_related('regions')

    # District Sanitaire : Voir uniquement sa région et son district
    elif user.roleemployee == 'DistrictSanitaire':
        poles = PolesRegionaux.objects.filter(regions__districts__id=user.district_id).distinct()

    # Centre Antirabique : Voir uniquement son district
    elif user.roleemployee == 'CentreAntirabique':
        poles = PolesRegionaux.objects.filter(regions__districts__centres__employees__user=user).distinct()

    else:
        poles = []

    return render(request, 'layout/aside.html', {'poles': poles})


@login_required
def patients_geojson(request):
    patients = Patient.objects.filter(commune__isnull=False, commune__geom__isnull=False)
    data = {
        "type": "FeatureCollection",
        "features": []
    }

    for patient in patients:
        if patient.commune.geom:  # Vérification que geom n'est pas null
            lon, lat = patient.commune.geom.coords  # Extraire longitude et latitude

            # Déterminer le type de cas (Post-exposition, Pré-exposition, Notification)
            if PostExposition.objects.filter(client=patient).exists():
                patient_type = "Post-exposition"
                color = "red"  # 🔴 Rouge
            elif Preexposition.objects.filter(client=patient).exists():
                patient_type = "Pré-exposition"
                color = "blue"  # 🔵 Bleu
            elif RageHumaineNotification.objects.filter(client=patient).exists():
                patient_type = "Notification"
                color = "black"  # ⚫ Noir
            else:
                patient_type = "Inconnu"
                color = "green"  # 🟢 Par défaut

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "nom": patient.nom,
                    "prenoms": patient.prenoms,
                    "contact": patient.contact,
                    "type": patient_type,
                    "lieu_exposition": getattr(patient, "lieu_exposition", "Non renseigné"),
                    "exposition_commune": patient.commune.name,
                    "date_exposition": getattr(patient, "date_exposition", "Non renseigné"),
                    "color": color
                }
            }
            data["features"].append(feature)

    return JsonResponse(data, safe=False)  # Désactiver la protection de JsonResponse pour listes/objets JSON


#
@staff_member_required  # 🔐 Sécurité : réservé au personnel connecté à l'admin Django
def synchroniser_patients_mpi(request):
    patients_sans_upi = Patient.objects.filter(mpi_upi__isnull=True)

    résultats = []
    for patient in patients_sans_upi:
        try:
            with transaction.atomic():
                mpi_upi = synchroniser_avec_mpi(patient)
                if mpi_upi:
                    if Patient.objects.filter(mpi_upi=mpi_upi).exists():
                        résultats.append(f"⚠️ Doublon UPI {mpi_upi} pour {patient}")
                        continue
                    patient.mpi_upi = mpi_upi
                    patient.save(update_fields=['mpi_upi'])
                    résultats.append(f"✅ {patient} synchronisé (UPI: {mpi_upi})")
                else:
                    résultats.append(f"⚠️ Pas d'UPI retourné pour {patient}")
        except Exception as e:
            résultats.append(f"❌ Erreur pour {patient}: {e}")

    return JsonResponse({"résultats": résultats})


def count_cases(model, sexe, min_age, max_age):
    """
    Compte les instances de `model` pour un sexe donné et une tranche d'âge [min_age, max_age].
    """
    today = date.today()
    # date la plus ancienne = aujourd'hui moins max_age années
    start_dob = today - relativedelta(years=max_age)
    # date la plus récente = aujourd'hui moins min_age années
    end_dob = today - relativedelta(years=min_age)
    return model.objects.filter(client__sexe=sexe,
                                client__date_naissance__gte=start_dob,
                                client__date_naissance__lte=end_dob,
                                ).count()


class CADashborad(LoginRequiredMixin, TemplateView):
    template_name = "pages/dahboard-centres.html"
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()
        start_of_year = today.replace(month=1, day=1)
        start_of_last_year = (today.replace(month=1, day=1, year=today.year - 1))
        start_of_month = today.replace(day=1)
        start_of_week = today - timedelta(days=today.weekday())

        # Filtrage des cas par période
        stats_by_period = {
            "L'Annee Précédente": {
                "postexposition": PostExposition.objects.filter(date_exposition__year=start_of_last_year.year).count(),
                "preexposition": Preexposition.objects.filter(created_at__year=start_of_last_year.year).count(),
                "notification": RageHumaineNotification.objects.filter(
                    date_notification__year=start_of_last_year.year).count(),
            },
            "Cette Année": {
                "postexposition": PostExposition.objects.filter(date_exposition__year=start_of_year.year).count(),
                "preexposition": Preexposition.objects.filter(created_at__year=start_of_year.year).count(),
                "notification": RageHumaineNotification.objects.filter(
                    date_notification__year=start_of_year.year).count(),
            },
            "Ce mois ci": {
                "postexposition": PostExposition.objects.filter(date_exposition__year=today.year,
                                                                date_exposition__month=today.month).count(),
                "preexposition": Preexposition.objects.filter(created_at__year=today.year,
                                                              created_at__month=today.month).count(),
                "notification": RageHumaineNotification.objects.filter(date_notification__year=today.year,
                                                                       date_notification__month=today.month).count(),
            },
            "Cette Semaine": {
                "postexposition": PostExposition.objects.filter(date_exposition__gte=start_of_week).count(),
                "preexposition": Preexposition.objects.filter(created_at__gte=start_of_week).count(),
                "notification": RageHumaineNotification.objects.filter(date_notification__gte=start_of_week).count(),
            },
        }
        # Définition des tranches d'âge
        age_ranges = {
            "0-4 ans": (0, 4),
            "5-14 ans": (5, 14),
            "15-30 ans": (15, 30),
            "31-45 ans": (31, 45),
            "46-60 ans": (46, 60),
            "61-80 ans": (61, 80),
            "81 ans et plus": (81, 150),
            # "41 ans et plus": (41, 150),
        }
        # Statistiques par tranche d'âge, sexe et type de cas
        age_stats = {}
        for label, (min_age, max_age) in age_ranges.items():
            age_stats[label] = {
                sexe: {
                    "postexposition": count_cases(PostExposition, sexe, min_age, max_age),
                    "preexposition": count_cases(Preexposition, sexe, min_age, max_age),
                    "notification": count_cases(RageHumaineNotification, sexe, min_age, max_age),
                }
                for sexe in ("M", "F")
            }
        # for label, (min_age, max_age) in age_ranges.items():
        #     age_stats[label] = {
        #         "M": {
        #             "postexposition": PostExposition.objects.filter(
        #                 client__sexe="M",
        #                 client__date_naissance__lte=today - timedelta(days=min_age * 365),
        #                 client__date_naissance__gt=today - timedelta(days=max_age * 365),
        #             ).count(),
        #             "preexposition": Preexposition.objects.filter(
        #                 client__sexe="M",
        #                 client__date_naissance__lte=today - timedelta(days=min_age * 365),
        #                 client__date_naissance__gt=today - timedelta(days=max_age * 365),
        #             ).count(),
        #             "notification": RageHumaineNotification.objects.filter(
        #                 client__sexe="M",
        #                 client__date_naissance__lte=today - timedelta(days=min_age * 365),
        #                 client__date_naissance__gt=today - timedelta(days=max_age * 365),
        #             ).count(),
        #         },
        #         "F": {
        #             "postexposition": PostExposition.objects.filter(
        #                 client__sexe="F",
        #                 client__date_naissance__lte=today - timedelta(days=min_age * 365),
        #                 client__date_naissance__gt=today - timedelta(days=max_age * 365),
        #             ).count(),
        #             "preexposition": Preexposition.objects.filter(
        #                 client__sexe="F",
        #                 client__date_naissance__lte=today - timedelta(days=min_age * 365),
        #                 client__date_naissance__gt=today - timedelta(days=max_age * 365),
        #             ).count(),
        #             "notification": RageHumaineNotification.objects.filter(
        #                 client__sexe="F",
        #                 client__date_naissance__lte=today - timedelta(days=min_age * 365),
        #                 client__date_naissance__gt=today - timedelta(days=max_age * 365),
        #             ).count(),
        #         },
        #     }

        # Comptage des patients enregistrés ce mois
        patients_this_month = {
            "postexposition": PostExposition.objects.filter(date_exposition__gte=start_of_month).count(),
            "preexposition": Preexposition.objects.filter(created_at__gte=start_of_month).count(),
            "notification": RageHumaineNotification.objects.filter(date_notification__gte=start_of_month).count(),
        }

        # Comptage des patients enregistrés cette semaine
        patients_this_week = {
            "postexposition": PostExposition.objects.filter(date_exposition__gte=start_of_week).count(),
            "preexposition": Preexposition.objects.filter(created_at__gte=start_of_week).count(),
            "notification": RageHumaineNotification.objects.filter(date_notification__gte=start_of_week).count(),
        }

        # Statistiques des motifs de vaccination
        motifs = ["voyage", "mise_a_jour", "protection_rage", "chien_voisin", "chiens_errants", "autre"]
        context["motif_vaccination_stats"] = {
            motif: Preexposition.objects.filter(**{motif: True}).count()
            for motif in motifs
        }

        # Définir les types d'expositions à analyser
        exposition_types = [
            "morsure",
            "griffure",
            "lechage_saine",
            "lechage_lesee",
            "contactanimalpositif",
            "contactpatientpositif",
            "autre",
        ]

        # Récupérer les statistiques pour chaque type d'exposition
        stats_exposition = {
            exposition: PostExposition.objects.filter(**{exposition: True}).count()
            for exposition in exposition_types
        }

        # Ajoutez ces nouvelles données pour les graphiques
        # Données mensuelles pour les 12 derniers mois
        months = []
        postexposition_data = []
        preexposition_data = []
        notification_data = []

        for i in range(11, -1, -1):
            month_date = today - relativedelta(months=i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

            label = month_date.strftime("%b %Y")
            months.append(label)

            postexposition_data.append({
                "x": label,
                "y": PostExposition.objects.filter(
                    date_exposition__range=(month_start, month_end)
                ).count()
            })

            preexposition_data.append({
                "x": label,
                "y": Preexposition.objects.filter(
                    created_at__range=(month_start, month_end)
                ).count()
            })

            notification_data.append({
                "x": label,
                "y": RageHumaineNotification.objects.filter(
                    date_notification__range=(month_start, month_end)
                ).count()
            })

        context["chart_data"] = {
            "months": months,
            "postexposition": postexposition_data,
            "preexposition": preexposition_data,
            "notification": notification_data
        }

        centres = CentreAntirabique.objects.annotate(
            total_preexposition=Count('patient__preexposition', distinct=True),
            total_postexposition=Count('patient__patientpep', distinct=True),
            total_notifications=Count('patient__notifications_rage', distinct=True),
            total_vaccinations=Count('patient__vaccination', distinct=True),
            total_mapis=Count('patient__mapi', distinct=True),
        ).select_related('district__region__poles').order_by('-total_preexposition', '-total_postexposition',
                                                             '-total_vaccinations', '-total_mapis')

        context["centres"] = centres
        # fin stat par centre
        # debut stat par  districts
        districts = DistrictSanitaire.objects.annotate(
            total_preexposition=Count('centres__patient__preexposition', distinct=True),
            total_postexposition=Count('centres__patient__patientpep', distinct=True),
            total_notifications=Count('centres__patient__notifications_rage', distinct=True),
            total_vaccinations=Count('centres__patient__vaccination', distinct=True),
            total_mapis=Count('centres__patient__mapi', distinct=True),
        ).select_related('region__poles').order_by('-total_preexposition', '-total_postexposition',
                                                   '-total_vaccinations', '-total_mapis')
        context["district"] = districts
        # fin stat par district
        # debut stat par  regions
        regions = HealthRegion.objects.annotate(
            total_preexposition=Count('districts__centres__patient__preexposition', distinct=True),
            total_postexposition=Count('districts__centres__patient__patientpep', distinct=True),
            total_notifications=Count('districts__centres__patient__notifications_rage', distinct=True),
            total_vaccinations=Count('districts__centres__patient__vaccination', distinct=True),
            total_mapis=Count('districts__centres__patient__mapi', distinct=True),
        ).select_related('poles').order_by('-total_preexposition', '-total_postexposition', '-total_vaccinations',
                                           '-total_mapis')

        context["statts_regions"] = regions
        # fin stat par centre

        # debut stat par  pres
        poles = PolesRegionaux.objects.annotate(
            total_preexposition=Count('regions__districts__centres__patient__preexposition', distinct=True),
            total_postexposition=Count('regions__districts__centres__patient__patientpep', distinct=True),
            total_notifications=Count('regions__districts__centres__patient__notifications_rage', distinct=True),
            total_vaccinations=Count('regions__districts__centres__patient__vaccination', distinct=True),
            total_mapis=Count('regions__districts__centres__patient__mapi', distinct=True),
        ).order_by('-total_preexposition', '-total_postexposition', '-total_vaccinations', '-total_mapis')
        context["stats_poles"] = poles
        # fin stat par centre

        context["patients_this_month"] = patients_this_month
        context["patients_this_week"] = patients_this_week

        context["stats_by_period"] = stats_by_period
        context["age_stats"] = age_stats
        context["patients_geojson_url"] = "/patients_geojson/"
        return context


class CartographieDataView(LoginRequiredMixin, View):
    """
    Retourne les données des cas et des districts en GeoJSON pour l'ajax,
    avec application des filtres 'type', 'start_date', 'end_date'.
    """

    def get(self, request, *args, **kwargs):
        # Récupération des filtres de zone
        pole_id = request.GET.get('pole')
        region_id = request.GET.get('region')
        district_id = request.GET.get('district')
        # Récupération des filtres métier
        case_type = request.GET.get('type')  # 'pre', 'post', 'notification'
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Filtrage géographique
        zone_filters = {}
        if district_id:
            zone_filters['pk'] = district_id
        elif region_id:
            zone_filters['region__pk'] = region_id
        elif pole_id:
            zone_filters['region__poles__pk'] = pole_id

        districts_qs = DistrictSanitaire.objects.filter(**zone_filters)

        # Sérialisation conditionnelle selon le type
        features = []
        if not case_type or case_type in ['all', 'pre']:
            features += self.serialize_cases(Preexposition, districts_qs, 'pre', start_date, end_date)
        if not case_type or case_type in ['all', 'post']:
            features += self.serialize_cases(PostExposition, districts_qs, 'post', start_date, end_date)
        if not case_type or case_type in ['all', 'notification']:
            features += self.serialize_cases(RageHumaineNotification, districts_qs, 'notification', start_date,
                                             end_date)

        # GeoJSON des districts
        districts_geojson = CartographieView().get_districts_geojson()

        return JsonResponse({'features': features, 'districts': districts_geojson})

    def serialize_cases(self, model, districts, case_type, start_date=None, end_date=None):
        """
        Sérialise les cas en GeoJSON en utilisant client.commune.geom,
        et applique date range selon le case_type.
        """
        # Choix du champ date selon le type
        date_field = {
            'pre': 'created_at__date',
            'post': 'date_exposition',
            'notification': 'date_notification'
        }[case_type]

        # Construction du filtre
        filters = {'client__commune__district__in': districts}
        if start_date:
            filters[f'{date_field}__gte'] = start_date
        if end_date:
            filters[f'{date_field}__lte'] = end_date

        qs = model.objects.filter(**filters).select_related('client', 'client__commune')
        result = []
        for case in qs:
            loc = getattr(case.client, 'commune', None)
            if not loc or not getattr(loc, 'geom', None):
                continue
            result.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [loc.geom.x, loc.geom.y]},
                'properties': self.get_case_properties(case, loc, case_type)
            })
        return result

    def get_case_properties(self, case, location, case_type):
        """
        Construit les propriétés communes et spécifiques selon le type,
        sans lever d'erreur si date absente.
        """
        props = {
            'id': case.id,
            'type': case_type,
            'patient': f"{case.client.nom} {case.client.prenoms}",
            'commune': location.name,
            'district': location.district.nom if location.district else None,
            'region': location.district.region.name if location.district and location.district.region else None,
        }
        # Date selon le type
        date_val = None
        if case_type == 'pre':
            date_val = getattr(case, 'created_at', None)
        elif case_type == 'post':
            date_val = getattr(case, 'date_exposition', None)
        else:
            date_val = getattr(case, 'date_notification', None)
        props['date'] = date_val.isoformat() if date_val else None

        # Attributs métier
        if case_type == 'pre':
            props['nature'] = 'Pré-exposition'
            props['gravite'] = None
        elif case_type == 'post':
            props['nature'] = self.get_exposition_nature(case)
            props['gravite'] = getattr(case, 'gravite_oms', None)
        else:
            props['nature'] = getattr(case, 'nature_exposition', None)
            props['gravite'] = getattr(case, 'categorie_lesion', None)

        return props

    def get_exposition_nature(self, exposition):
        if exposition.morsure == 'Oui':            return 'Morsure'
        if exposition.griffure == 'Oui':           return 'Griffure'
        if exposition.lechage_lesee == 'Oui':      return 'Léchage lésé'
        if exposition.contactanimalpositif == 'Oui': return 'Contact animal positif'
        return 'Autre'


class CartographieView(LoginRequiredMixin, TemplateView):
    template_name = "pages/cartographie.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'districts_geojson': self.get_districts_geojson(),
            'poles': PolesRegionaux.objects.all().order_by('name'),
            'regions': HealthRegion.objects.select_related('poles').order_by('name'),
            'districts': DistrictSanitaire.objects.select_related('region').order_by('nom'),
        })
        return ctx

    def get_districts_geojson(self):
        qs = DistrictSanitaire.objects.annotate(
            pre_count=self._case_count_subquery(Preexposition, 'client__commune__district'),
            post_count=self._case_count_subquery(PostExposition, 'client__commune__district'),
            notif_count=self._case_count_subquery(RageHumaineNotification, 'client__commune__district')
        ).annotate(
            total_cases=Coalesce('pre_count', 0) + Coalesce('post_count', 0) + Coalesce('notif_count', 0)
        ).select_related('region')

        features = []
        for d in qs:
            if not d.geom:
                continue
            features.append({
                'type': 'Feature',
                'geometry': {'type': d.geom.geom_type, 'coordinates': list(d.geom.coords)},
                'properties': {
                    'id': d.id,
                    'nom': d.nom,
                    'region': d.region.name if d.region else None,
                    'case_count': d.total_cases,
                    'color': self.get_color_for_count(d.total_cases)
                }
            })
        return {'type': 'FeatureCollection', 'features': features}

    def _case_count_subquery(self, model, path):
        return Coalesce(
            Subquery(
                model.objects.filter(**{path: OuterRef('pk')})
                .values(path)
                .annotate(count=Count('pk'))
                .values('count')[:1]
            ), 0
        )

    def get_color_for_count(self, count):
        if count == 0:    return '#f8f9fa'
        if count <= 3:    return '#ffeda0'
        if count <= 10:   return '#feb24c'
        return '#f03b20'


class DistrictDashborad(LoginRequiredMixin, TemplateView):
    template_name = "pages/index.html"

    @method_decorator(role_required('DistrictSanitaire'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class RegionDashborad(LoginRequiredMixin, TemplateView):
    template_name = "pages/index.html"

    @method_decorator(role_required('Regional'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class NationalDashborad(LoginRequiredMixin, TemplateView):
    template_name = "pages/index.html"

    @method_decorator(role_required('National'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ------------------------------ Les Vues des ressources-------------------------------------------------------


# ------------------------------ Donnees des patients ----------------------------------------------------------

class PatientListView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/patients/patient_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer les paramètres de recherche
        search = self.request.GET.get('search', '')
        genre = self.request.GET.get('genre', '')
        nationalite = self.request.GET.get('nationalite', '')
        status = self.request.GET.get('status', '')
        # Filtrer les patients du même centre que l'employé connecté
        user_centre = self.request.user.centre  # ⚡ Ici on récupère le centre de l'employé

        queryset = Patient.objects.filter(centre_ar=user_centre)
        # Filtrer les patients

        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(prenoms__icontains=search))

        if genre:
            queryset = queryset.filter(genre=genre)

        if nationalite:
            queryset = queryset.filter(nationalite=nationalite)

        if status:
            queryset = queryset.filter(status=status)

        # Ajouter les patients filtrés au contexte
        context['patients'] = queryset
        return context


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = ClientForm
    template_name = 'pages/patients/patient_form.html'  # Template pour afficher le formulaire
    success_url = reverse_lazy('patient_list')  # Redirige après la soumission réussie

    def form_valid(self, form):
        """ Méthode appelée si le formulaire est valide """
        response = super().form_valid(form)
        messages.success(self.request, "Le patient a été ajouté avec succès ! ✅")
        return response

    def form_invalid(self, form):
        """ Méthode appelée si le formulaire contient des erreurs """
        messages.error(self.request, "Une erreur s'est produite. Vérifiez le formulaire ❌")
        return super().form_invalid(form)


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = 'pages/patients/dossier_patient.html'
    context_object_name = 'patientdossier'


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient
    template_name = 'patients/patient_form.html'
    fields = '__all__'  # Remplace par les champs nécessaires
    success_url = reverse_lazy('patient_list')


class PatientDeleteView(LoginRequiredMixin, DeleteView):
    model = Patient
    template_name = 'patients/patient_confirm_delete.html'
    success_url = reverse_lazy('patient_list')


# def formulaire_inscription(request):
#     if request.method == "POST":
#         client_form = ClientForm(request.POST)
#         motif_formset = MotifVaccinationFormSet(request.POST)
#         info_formset = InformationVaccinationFormSet(request.POST)
#         connaissance_formset = ConnaissanceAttitudeFormSet(request.POST)
#         suivi_formset = SuiviVaccinationFormSet(request.POST)
#         # agent_formset = EnregistrementAgentFormSet(request.POST)  # Décommenté
#
#         if (
#                 client_form.is_valid()
#                 and motif_formset.is_valid()
#                 and info_formset.is_valid()
#                 and connaissance_formset.is_valid()
#                 and suivi_formset.is_valid()
#                 # and agent_formset.is_valid()
#         ):
#             client = client_form.save()
#
#             # Lier les formsets au client
#             motif_formset.instance = client
#             info_formset.instance = client
#             connaissance_formset.instance = client
#             suivi_formset.instance = client
#             # agent_formset.instance = client  # Ajouté
#
#             # Sauvegarde des formsets
#             motif_formset.save()
#             info_formset.save()
#             connaissance_formset.save()
#             suivi_formset.save()
#             # agent_formset.save()
#
#             return redirect('success_page')
#
#     else:
#         client_form = ClientForm()
#         motif_formset = MotifVaccinationFormSet()
#         info_formset = InformationVaccinationFormSet()
#         connaissance_formset = ConnaissanceAttitudeFormSet()
#         suivi_formset = SuiviVaccinationFormSet()
#         # agent_formset = EnregistrementAgentFormSet()  # Ajouté
#
#     return render(request, 'pages/expositions/declaration.html', {
#         'client_form': client_form,
#         'motif_formset': motif_formset,
#         'info_formset': info_formset,
#         'connaissance_formset': connaissance_formset,
#         'suivi_formset': suivi_formset,
#         # 'agent_formset': agent_formset,  # Ajouté
#     })


# ------------------------------ Fin Donnees des patients ----------------------------------------------------------

class DeclarationTemplate(LoginRequiredMixin, TemplateView):
    template_name = 'pages/expositions/declaration.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'client_form': ClientForm(),
            # 'motif_formset': MotifVaccinationFormSet(),
            # 'agent_formset': EnregistrementAgentFormSet(),
        })
        return context

    # def post(self, request, *args, **kwargs):
    #     client_form = ClientForm(request.POST)
    #
    #     if client_form.is_valid():
    #         client = client_form.save(commit=False)
    #         client.save()
    #
    #         # motif_formset = MotifVaccinationFormSet(request.POST, instance=client)
    #         # info_formset = InformationVaccinationFormSet(request.POST, instance=client)
    #
    #
    #         if (
    #                 motif_formset.is_valid()
    #                 and info_formset.is_valid()
    #                 and connaissance_formset.is_valid()
    #                 and suivi_formset.is_valid()
    #         ):
    #             motif_formset.save()
    #             info_formset.save()
    #             connaissance_formset.save()
    #             suivi_formset.save()
    #
    #             messages.success(request, "Le dossier de vaccination a été enregistré avec succès ! ✅")
    #             return redirect('success_page')
    #         else:
    #             messages.error(request,
    #                            "Une erreur s'est produite lors de l'enregistrement. Veuillez vérifier les informations.")
    #             print("Formset errors:")
    #             print(motif_formset.errors)
    #             print(info_formset.errors)
    #             print(connaissance_formset.errors)
    #             print(suivi_formset.errors)
    #
    #     else:
    #         messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    #         print("Client form errors:", client_form.errors)
    #
    #     return self.render_to_response(self.get_context_data(
    #         client_form=client_form,
    #         motif_formset=motif_formset,
    #         info_formset=info_formset,
    #         connaissance_formset=connaissance_formset,
    #         suivi_formset=suivi_formset,
    #     ))


@login_required
def verifier_patient_mpi(patient_temp):
    return Patient.objects.filter(
        nom__iexact=patient_temp.nom,
        prenoms__iexact=patient_temp.prenoms,
        date_naissance=patient_temp.date_naissance,
        sexe=patient_temp.sexe
    ).first()


@login_required
def comparer_patients(patient_local, patient_mpi):
    champs = ['contact', 'cni_num', 'cni_nni', 'commune_id', 'quartier', 'village']
    differences = {}
    for champ in champs:
        local = getattr(patient_local, champ, None)
        distant = getattr(patient_mpi, champ, None)
        if local != distant:
            differences[champ] = {"local": local, "mpi": distant}
    return differences


# @method_decorator(login_required, name='dispatch')
class PreExpositionCreateView(View):
    template_name = "pages/expositions/preexposition_form.html"

    def get(self, request):
        patient_form = ClientForm()
        exposition_form = PreExpositionForm()
        return render(request, self.template_name, {
            "patient_form": patient_form,
            "exposition_form": exposition_form
        })

    def post(self, request):
        patient_form = ClientForm(request.POST)
        exposition_form = PreExpositionForm(request.POST)

        if patient_form.is_valid() and exposition_form.is_valid():
            try:
                with transaction.atomic():
                    # 🎯 Création du Patient

                    patient = patient_form.save(commit=False)
                    patient.created_by = request.user
                    if hasattr(request.user, 'centre'):
                        patient.centre_ar = request.user.centre
                    patient.save()

                    # 🎯 Création de la Pré-Exposition
                    preexposition = exposition_form.save(commit=False)
                    preexposition.client = patient
                    preexposition.created_by = request.user
                    preexposition.save()

                    # 🎯 Gestion du protocole et création des rendez-vous
                    protocole = exposition_form.cleaned_data.get(
                        'protocole_vaccination') or ProtocoleVaccination.objects.filter(
                        nom="ID-PrEP"
                    ).first()

                    if protocole and protocole.nombre_visite and protocole.nombre_doses and protocole.nbr_dose_par_rdv:
                        intervals_raw = [
                            protocole.intervale_visite1_2,
                            protocole.intervale_visite2_3,
                            protocole.intervale_visite3_4,
                            protocole.intervale_visite4_5,
                        ]

                        try:
                            intervals = [int(i.replace("Jours", "").strip()) if i else None for i in intervals_raw]
                        except ValueError:
                            intervals = [None] * 4

                        date_rdv = now().date()
                        dose_numero = 1
                        doses_restantes = protocole.nombre_doses
                        visites_max = protocole.nombre_visite
                        dose_par_rdv = protocole.nbr_dose_par_rdv or 1
                        duree_max = timedelta(days=protocole.duree) if protocole.duree else None
                        date_limite = date_rdv + duree_max if duree_max else None

                        visites_creees = 0
                        interval_index = 0

                        while doses_restantes > 0 and visites_creees < visites_max:
                            if date_limite and date_rdv > date_limite:
                                break

                            doses_a_admin = min(dose_par_rdv, doses_restantes)

                            RendezVousVaccination.objects.create(
                                patient=patient,
                                preexposition=preexposition,
                                protocole=protocole,
                                date_rendez_vous=date_rdv,
                                dose_numero=dose_numero,
                                ordre_rdv=visites_creees + 1,
                                est_effectue=False,
                                created_by=request.user
                            )

                            dose_numero += doses_a_admin
                            doses_restantes -= doses_a_admin
                            visites_creees += 1

                            if interval_index < len(intervals) and intervals[interval_index]:
                                date_rdv += timedelta(days=intervals[interval_index])
                            interval_index += 1

                        # 🗓️ Liste des RDV
                        rendez_vous_dates = RendezVousVaccination.objects.filter(
                            preexposition=preexposition
                        ).order_by('date_rendez_vous')

                        liste_rdv_str = "\n".join(
                            [f"- {rdv.date_rendez_vous.strftime('%d/%m/%Y')}" for rdv in rendez_vous_dates]
                        )

                        # 📨 Message formaté
                        message = (
                            f"Bonjour {patient.nom}, vous êtes inscrit(e) à la vaccination antirabique (PrEP) à l’INHP.\n\n"
                            "📅 Vos rendez-vous sont prévus aux dates suivantes :\n"
                            f"{liste_rdv_str}\n\n"
                            f"8h-15h"
                            "Merci de respecter ces rendez-vous pour une bonne protection.\n"
                            "💪L’équipe INHP est avec vous !"
                        )
                        # message = (
                        #     f"INHP : Bonjour {patient.nom}, vos RDV PrEP rage sont fixés aux dates : {dates}. "
                        #     "Respectez-les pour une bonne protection. 💪 L’INHP est avec vous !"
                        # )

                        # 📲 Envoi SMS via Celery
                        def try_send_sms(number, msg):
                            if number:
                                try:
                                    send_analysis_sms.delay(str(number), msg)
                                except Exception as e:
                                    print(f"[❌] Erreur d’envoi SMS à {number} : {e}")

                        # Envoi au patient uniquement
                        try_send_sms(patient.contact, message)

                    messages.success(request, "✅ Patient, pré-exposition et rendez-vous enregistrés avec succès.")
                    return redirect(reverse("preexposition_list"))

            except Exception as e:
                messages.error(request, f"❌ Une erreur est survenue : {str(e)}")

        else:
            # Si erreurs de formulaire
            error_messages = [
                                 f"<strong>{field.label if hasattr(field, 'label') else field}</strong> : {', '.join(errors)}"
                                 for field, errors in patient_form.errors.items()
                             ] + [
                                 f"<strong>{field.label if hasattr(field, 'label') else field}</strong> : {', '.join(errors)}"
                                 for field, errors in exposition_form.errors.items()
                             ]
            error_text = "Veuillez corriger les erreurs du formulaire :<br>" + "<br>".join(error_messages)
            messages.error(request, error_text)

        return render(request, self.template_name, {
            "patient_form": patient_form,
            "exposition_form": exposition_form
        })


@login_required
def fichePreExpoPDF(request, pk):
    preexposition = get_object_or_404(
        Preexposition.objects.select_related('created_by__centre'),
        pk=pk
    )

    vaccinations = Vaccination.objects.filter(patient=preexposition.client).order_by('date_effective')
    # Convertir l'objet Preexposition en dictionnaire
    preexposition_data = model_to_dict(preexposition)

    # Vérifier que le centre est disponible
    centre_nom = preexposition.created_by.centre.nom if preexposition.created_by and preexposition.created_by.centre else "Non renseigné"

    # Vérifier que le client existe avant d'ajouter ses données
    if preexposition.client:
        client_data = model_to_dict(preexposition.client)
    else:
        client_data = {}

    # Ajouter les vaccinations et autres informations
    context = {
        'centre_nom': centre_nom,  # Nom du centre antirabique
        'preexposition': preexposition_data,  # Données de la préexposition
        'client': client_data,  # Données du patient
        'date_creation': preexposition.created_at.strftime('%d/%m/%Y'),  # Formatage de la date
        'numero': preexposition.codeexpo,  # Formatage de la date
        'vaccinations': vaccinations,  # Liste des vaccinations associées
        'mshplogo': request.build_absolute_uri('/static/assets/media/mshp.png'),
        'inhplogo': request.build_absolute_uri('/static/assets/media/logos/logo-001_0.png'),
    }

    # Charger et rendre le template
    template_path = 'pdf/preexpofiche.html'
    template = get_template(template_path)
    html = template.render(context)

    # Générer le fichier PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PreExposition_{preexposition.client.nom}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)

    return response


@login_required
def fichePostExpoPDF(request, pk):
    postexposition = get_object_or_404(
        PostExposition.objects.select_related('created_by__centre'),
        pk=pk
    )

    # Vérifier si le patient existe avant de récupérer ses vaccinations
    vaccinations = Vaccination.objects.filter(patient=postexposition.client).order_by(
        'date_effective') if postexposition.client else []

    # Convertir l'objet PostExposition en dictionnaire
    postexposition_data = model_to_dict(postexposition)

    # Vérifier que le centre est disponible
    centre_nom = postexposition.created_by.centre.nom if postexposition.created_by and postexposition.created_by.centre else "Non renseigné"

    # Vérifier que le client existe avant d'ajouter ses données
    client_data = model_to_dict(postexposition.client) if postexposition.client else {}

    # Ajouter les vaccinations et autres informations
    context = {
        'centre_nom': centre_nom,  # Nom du centre antirabique
        'postexposition': postexposition_data,  # Données de la post-exposition
        'client': client_data,  # Données du patient
        'date_creation': postexposition.created_at.strftime('%d/%m/%Y'),  # Formatage de la date
        'numero': postexposition.pk,  # Identifiant unique de l'exposition
        'vaccinations': vaccinations,  # Liste des vaccinations associées
        'mshplogo': request.build_absolute_uri('/static/assets/media/mshp.png'),
        'inhplogo': request.build_absolute_uri('/static/assets/media/logos/logo-001_0.png'),
    }

    # Charger et rendre le template
    template_path = 'pdf/postexpofiche.html'  # Correction du template
    template = get_template(template_path)
    html = template.render(context)

    # Générer le fichier PDF
    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="PostExposition_{postexposition.client.nom if postexposition.client else "Inconnu"}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)

    return response


@login_required
def ajouter_mapi(request, vaccination_id):
    vaccination = get_object_or_404(Vaccination, id=vaccination_id)
    patient = vaccination.patient

    if request.method == 'POST':
        form = MAPIForm(request.POST)
        if form.is_valid():
            mapi = form.save(commit=False)
            mapi.vaccination = vaccination
            mapi.patient = patient
            mapi.created_by = request.user
            mapi.save()
            messages.success(request, "MAPI ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de l'ajout du MAPI.")
    return redirect('ta_vue_de_liste')  # Remplace par la bonne vue


# Pre-Expositions
class PreExpositionListView(LoginRequiredMixin, SingleTableView):
    model = Preexposition
    table_class = PreExpositionTable
    template_name = "pages/expositions/preexposition_list.html"


class PreExpositionDetailView(LoginRequiredMixin, DetailView):
    model = Preexposition
    template_name = "pages/expositions/preexposition_detail.html"
    context_object_name = "preexposition"


class PreExpositionUpdateView(LoginRequiredMixin, UpdateView):
    model = Preexposition
    # form_class = PreExpositionForm
    form_class = PreExpositionUpdateForm
    template_name = "pages/expositions/preexposition_update.html"
    success_url = reverse_lazy("preexposition_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Modifier une pré-exposition"
        context['page_subtitle'] = f"Mise à jour du dossier {self.object.codeexpo}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Le dossier de vaccination a été mis à jour avec succès ! ✅")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs du formulaire.")
        return super().form_invalid(form)


class PreExpositionDeleteView(LoginRequiredMixin, DeleteView):
    model = Preexposition
    template_name = "pages/expositions/preexposition_confirm_delete.html"
    success_url = reverse_lazy("preexposition_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Le dossier de vaccination a été supprimé avec succès ! 🗑️")
        return super().delete(request, *args, **kwargs)


# @login_required
# def add_injection_immunoglobuline(request, patient_id):
#     patient = get_object_or_404(Patient, pk=patient_id)
#
#     if request.method == 'POST':
#         form = InjectionImmunoglobulineForm(request.POST)
#         if form.is_valid():
#             injection = form.save(commit=False)
#             injection.created_by = request.user
#             injection.patient = patient
#             injection.save()
#             messages.success(request, "Informations enregistrées avec succès.")
#             return redirect('vaccin-rdv-list')
#         else:
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, f"{form.fields.get(field).label or field} : {error}")
#     else:
#         form = InjectionImmunoglobulineForm(initial={'patient': patient})
#
#     return render(request, 'vaccins/injection_form.html', {
#         'form': form,
#         'patient': patient,
#     })


# ✅ Vue Liste des PostExposition avec django-tables2

@login_required
def add_injection_immunoglobuline(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == 'POST':
        form = InjectionImmunoglobulineForm(request.POST)

        if form.is_valid():
            dose_ui = form.cleaned_data.get('dose_ui')
            refus = form.cleaned_data.get('refus_injection', False)

            if not refus:
                dose_max = patient.dose_immunoglobuline_ui

                if dose_ui and dose_max and dose_ui > dose_max:
                    messages.error(
                        request,
                        f"La dose injectée ({dose_ui} UI) dépasse la dose maximale prescrite ({dose_max} UI)."
                    )
                    return redirect('vaccin-rdv-list')

            injection = form.save(commit=False)
            injection.created_by = request.user
            injection.patient = patient
            injection.save()

            messages.success(request, "Informations enregistrées avec succès.")
            return redirect('vaccin-rdv-list')

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields.get(field).label or field} : {error}")

    else:
        form = InjectionImmunoglobulineForm(initial={'patient': patient})

    return redirect('vaccin-rdv-list')


class PostExpositionListView(SingleTableView, LoginRequiredMixin):
    model = PostExposition
    table_class = PostExpositionTable
    template_name = "pages/postexposition/postexposition_list.html"
    qs = PostExposition.objects.select_related('client').prefetch_related('client__patients_immuno')


def get_communes(request):
    query = request.GET.get('query', '')
    communes = Commune.objects.filter(name__icontains=query).values('id', 'name')
    return JsonResponse(list(communes), safe=False)


def commune_autocomplete(request):
    query = request.GET.get('q', '')
    results = Commune.objects.filter(name__icontains=query).values('id', 'name')[:10]
    formatted = [{'id': r['id'], 'text': r['name']} for r in results]
    return JsonResponse({'results': formatted})


def generate_avis_surveillance(request, exposition_id):
    exposition = PostExposition.objects.select_related('client', 'created_by').get(id=exposition_id)
    patient = exposition.client
    centre = request.user.centre

    html_string = render_to_string("pdf/avis_prophylaxie.html", {
        "exposition": exposition,
        "centre": centre,
        "proprio_nom": exposition.nom_proprietaire or patient.accompagnateur,
        "proprio_contact": exposition.contact_proprietaire or patient.accompagnateur_contact,
        "today": date.today()
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    result = tempfile.NamedTemporaryFile(delete=True)
    html.write_pdf(target=result.name)

    with open(result.name, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="avis_surveillance_{patient.nom}.pdf"'
        return response


# @method_decorator(login_required, name='dispatch')
class PostExpositionCreateView(LoginRequiredMixin, View):
    template_name = "pages/expositions/postexposition_form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "patient_form": ClientForm(),
            "exposition_form": PostExpositionForm()
        })

    def post(self, request):
        patient_form = ClientForm(request.POST)
        exposition_form = PostExpositionForm(request.POST, request.FILES)

        if not request.user.is_authenticated or not isinstance(request.user, EmployeeUser):
            messages.error(request, "Vous devez être connecté avec un compte employé pour effectuer cette action.")
            return redirect('account_login')

        if patient_form.is_valid() and exposition_form.is_valid():
            with transaction.atomic():
                # 🔁 Commune : si texte libre, la créer
                commune_field = patient_form.cleaned_data.get('commune')

                if isinstance(commune_field, str):
                    commune_name = commune_field.strip()
                    if commune_name:
                        commune, _ = Commune.objects.get_or_create(name=commune_name, defaults={'type': 'Commune'})
                        patient_form.instance.commune = commune
                elif isinstance(commune_field, Commune):
                    patient_form.instance.commune = commune_field

                # 🧍 Patient : chercher ou créer
                patient = Patient.objects.filter(
                    nom=patient_form.cleaned_data['nom'],
                    prenoms=patient_form.cleaned_data['prenoms'],
                    date_naissance=patient_form.cleaned_data['date_naissance'],
                ).first()

                if not patient:
                    patient = patient_form.save(commit=False)
                    patient.created_by = request.user
                    patient.centre_ar = request.user.centre
                    patient = patient_form.save()
                else:
                    patient_form.instance = patient
                    updated_patient = patient_form.save(commit=False)
                    updated_patient.centre_ar = updated_patient.centre_ar or request.user.centre
                    patient = patient_form.save()

                # 📄 PostExposition
                postexposition = exposition_form.save(commit=False)
                postexposition.client = patient
                postexposition.created_by = request.user

                postexposition.temps_saisie = exposition_form.cleaned_data.get('temps_saisie') or 0

                # ✅ Injection si "Propriétaire animal"
                accompagnateur_nature = patient_form.cleaned_data.get("accompagnateur_nature")
                if accompagnateur_nature and isinstance(accompagnateur_nature,
                                                        str) and accompagnateur_nature.strip() == "Propriétaire animal":
                    postexposition.connais_proprio = "Oui"
                    postexposition.retour_info_proprietaire = "Oui"
                    postexposition.nom_proprietaire = patient_form.cleaned_data.get("accompagnateur", "")
                    postexposition.contact_proprietaire = patient_form.cleaned_data.get("accompagnateurcontact", "")

                postexposition.save()

                # 🗓️ Génération des rendez-vous selon protocole
                protocole = exposition_form.cleaned_data.get('protocole_vaccination') or \
                            ProtocoleVaccination.objects.filter(nom="ID-PEP").first()

                if protocole and protocole.nombre_visite and protocole.nombre_doses:
                    intervals_raw = [
                        protocole.intervale_visite1_2,
                        protocole.intervale_visite2_3,
                        protocole.intervale_visite3_4,
                        protocole.intervale_visite4_5
                    ]

                    try:
                        intervals = [int(i.replace("Jours", "").strip()) if i else None for i in intervals_raw]
                    except ValueError:
                        intervals = [None] * 4

                    date_rdv = now().date()
                    dose_numero = 1
                    doses_restantes = protocole.nombre_doses
                    visites_max = protocole.nombre_visite
                    dose_par_rdv = protocole.nbr_dose_par_rdv or 1
                    duree_max = timedelta(days=protocole.duree) if protocole.duree else None
                    date_limite = date_rdv + duree_max if duree_max else None

                    visites_creees = 0
                    interval_index = 0

                    while doses_restantes > 0 and visites_creees < visites_max:
                        if date_limite and date_rdv > date_limite:
                            break

                        doses_a_admin = min(dose_par_rdv, doses_restantes)

                        RendezVousVaccination.objects.create(
                            patient=patient,
                            postexposition=postexposition,
                            protocole=protocole,
                            date_rendez_vous=date_rdv,
                            dose_numero=dose_numero,
                            ordre_rdv=visites_creees + 1,
                            est_effectue=False,
                            created_by=request.user
                        )

                        dose_numero += doses_a_admin
                        doses_restantes -= doses_a_admin
                        visites_creees += 1

                        if interval_index < len(intervals) and intervals[interval_index]:
                            date_rdv += timedelta(days=intervals[interval_index])
                        interval_index += 1
                    # 📲 Envoi du SMS de confirmation au patient
                    rendez_vous_dates = RendezVousVaccination.objects.filter(postexposition=postexposition).order_by(
                        'date_rendez_vous')

                    liste_rdv_str = ", ".join([
                        rdv.date_rendez_vous.strftime('%d/%m/%Y') for rdv in rendez_vous_dates
                    ])

                    # 📨 Message version courte (≤160 caractères)
                    # message = (
                    #     f"INHP : Bonjour {patient.nom}, vos rendez-vous pour la vaccination antirabique (PEP) sont prévus le {liste_rdv_str}. "
                    #     "Merci de bien les respecter. L’INHP vous accompagne."
                    # )
                    message = (
                        f"Bonjour {patient.nom}, vous êtes enregistré(e) pour une prise en charge antirabique (PEP).\n"
                        f"📅Vos rendez-vous de vaccination sont prévus aux dates suivantes : \n{liste_rdv_str}. \n\n"
                        "Merci de les respecter pour votre santé. \n💪L’équipe INHP vous accompagne."
                    )

                    # Gravité OMS déterminée automatiquement à la sauvegarde
                    if postexposition.gravite_oms == "III":
                        message_immuno = (
                            f"Attention ! Votre exposition est classée de gravité OMS III. Une injection d’immunoglobuline est nécessaire "
                            "le plus tôt possible. Merci de vous rapproché de votre consillé INHP au centre de vaccination le plus proche"
                        )
                    else:
                        message_immuno = None

                    # 📦 Envoi SMS via Celery
                    def try_send_sms(number, msg):
                        if number:
                            try:
                                send_analysis_sms.delay(str(number), msg)
                            except Exception as e:
                                print(f"[❌] Erreur d’envoi SMS à {number} : {e}")

                    # Envoi au patient

                    try_send_sms(patient.contact, message)

                    if message_immuno:
                        try_send_sms(patient.contact, message_immuno)

                messages.success(request, "✅ Dossier enregistré avec succès.")
                return redirect(reverse("postexposition_list"))

        else:
            # 🐞 Log erreurs pour debug
            print("--- Patient Form Errors ---")
            print(patient_form.errors)
            print("--- Exposition Form Errors ---")
            print(exposition_form.errors)
            for field, errors in exposition_form.errors.items():
                for error in errors:
                    messages.error(request, f"{exposition_form.fields.get(field).label or field} : {error}")

            messages.error(request, "❌ Erreur lors de l'enregistrement. Merci de corriger les champs invalides.")

        return render(request, self.template_name, {
            "patient_form": patient_form,
            "exposition_form": exposition_form,
            'can_edit': True,
        })


# ✅ Vue Détail
class PostExpositionDetailView(LoginRequiredMixin, DetailView):
    model = PostExposition
    template_name = "pages/postexposition/postexposition_detail.html"


# ✅ Vue Mise à Jour
class PostExpositionUpdateView(LoginRequiredMixin, UpdateView):
    model = PostExposition
    form_class = PostExpositionForm
    template_name = "pages/postexposition/postexposition__update_form.html"  # ⚠️ nouveau template
    success_url = reverse_lazy("postexposition_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'patient_form' not in context:
            context['patient_form'] = ClientForm(instance=self.object.client)
        context['exposition_form'] = context.get('form')
        return context

    def form_valid(self, form):
        # Enregistre d’abord le patient s’il a été modifié
        patient_form = ClientForm(self.request.POST, self.request.FILES, instance=self.object.client)
        if patient_form.is_valid():
            patient_form.save()
            messages.success(self.request, "Le dossier post-exposition a été mis à jour avec succès ! ✅")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs du formulaire.")
        return self.render_to_response(self.get_context_data(form=form))


# ✅ Vue Suppression
class PostExpositionDeleteView(LoginRequiredMixin, DeleteView):
    model = PostExposition
    template_name = "pages/postexposition/postexposition_confirm_delete.html"
    success_url = reverse_lazy("postexposition_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Le dossier post-exposition a été supprimé avec succès ! 🗑️")
        return super().delete(request, *args, **kwargs)


# fin des pre expositions


# def generate_exposition_pdf(request, exposition_id):
#     # Récupérer l'exposition depuis la base de données
#     exposition = Exposition.objects.get(id=exposition_id)
#
#     # Créer une réponse HTTP avec le bon type MIME pour le PDF
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="Exposition_{exposition.id}.pdf"'
#
#     # Créer un buffer mémoire pour le PDF
#     buffer = BytesIO()
#     pdf = canvas.Canvas(buffer, pagesize=A4)
#     pdf.setTitle(f"Exposition - {exposition.patient.nom}")
#
#     # Définir les marges et la position initiale du texte
#     x = 50
#     y = 800
#     line_height = 20
#
#     # Titre du document
#     pdf.setFont("Helvetica-Bold", 16)
#     pdf.drawString(x, y, "Formulaire d'Exposition")
#     y -= 40
#
#     # Style des champs
#     pdf.setFont("Helvetica", 12)
#
#     def draw_label_value(label, value):
#         """ Fonction pour dessiner un label et sa valeur sur le PDF """
#         nonlocal y
#         pdf.setFillColor(colors.black)
#         pdf.drawString(x, y, f"{label}:")
#         pdf.setFillColor(colors.blue)
#         pdf.drawString(x + 150, y, str(value) if value else "N/A")
#         y -= line_height
#
#     # Remplir les informations dans le PDF
#     draw_label_value("Nom du patient", exposition.patient.nom)
#     draw_label_value("Type d'exposition", exposition.get_type_exposition_display())
#     draw_label_value("Date d'exposition", exposition.date_exposition)
#     draw_label_value("Lieu d'exposition", exposition.lieu_exposition)
#     draw_label_value("Commune", exposition.commune)
#     draw_label_value("Quartier", exposition.quartier)
#     draw_label_value("Animal concerné", exposition.get_animal_concerne_display())
#     draw_label_value("Circonstances", exposition.circonstance)
#     draw_label_value("Nature de l'exposition", exposition.nature_exposition)
#     draw_label_value("Siège de l'exposition", exposition.siege_exposition)
#     draw_label_value("Saignement immédiat", "Oui" if exposition.saignement_immediat else "Non")
#     draw_label_value("Vêtements présents", "Oui" if exposition.vetements_presents else "Non")
#     draw_label_value("État des vêtements", exposition.vetements_etat)
#     draw_label_value("Nombre de lésions", exposition.nombre_lesions)
#     draw_label_value("Gravité des lésions", exposition.gravite_lesions)
#     draw_label_value("Prise en charge", "Oui" if exposition.prise_en_charge else "Non")
#     draw_label_value("Traitements administrés", exposition.traitements_administres)
#
#     # Sauvegarde et retour du PDF
#     pdf.showPage()
#     pdf.save()
#     pdf_data = buffer.getvalue()
#     buffer.close()
#     response.write(pdf_data)
#
#     return response
#

# -------------------------------------------- Exposition de la rage ----------------------------

# class ExpositionListView(ListView):
#     model = Exposition
#     template_name = 'pages/expositions/exposition_list.html'
#     context_object_name = 'expositions'
#     ordering = ['-created_at']


# class ExpositionListView(SingleTableView, FilterView):
#     model = Exposition
#     table_class = ExpositionTable
#     template_name = 'pages/expositions/exposition_list.html'
#     filterset_class = ExpositionFilter
#     paginate_by = 10  # Nombre d'éléments par page
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         filterset_class = self.get_filterset_class()  # Récupération de la classe du filtre
#         if filterset_class:
#             context['filter'] = filterset_class(self.request.GET, queryset=self.get_queryset())
#         return context
#
#
# @login_required
# def ajouterProtocole(request, exposition_id):
#     exposition = Exposition.objects.get(pk=exposition_id)
#     if request.method == 'POST':
#         form = ProtocoleVaccinationForm(request.POST)
#         if form.is_valid():
#             protocole = form.save(commit=False)
#             protocole.patient = exposition.patient  # Ajout du patient
#             protocole.created_by = request.user  # Ajout de l'utilisateur qui a créé l'entrée
#             protocole.save()
#             messages.success(request, "Protocole ajouté avec succès.")
#             return redirect('exposition_detail', exposition.pk)
#         else:
#             messages.error(request, 'Protocole na pas ete créé!')
#
#     else:
#         messages.warning(request, 'Un probleme est survenue dans la requete')
#     return redirect('exposition_detail', exposition.pk)
class RageHumaineNotificationListView(FilterView, LoginRequiredMixin, SingleTableView):
    model = RageHumaineNotification
    table_class = RageHumaineNotificationTable
    template_name = "pages/rage_notification/rage_notification_list.html"
    filterset_class = RageHumaineNotificationFilter

    def get_queryset(self):
        return RageHumaineNotification.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset
        return context


class RageHumaineNotificationDetailView(LoginRequiredMixin, DetailView):
    model = RageHumaineNotification
    template_name = "pages/rage_notification/rage_notification_detail.html"
    context_object_name = "notification"


class RageHumaineNotificationUpdateView(LoginRequiredMixin, UpdateView):
    model = RageHumaineNotification
    form_class = RageHumaineNotificationForm
    template_name = "pages/rage_notification/rage_notification_update.html"
    success_url = reverse_lazy("notification_rage_liste")


class RageHumaineNotificationDeleteView(LoginRequiredMixin, DeleteView):
    model = RageHumaineNotification
    template_name = "pages/rage_notification/rage_notification_confirm_delete.html"
    success_url = reverse_lazy("notification_rage_liste")


class RageNotificationCreateView(LoginRequiredMixin, View):
    login_url = 'login'
    redirect_field_name = 'next'
    template_name = "pages/rage_notification/rage_notification_form.html"

    def get(self, request):
        patient_form = ClientForm()
        rage_notif_form = RageHumaineNotificationForm()
        return render(request, self.template_name, {
            "patient_form": patient_form,
            "rage_notif_form": rage_notif_form
        })

    def post(self, request):
        patient_form = ClientForm(request.POST)
        rage_notif_form = RageHumaineNotificationForm(request.POST)

        if patient_form.is_valid() and rage_notif_form.is_valid():
            # Sauvegarde du patient
            patient = patient_form.save()

            # Sauvegarde de la notification avec lien vers le patient
            notification = rage_notif_form.save(commit=False)
            notification.client = patient
            notification.save()

            messages.success(request, "La notification a été enregistrée avec succès ! ✅")
            return redirect("notification_rage_liste")

        # Si les formulaires ne sont pas valides
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        return render(request, self.template_name, {
            "patient_form": patient_form,
            "rage_notif_form": rage_notif_form
        })


@login_required
def ajouter_symptome(request):
    if request.method == 'POST':
        form = SymptomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Symptôme ajouté avec succès.")
            return redirect('liste_symptomes')
        else:
            messages.error(request, "Erreur lors de l'ajout du symptôme.")
    else:
        form = SymptomForm()

    return render(request, 'symptomes/ajouter_symptome.html', {'form': form})


# @login_required
# def ajouter_echantillon(request, exposition_id):
#     exposition = get_object_or_404(Exposition, pk=exposition_id)
#
#     if request.method == 'POST':
#         form = EchantillonForm(request.POST)
#         if form.is_valid():
#             echantillon = form.save(commit=False)
#             echantillon.patient = exposition.patient  # Associer au patient de l'exposition
#             echantillon.agent_collect = request.user  # Associer à l'agent collecteur
#             echantillon.save()
#             messages.success(request, "Échantillon ajouté avec succès.")
#             return redirect('exposition_detail', exposition.pk)
#         else:
#             messages.error(request, "Erreur lors de l'ajout de l'échantillon.")
#     else:
#         form = EchantillonForm()
#
#     return render(request, 'echantillons/ajouter_echantillon.html', {'form': form, 'exposition': exposition})
@login_required
# def lots_par_vaccin(request):
#     vaccin_id = request.GET.get('vaccin_id')
#
#     if not vaccin_id:
#         return JsonResponse({'error': 'ID de vaccin manquant.'}, status=400)
#
#     try:
#         lots = LotVaccin.objects.filter(
#             vaccin_id=vaccin_id,
#             quantite_disponible__gt=0
#         ).order_by('date_expiration').select_related('vaccin')
#
#         data = [
#             {
#                 'id': lot.id,
#                 'numero': lot.numero_lot,
#                 'date_expiration': lot.date_expiration.isoformat() if lot.date_expiration else None,
#                 'stock_restant': lot.quantite_disponible,
#                 'vaccin_nom': lot.vaccin.nom if lot.vaccin else ''
#             }
#             for lot in lots
#         ]
#
#         return JsonResponse(data, safe=False)
#
#     except Exception as e:
#         logger.error(f"Erreur dans lots_par_vaccin: {str(e)}")
#         return JsonResponse({'error': 'Une erreur est survenue.'}, status=500)
def get_lots_by_vaccin(request):
    vaccin_id = request.GET.get('vaccin_id')
    lots = LotVaccin.objects.filter(vaccin_id=vaccin_id, quantite_disponible__gt=0)
    data = [{'id': lot.id, 'label': str(lot)} for lot in lots]
    return JsonResponse({'lots': data})


@login_required
def vacciner(request, rendez_vous_id):
    rendez_vous = get_object_or_404(RendezVousVaccination, id=rendez_vous_id)

    if not request.user.has_perm('vaccination.add_vaccination'):
        return JsonResponse({'error': 'Permission refusée.'}, status=403)

    if request.method == 'POST':
        form = VaccinationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    vaccination = form.save(commit=False)
                    vaccination.patient = rendez_vous.patient
                    vaccination.protocole = rendez_vous.protocole
                    vaccination.date_prevue = rendez_vous.date_rendez_vous
                    vaccination.dose_numero = rendez_vous.ordre_rdv
                    vaccination.nombre_dose = rendez_vous.protocole.nbr_dose_par_rdv or 1
                    vaccination.created_by = request.user
                    vaccination.save()

                    # Mise à jour du stock
                    lot = form.cleaned_data.get('lot')
                    if lot:
                        lot.quantite_disponible -= 1
                        lot.save()

                    rendez_vous.est_effectue = True
                    rendez_vous.save()

                    # Récupération du prochain rendez-vous (si disponible)
                    prochain_rdv = RendezVousVaccination.objects.filter(
                        patient=rendez_vous.patient,
                        protocole=rendez_vous.protocole,
                        est_effectue=False,
                        date_rendez_vous__gt=rendez_vous.date_rendez_vous
                    ).order_by('date_rendez_vous').first()

                    # Construction du message SMS
                    message_sms = (
                        f"Merci {rendez_vous.patient.nom}, votre vaccination du "
                        f"{vaccination.date_prevue.strftime('%d/%m/%Y')} a bien été enregistrée.\n"
                        f"👉 Veuillez rester 15 minutes en observation (MAPI).\n"
                    )

                    if prochain_rdv:
                        message_sms += (
                            f"📅 Votre prochain RDV est prévu pour le "
                            f"{prochain_rdv.date_rendez_vous.strftime('%d/%m/%Y')} "
                            f"(dose {prochain_rdv.ordre_rdv}).\n"
                        )

                    message_sms += (
                        "📣 Signalez tout effet secondaire ici : "
                        f"{request.build_absolute_uri(reverse('cartographie'))}"
                    )

                    # Envoi du SMS
                    try:
                        send_analysis_sms(rendez_vous.patient.contact, message_sms)
                    except Exception as sms_error:
                        logger.warning(f"Échec de l'envoi du SMS au {rendez_vous.patient.contact} : {sms_error}")

                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'redirect_url': reverse('vaccin-rdv-list')
                        })

                    messages.success(request, "Vaccination enregistrée avec succès.")
                    return redirect('vaccin-rdv-list')

            except Exception as e:
                logger.error(f"Erreur lors de la vaccination: {str(e)}")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Erreur lors de la mise à jour de la base de données'
                    }, status=500)

                messages.error(request, "Une erreur est survenue lors de l'enregistrement.")
                return redirect('vaccin-rdv-list')

        else:
            errors = form.errors.as_json()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Formulaire invalide',
                    'errors': errors
                }, status=400)

            messages.error(request, "Erreur lors de la soumission.")
            return redirect('vaccin-rdv-list')

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# @login_required
# def vacciner(request, rendez_vous_id):
#     rendez_vous = get_object_or_404(RendezVousVaccination, id=rendez_vous_id)
#
#     if request.method == 'POST':
#         form = VaccinationForm(request.POST)
#         if form.is_valid():
#             vaccination = form.save(commit=False)
#             vaccination.patient = rendez_vous.patient
#             vaccination.protocole = rendez_vous.protocole
#             vaccination.date_prevue = rendez_vous.date_rendez_vous
#             vaccination.dose_numero = rendez_vous.ordre_rdv  # Fix ici
#             vaccination.nombre_dose = rendez_vous.protocole.nbr_dose_par_rdv or 1
#             vaccination.created_by = request.user  # Enregistre l'utilisateur qui a validé la vaccination
#             vaccination.save()
#
#             # Mise à jour du champ `est_effectue`
#             rendez_vous.est_effectue = True
#             rendez_vous.save()
#
#             messages.success(request, "Vaccination enregistrée avec succès.")
#             return redirect('vaccin-rdv-list')
#         else:
#             messages.error(request, "Erreur lors de l'enregistrement de la vaccination.")
#     else:
#         form = VaccinationForm()
#
#     return redirect('vaccin-rdv-list')


@login_required
def effectuer_paiement(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)

    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.facture = facture
            paiement.created_by = request.user

            # Vérifier que le paiement ne dépasse pas le reste à payer
            if paiement.montant > facture.reste_a_payer:
                messages.error(request, "Le montant du paiement ne peut pas dépasser le montant restant à payer.")
                return redirect('effectuer_paiement', facture_id=facture.id)

            with transaction.atomic():
                paiement.save()  # Sauvegarde du paiement

                # Mise à jour de la facture
                facture.montant_paye += paiement.montant
                facture.reste_a_payer = facture.montant_total - facture.montant_paye

                # Mise à jour du statut
                if facture.reste_a_payer <= 0:
                    facture.statut_paiement = "payee"
                elif facture.montant_paye > 0:
                    facture.statut_paiement = "partiellement_payee"
                else:
                    facture.statut_paiement = "non_payee"

                facture.save()

            messages.success(request, "Paiement effectué avec succès.")
            return redirect('liste_factures', )
    else:
        form = PaiementForm()

    return redirect('liste_factures', )


def confirm_rdv_to_patient(rdv):
    if not rdv.patient.contact:
        return False

    phone_number = str(rdv.patient.contact).replace("+", "")
    message = (
        f"📅 Rendez-vous vaccination\n"
        f"Patient: {rdv.patient.nom}\n"
        f"Date: {rdv.date_rendez_vous.strftime('%d/%m/%Y à %H:%M')}\n"
        f"Dose: {rdv.dose_numero}/{rdv.protocole.nombre_doses}\n"
        f"Lieu: {rdv.patient.centre_ar.nom}"
    )

    return WhatsAppService.send_custom_message(phone_number, message)


class RendezVousListView(SingleTableMixin, LoginRequiredMixin, FilterView):
    model = RendezVousVaccination
    table_class = RendezVousTable
    template_name = "pages/rendez_vous/rendez_vous_list.html"
    filterset_class = RendezVousFilter
    paginate_by = 10  # Nombre d'éléments par page

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "protocole", "preexposition", "postexposition")

    def get_context_data(self, **kwargs):
        """ Ajoute le filtre dans le contexte pour qu'il soit bien rendu dans le template """
        context = super().get_context_data(**kwargs)
        context["filter"] = self.get_filterset(
            self.filterset_class)  # Utiliser get_filterset() au lieu de self.filterset
        context["vaccins"] = Vaccins.objects.all()
        context["igform"] = InjectionImmunoglobulineForm()

        return context


class FactureListView(SingleTableMixin, LoginRequiredMixin, FilterView):
    model = Facture
    table_class = FactureTable
    template_name = "pages/factures/facture_list.html"
    # filterset_class = FactureFilter
    paginate_by = 10  # Pagination : 10 factures par page


class RendezVousDetailView(LoginRequiredMixin, DetailView):
    model = RendezVousVaccination
    template_name = 'pages/rendez_vous/rendez_vous_detail.html'
    context_object_name = 'details_rdv'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object.patient  # Récupérer le patient lié à l'exposition
        # Récupérer les protocoles de vaccination du patient
        # context["protocoles_vaccination"] = ProtocoleVaccination.objects.filter(patient=patient)
        # context["patientdossier"] = patient  # Passer les infos du patient
        context["vaccinform"] = VaccinationForm()  # Passer les infos du patient
        return context


# class ExpositionDetailView(DetailView):
#     model = Exposition
#     template_name = 'pages/expositions/exposition_detail.html'
#     context_object_name = 'exposition'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         patient = self.object.patient  # Récupérer le patient lié à l'exposition
#         # Récupérer les protocoles de vaccination du patient
#         context["protocoles_vaccination"] = ProtocoleVaccination.objects.filter(patient=patient)
#         context["rdvvaccin"] = RendezVousVaccination.objects.filter(patient=patient)
#         context["patientdossier"] = patient  # Passer les infos du patient
#         context["protocolefrom"] = ProtocoleVaccinationForm()  # Passer les infos du patient
#         return context
#
#
# class ExpositionCreateView(CreateView):
#     model = Exposition
#     form_class = ExpositionForm
#     template_name = 'pages/expositions/exposition_form.html'
#     success_url = reverse_lazy('exposition_list')
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)
#
#
# class ExpositionUpdateView(UpdateView):
#     model = Exposition
#     template_name = 'pages/expositions/exposition_form.html'
#     fields = '__all__'
#     success_url = reverse_lazy('exposition_list')
#
#
# class ExpositionDeleteView(DeleteView):
#     model = Exposition
#     template_name = 'pages/expositions/exposition_confirm_delete.html'
#     success_url = reverse_lazy('exposition_list')


# ----------------------------------- Animal ------------------------------------------------------

class AnimalListView(LoginRequiredMixin, ListView):
    model = Animal
    template_name = 'animaux/animal_list.html'
    context_object_name = 'animaux'
    ordering = ['-created_at']


class AnimalDetailView(LoginRequiredMixin, DetailView):
    model = Animal
    template_name = 'animaux/animal_detail.html'
    context_object_name = 'animal'


class AnimalUpdateView(LoginRequiredMixin, UpdateView):
    model = Animal
    template_name = 'animaux/animal_form.html'
    fields = '__all__'
    success_url = reverse_lazy('animal_list')


class AnimalDeleteView(LoginRequiredMixin, DeleteView):
    model = Animal
    template_name = 'animaux/animal_confirm_delete.html'
    success_url = reverse_lazy('animal_list')


# -------------------- Protocole de Vaccinantion ------------------------------------#

class ProtocoleVaccinationListView(LoginRequiredMixin, ListView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_list.html'
    context_object_name = 'protocoles'


class ProtocoleVaccinationDetailView(LoginRequiredMixin, DetailView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_detail.html'
    context_object_name = 'protocole'


class ProtocoleVaccinationUpdateView(LoginRequiredMixin, UpdateView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_form.html'
    fields = '__all__'
    success_url = reverse_lazy('protocole_list')


class ProtocoleVaccinationDeleteView(LoginRequiredMixin, DeleteView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_confirm_delete.html'
    success_url = reverse_lazy('protocole_list')


# ----------------------  Vaccinantion ------------------------------------
@login_required
def attestation_vaccination(request, vaccination_id):
    vaccination = get_object_or_404(Vaccination, id=vaccination_id)

    # Création du buffer et du canvas en format A6 (105 x 148 mm)
    buffer = BytesIO()
    width, height = A6
    p = canvas.Canvas(buffer, pagesize=A6)

    # Chemins des logos (ajuster selon votre structure de fichiers)
    logo_ministere = os.path.join(settings.STATIC_ROOT, 'assets/media/certificat.jpg')
    logo_hopital = os.path.join(settings.STATIC_ROOT, 'assets/logo_hopital.png')

    # Ajout du filigrane
    p.setFillColor(lightgrey)
    p.setFont("Helvetica-Bold", 40)
    p.rotate(45)
    p.drawString(50, -100, "CERTIFICAT OFFICIEL")
    p.rotate(-45)
    p.setFillColorRGB(0, 0, 0)  # Retour à la couleur noire

    # En-tête

    # En-tête avec logos
    logo_height = 15  # Hauteur en mm
    logo_width = 30  # Largeur en mm (sera ajustée pour conserver les proportions)

    # Logo ministère (gauche)
    if os.path.exists(logo_ministere):
        img = ImageReader(logo_ministere)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        p.drawImage(img, 5, height - logo_height - 15,
                    width=logo_width, height=logo_width * aspect,
                    preserveAspectRatio=True, mask='auto')

    # Logo hôpital (droite)
    if os.path.exists(logo_hopital):
        img = ImageReader(logo_hopital)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        p.drawImage(img, width - logo_width - 10, height - logo_height - 15,
                    width=logo_width, height=logo_width * aspect,
                    preserveAspectRatio=True, mask='auto')

    p.setFont("Helvetica", 5)
    p.drawCentredString(width / 4, height - 20, "Ministère de la Santé de l'hygiène publique")
    p.drawCentredString(width / 4, height - 25, " et de la couverture Maladie Universelle")

    p.drawCentredString(width / 1.2, height - 20, "République de Côte d'Ivoire")
    p.drawCentredString(width / 1.2, height - 25, "Union-Discipline-Travail")

    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2, height - 40, "ATTESTATION DE VACCINATION")

    # Informations patient
    y_position = height - 50
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10, y_position, "INFORMATIONS DU PATIENT:")
    p.setFont("Helvetica", 9)
    y_position -= 15
    p.drawString(15, y_position, f"Nom: {vaccination.patient.nom} {vaccination.patient.prenoms}")
    y_position -= 12
    p.drawString(15, y_position, f"Date de naissance: {vaccination.patient.date_naissance.strftime('%d/%m/%Y')}")

    # Détails vaccination
    y_position -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10, y_position, "DÉTAILS DE LA VACCINATION:")
    p.setFont("Helvetica", 9)
    y_position -= 15
    p.drawString(15, y_position, f"Date: {vaccination.date_effective.strftime('%d/%m/%Y %H:%M')}")
    y_position -= 12
    p.drawString(15, y_position, f"Vaccin: {vaccination.vaccin.nom}")
    y_position -= 12
    p.drawString(15, y_position, f"Lot: {vaccination.lot.numero_lot if vaccination.lot else 'N/A'}")
    y_position -= 12
    p.drawString(15, y_position, f"Dose: {vaccination.dose_numero}/{vaccination.nombre_dose}")
    y_position -= 12
    p.drawString(15, y_position, f"Volume: {vaccination.dose_ml} ml")
    y_position -= 12
    p.drawString(15, y_position, f"Voie: {vaccination.get_voie_injection_display()}")

    # Génération du QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=2,
        border=2,
    )
    qr_data = f"""
Patient: {vaccination.patient.nom} {vaccination.patient.prenoms}
Date: {vaccination.date_effective.strftime('%d/%m/%Y')}
Vaccin: {vaccination.vaccin.nom}
Lot: {vaccination.lot.numero_lot if vaccination.lot else 'N/A'}
Dose: {vaccination.dose_numero}/{vaccination.nombre_dose}
ID: {vaccination.id}
    """
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Sauvegarde du QR code dans un buffer temporaire
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Ajout du QR code au PDF
    qr_size = 30  # Taille en points (environ 10mm)
    p.drawImage(ImageReader(qr_buffer), width - qr_size - 10, 20,
                width=qr_size, height=qr_size)

    # Pied de page
    p.setFont("Helvetica", 8)
    p.drawString(10, 30, f"Certificat généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    p.drawString(10, 20, "Signature du responsable: ________________")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attestation_vaccination_{vaccination.id}.pdf"'
    return response


class GenerateVaccinationCertificatePDF(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        vaccination_id = kwargs.get('pk')
        try:
            vaccination = Vaccination.objects.get(pk=vaccination_id)
        except Vaccination.DoesNotExist:
            return HttpResponse("Vaccination non trouvée", status=404)

        # Création du contexte pour le template
        context = {
            'vaccination': vaccination,
            'date_emission': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'qr_code_data': self.generate_qr_code_data(vaccination),
        }

        # Chargement du template HTML
        template = get_template('pages/vaccinations/certificate_pdf.html')
        html = template.render(context)

        # Création du PDF
        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'] = f'attachment; filename="certificat_vaccination_{vaccination.patient.nom}_{vaccination.id}.pdf"'

        # Génération du PDF
        pisa_status = pisa.CreatePDF(
            html, dest=response, encoding='utf-8')

        if pisa_status.err:
            return HttpResponse('Erreur lors de la génération du PDF', status=500)
        return response

    def generate_qr_code_data(self, vaccination):
        """Génère les données pour le QR code"""
        data = {
            "patient": {
                "nom": vaccination.patient.nom,
                "prenom": vaccination.patient.prenoms,
                "date_naissance": str(vaccination.patient.date_naissance),
            },
            "vaccination": {
                "date": str(vaccination.date_effective),
                "vaccin": vaccination.vaccin.nom if vaccination.vaccin else "",
                "lot": vaccination.lot.numero_lot if vaccination.lot else "",
                "dose": f"{vaccination.dose_numero}/{vaccination.nombre_dose}",
                "protocole": vaccination.protocole.nom,
            },
            "centre": {
                "nom": vaccination.lieu,
            }
        }
        return data

    def generate_qr_code(self, data):
        """Génère un QR code à partir des données"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer


class VaccinationListView(LoginRequiredMixin, ListView):
    model = Vaccination
    template_name = 'pages/vaccinations/vaccination_list.html'
    context_object_name = 'vaccinations'
    ordering = ['-created_at']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapi_form"] = MAPIForm()
        return context


class VaccinationDetailView(LoginRequiredMixin, DetailView):
    model = Vaccination
    template_name = 'pages/vaccinations/vaccination_detail.html'
    context_object_name = 'vaccination'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapi_form"] = MAPIForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MAPIForm(request.POST)

        if form.is_valid():
            mapi = form.save(commit=False)
            mapi.vaccination = self.object
            mapi.patient = self.object.patient  # si `Vaccination` a un lien vers `Patient`
            mapi.created_by = request.user
            mapi.save()
            messages.success(request, "✅ Symptôme MAPI enregistré avec succès.")
            return redirect("vaccination_detail", pk=self.object.pk)

        context = self.get_context_data()
        context["mapi_form"] = form
        return self.render_to_response(context)


class VaccinationUpdateView(LoginRequiredMixin, UpdateView):
    model = Vaccination
    template_name = 'vaccinations/vaccination_form.html'
    fields = '__all__'
    success_url = reverse_lazy('vaccination_list')


class VaccinationDeleteView(LoginRequiredMixin, DeleteView):
    model = Vaccination
    template_name = 'vaccinations/vaccination_confirm_delete.html'
    success_url = reverse_lazy('vaccination_list')


class InjectionImmunoglobulineCreateView(LoginRequiredMixin, CreateView):
    model = InjectionImmunoglobuline
    form_class = InjectionImmunoglobulineForm
    template_name = "pages/immunoglobuline/injection_form.html"
    success_url = reverse_lazy('injection_list')  # À adapter à ton URL

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "✅ Injection enregistrée avec succès.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Erreur lors de l’enregistrement. Veuillez corriger les champs.")
        return super().form_invalid(form)


# --------------------------------------------------------Parametres---------------------------------------------------#


# ----------Vaccins------------------#

class VaccinListView(LoginRequiredMixin, ListView):
    model = Vaccins
    template_name = 'parametres/vaccins/vaccin_list.html'
    context_object_name = 'vaccins'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrage par nom si un paramètre de recherche est présent
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(nom__icontains=search_query)
        return queryset


class VaccinCreateView(LoginRequiredMixin, CreateView):
    model = Vaccins
    form_class = VaccinForm
    template_name = 'parametres/vaccins/vaccin_form.html'
    success_url = reverse_lazy('vaccin_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class VaccinUpdateView(LoginRequiredMixin, UpdateView):
    model = Vaccins
    form_class = VaccinForm
    template_name = 'parametres/vaccins/vaccin_form.html'
    success_url = reverse_lazy('vaccin_list')


class VaccinDetailView(LoginRequiredMixin, DetailView):
    model = Vaccins
    template_name = 'parametres/vaccins/vaccin_detail.html'
    context_object_name = 'vaccin'


class LotVaccinListView(LoginRequiredMixin, ListView):
    model = LotVaccin
    template_name = 'parametres/vaccins/lot_vaccin_list.html'
    context_object_name = 'lots'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrage par centre de l'utilisateur connecté
        if not self.request.user.is_superuser:
            queryset = queryset.filter(centre=self.request.user.centre)

        # Filtrage par vaccin si spécifié
        vaccin_id = self.request.GET.get('vaccin')
        if vaccin_id:
            queryset = queryset.filter(vaccin_id=vaccin_id)

        # Filtrage par date d'expiration
        expiration = self.request.GET.get('expiration')
        if expiration == 'soon':
            from django.utils import timezone
            from datetime import timedelta
            soon_date = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(date_expiration__lte=soon_date)

        return queryset.order_by('date_expiration')


class LotVaccinCreateView(LoginRequiredMixin, CreateView):
    model = LotVaccin
    form_class = LotVaccinForm
    template_name = 'parametres/vaccins/lot_vaccin_form.html'
    success_url = reverse_lazy('lot_vaccin_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.centre = self.request.user.centre
        form.instance.quantite_disponible = form.instance.quantite_initiale
        return super().form_valid(form)


class LotVaccinUpdateView(LoginRequiredMixin, UpdateView):
    model = LotVaccin
    form_class = LotVaccinForm
    template_name = 'parametres/vaccins/lot_vaccin_form.html'
    success_url = reverse_lazy('lot_vaccin_list')


class LotVaccinDetailView(LoginRequiredMixin, DetailView):
    model = LotVaccin
    template_name = 'parametres/vaccins/lot_vaccin_detail.html'
    context_object_name = 'lot'


# --------------------Employee Mnagement--------------------------------

class EmployeeUserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EmployeeUser
    template_name = 'parametres/users/employeeuser_list.html'
    context_object_name = 'users'
    permission_required = 'rage.view_employeeuser'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrage par rôle si spécifié
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(roleemployee=role)

        # Filtrage par centre pour les non-superusers
        if not self.request.user.is_superuser and self.request.user.centre:
            queryset = queryset.filter(centre=self.request.user.centre)

        return queryset.order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['centres'] = CentreAntirabique.objects.all()
        return context


class EmployeeUserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EmployeeUser
    form_class = EmployeeUserForm
    template_name = 'parametres/users/employeeuser_form.html'
    success_url = reverse_lazy('employeeuser_list')
    permission_required = 'rage.add_employeeuser'

    def form_valid(self, form):
        user = self.request.user

        # Si le créateur n'est PAS superuser et a un centre
        if not user.is_superuser and hasattr(user, 'centre') and user.centre:
            form.instance.centre = user.centre

        return super().form_valid(form)


class EmployeeUserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EmployeeUser
    form_class = EmployeeUserUpdateForm
    template_name = 'parametres/users/employeeuser_form.html'
    success_url = reverse_lazy('employeeuser_list')
    permission_required = 'rage.change_employeeuser'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Limiter les choix de centre pour les non-superusers
        if not self.request.user.is_superuser:
            kwargs['centre_queryset'] = CentreAntirabique.objects.filter(pk=self.request.user.centre.pk)
        return kwargs


class EmployeeUserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = EmployeeUser
    template_name = 'parametres/users/employeeuser_detail.html'
    context_object_name = 'user'
    permission_required = 'rage.view_employeeuser'


class EmployeeUserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EmployeeUser
    template_name = 'parametres/users/employeeuser_confirm_delete.html'
    success_url = reverse_lazy('employeeuser_list')
    permission_required = 'rage.delete_employeeuser'

    def dispatch(self, request, *args, **kwargs):
        # Empêcher la suppression de soi-même
        if self.get_object() == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('employeeuser_list')
        return super().dispatch(request, *args, **kwargs)


class CentreAntirabiqueListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CentreAntirabique
    template_name = 'parametres/centres/centreantirabique_list.html'
    context_object_name = 'centres'
    permission_required = 'rage.view_centreantirabique'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrage par district si spécifié
        district = self.request.GET.get('district')
        if district:
            queryset = queryset.filter(district_id=district)
        return queryset.order_by('nom')


class CentreAntirabiqueCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CentreAntirabique
    form_class = CentreAntirabiqueForm
    template_name = 'parametres/centres/centreantirabique_form.html'
    success_url = reverse_lazy('centreantirabique_list')
    permission_required = 'rage.add_centreantirabique'


class CentreAntirabiqueUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CentreAntirabique
    form_class = CentreAntirabiqueForm
    template_name = 'parametres/centres/centreantirabique_form.html'
    success_url = reverse_lazy('centreantirabique_list')
    permission_required = 'rage.change_centreantirabique'


class CentreAntirabiqueDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = CentreAntirabique
    template_name = 'parametres/centres/centreantirabique_detail.html'
    context_object_name = 'centre'
    permission_required = 'rage.view_centreantirabique'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = self.object.employeeuser_set.all()
        return context


class CentreAntirabiqueDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CentreAntirabique
    template_name = 'parametres/centres/centreantirabique_confirm_delete.html'
    success_url = reverse_lazy('centreantirabique_list')
    permission_required = 'rage.delete_centreantirabique'

    def delete(self, request, *args, **kwargs):
        centre = self.get_object()
        if centre.employeeuser_set.exists():
            messages.error(request, "Impossible de supprimer ce centre car il a des utilisateurs associés.")
            return redirect('centreantirabique_list')
        return super().delete(request, *args, **kwargs)
