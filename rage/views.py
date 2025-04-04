from datetime import timedelta, datetime
from io import BytesIO
from venv import logger

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Count
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, DeleteView, CreateView
from django_filters.views import FilterView
from django_tables2 import tables, SingleTableView, SingleTableMixin
from import_export.admin import ExportMixin
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa

from rage.models import HealthRegion, PolesRegionaux, Patient, ProtocoleVaccination, Vaccination, Animal, \
    RendezVousVaccination, Facture, Preexposition, PostExposition, Commune, RageHumaineNotification, CentreAntirabique, \
    DistrictSanitaire, LotVaccin
from rage.tables import RendezVousTable, FactureTable, PreExpositionTable, PostExpositionTable, \
    RageHumaineNotificationTable
from rage_INHP.decorators import role_required
from rage_INHP.filters import RendezVousFilter, RageHumaineNotificationFilter
# from rage_INHP.filters import ExpositionFilter
from rage_INHP.forms import PatientForm, EchantillonForm, SymptomForm, \
    VaccinationForm, PaiementForm, ClientForm, PreExpositionForm, PostExpositionForm, ClientPreExpositionForm, \
    ClientPostExpositionForm, PatientRageNotificationForm, RageHumaineNotificationForm, PreExpositionUpdateForm, \
    MAPIForm
from rage_INHP.services import synchroniser_avec_mpi


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


def patients_geojson(request):
    patients = Patient.objects.filter(residence_commune__isnull=False, residence_commune__geom__isnull=False)
    data = {
        "type": "FeatureCollection",
        "features": []
    }

    for patient in patients:
        if patient.residence_commune.geom:  # Vérification que geom n'est pas null
            lon, lat = patient.residence_commune.geom.coords  # Extraire longitude et latitude

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
                    "exposition_commune": patient.residence_commune.name,
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
            "0-5 ans": (0, 5),
            "6-11 ans": (6, 11),
            "12-17 ans": (12, 17),
            "18-25 ans": (18, 25),
            "26-31 ans": (26, 31),
            "32-40 ans": (32, 40),
            "41 ans et plus": (41, 150),
        }
        # Statistiques par tranche d'âge, sexe et type de cas
        age_stats = {}
        for label, (min_age, max_age) in age_ranges.items():
            age_stats[label] = {
                "M": {
                    "postexposition": PostExposition.objects.filter(
                        client__sexe="M",
                        client__date_naissance__lte=today - timedelta(days=min_age * 365),
                        client__date_naissance__gt=today - timedelta(days=max_age * 365),
                    ).count(),
                    "preexposition": Preexposition.objects.filter(
                        client__sexe="M",
                        client__date_naissance__lte=today - timedelta(days=min_age * 365),
                        client__date_naissance__gt=today - timedelta(days=max_age * 365),
                    ).count(),
                    "notification": RageHumaineNotification.objects.filter(
                        client__sexe="M",
                        client__date_naissance__lte=today - timedelta(days=min_age * 365),
                        client__date_naissance__gt=today - timedelta(days=max_age * 365),
                    ).count(),
                },
                "F": {
                    "postexposition": PostExposition.objects.filter(
                        client__sexe="F",
                        client__date_naissance__lte=today - timedelta(days=min_age * 365),
                        client__date_naissance__gt=today - timedelta(days=max_age * 365),
                    ).count(),
                    "preexposition": Preexposition.objects.filter(
                        client__sexe="F",
                        client__date_naissance__lte=today - timedelta(days=min_age * 365),
                        client__date_naissance__gt=today - timedelta(days=max_age * 365),
                    ).count(),
                    "notification": RageHumaineNotification.objects.filter(
                        client__sexe="F",
                        client__date_naissance__lte=today - timedelta(days=min_age * 365),
                        client__date_naissance__gt=today - timedelta(days=max_age * 365),
                    ).count(),
                },
            }

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

        # Statistiques par niveau géographique
        # def get_stats_by_level(model, date_field):
        #     stats = {
        #         'poles': list(
        #             model.objects.values('client__centre_ar__district__region__poles__name')
        #             .annotate(count=Count('id'))
        #             .order_by('client__centre_ar__district__region__poles__name')
        #         ) or [],
        #         'regions': list(
        #             model.objects.values('client__centre_ar__district__region__name')
        #             .annotate(count=Count('id'))
        #             .order_by('client__centre_ar__district__region__name')
        #         ) or [],
        #         'districts': list(
        #             model.objects.values('client__centre_ar__district__nom')
        #             .annotate(count=Count('id'))
        #             .order_by('client__centre_ar__district__nom')
        #         ) or [],
        #         'centres': list(
        #             model.objects.values('client__centre_ar__nom')
        #             .annotate(count=Count('id'))
        #             .order_by('client__centre_ar__nom')
        #         ) or []
        #     }
        #     return stats
        #
        # context['stats_geo'] = {
        #     'preexposition': get_stats_by_level(Preexposition, 'created_at'),
        #     'postexposition': get_stats_by_level(PostExposition, 'date_exposition'),
        #     'notification': get_stats_by_level(RageHumaineNotification, 'date_notification')
        # }
        #
        # # Statistiques détaillées par centre
        # centres = CentreAntirabique.objects.all()
        # centre_stats = []
        # for centre in centres:
        #     district_name = centre.district.nom if centre.district else "N/A"
        #
        #     stats = {
        #
        #         'centre': centre.nom,
        #         'district': centre.district.nom if centre.district else '',
        #         'region': centre.district.region.name if centre.district and centre.district.region else '',
        #         'pole': centre.district.region.poles.name if centre.district and centre.district.region and centre.district.region.poles else '',
        #         'preexposition': Preexposition.objects.filter(client__centre_ar=centre).count(),
        #         'postexposition': PostExposition.objects.filter(client__centre_ar=centre).count(),
        #         'notification': RageHumaineNotification.objects.filter(client__centre_ar=centre).count(),
        #         'total': Preexposition.objects.filter(client__centre_ar=centre).count() +
        #                  PostExposition.objects.filter(client__centre_ar=centre).count() +
        #                  RageHumaineNotification.objects.filter(client__centre_ar=centre).count()
        #     }
        #     centre_stats.append(stats)
        #
        #
        # context['centre_stats'] = sorted(centre_stats, key=lambda x: x['total'], reverse=True)

        # context["stats_exposition"] = stats_exposition
        # debut stat par centre
        centres = CentreAntirabique.objects.annotate(
            total_preexposition=Count('patient__preexposition', distinct=True),
            total_postexposition=Count('patient__postexposition', distinct=True),
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
            total_postexposition=Count('centres__patient__postexposition', distinct=True),
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
            total_postexposition=Count('districts__centres__patient__postexposition', distinct=True),
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
            total_postexposition=Count('regions__districts__centres__patient__postexposition', distinct=True),
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


class DistrictDashborad(TemplateView):
    template_name = "pages/index.html"

    @method_decorator(role_required('DistrictSanitaire'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class RegionDashborad(TemplateView):
    template_name = "pages/index.html"

    @method_decorator(role_required('Regional'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class NationalDashborad(TemplateView):
    template_name = "pages/index.html"

    @method_decorator(role_required('National'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


#------------------------------ Les Vues des ressources-------------------------------------------------------


#------------------------------ Donnees des patients ----------------------------------------------------------

class PatientListView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/patients/patient_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer les paramètres de recherche
        search = self.request.GET.get('search', '')
        genre = self.request.GET.get('genre', '')
        nationalite = self.request.GET.get('nationalite', '')
        status = self.request.GET.get('status', '')

        # Filtrer les patients
        queryset = Patient.objects.all()

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
    form_class = PatientForm
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


class PatientDeleteView(DeleteView):
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


#------------------------------ Fin Donnees des patients ----------------------------------------------------------

class DeclarationTemplate(TemplateView):
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


# class PreExpositionCreateView(CreateView):
#     model = Preexposition
#     form_class = PreExpositionForm
#     template_name = "pages/expositions/preexposition_form.html"
#     success_url = reverse_lazy("success_page")  # Remplace par ton URL de succès
#
#     def form_valid(self, form):
#         # Vérifie si un patient est sélectionné
#         client = form.cleaned_data.get("client")
#         if not client:
#             messages.error(self.request, "Veuillez sélectionner un patient avant d'enregistrer.")
#             return self.form_invalid(form)
#
#         messages.success(self.request, "Le dossier de vaccination a été enregistré avec succès ! ✅")
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         messages.error(self.request, "Veuillez corriger les erreurs du formulaire.")
#         return super().form_invalid(form)
# class PreExpositionCreateView(View):
#     template_name = "pages/expositions/preexposition_form.html"
#
#     def get(self, request):
#         client_form = ClientForm()
#         preexposition_form = PreExpositionForm()
#         return render(request, self.template_name, {
#             'client_form': client_form,
#             'preexposition_form': preexposition_form,
#         })
#
#     def post(self, request):
#         client_form = ClientForm(request.POST)
#         preexposition_form = PreExpositionForm(request.POST)
#
#         if client_form.is_valid() and preexposition_form.is_valid():
#             patient = client_form.save()  # Enregistre le patient
#             preexposition = preexposition_form.save(commit=False)  # Ne sauvegarde pas encore
#             preexposition.client = patient  # Associe au patient
#             preexposition.save()  # Enregistre l'entrée PreExposition
#
#             messages.success(request, "Le dossier de vaccination et le patient ont été enregistrés avec succès ! ✅")
#             return redirect(reverse_lazy("preexposition_list"))
#
#         messages.error(request, "Veuillez corriger les erreurs du formulaire.")
#         return render(request, self.template_name, {
#             'client_form': client_form,
#             'preexposition_form': preexposition_form,
#         })

class PreExpositionCreateView(View):
    template_name = "pages/expositions/preexposition_form.html"

    def get(self, request):
        form = ClientPreExpositionForm()
        return render(request, self.template_name, {"form": form})

    # def post(self, request):
    #     form = ClientPreExpositionForm(request.POST)
    #
    #     if form.is_valid():
    #         with transaction.atomic():
    #             # Sauvegarde du patient
    #             patient = form.save(commit=False)
    #             patient.created_by = request.user
    #             if hasattr(request.user, 'centre'):
    #                 patient.centre_ar = request.user.centre
    #             patient.save()
    #
    #             # Sauvegarde des données de pré-exposition
    #             preexposition = Preexposition.objects.create(
    #                 client=patient,
    #                 voyage=form.cleaned_data['voyage'],
    #                 mise_a_jour=form.cleaned_data['mise_a_jour'],
    #                 protection_rage=form.cleaned_data['protection_rage'],
    #                 chien_voisin=form.cleaned_data['chien_voisin'],
    #                 chiens_errants=form.cleaned_data['chiens_errants'],
    #                 autre=form.cleaned_data['autre'],
    #                 autre_motif=form.cleaned_data['autre_motif'],
    #                 tele=form.cleaned_data['tele'],
    #                 radio=form.cleaned_data['radio'],
    #                 sensibilisation=form.cleaned_data['sensibilisation'],
    #                 proche=form.cleaned_data['proche'],
    #                 presse=form.cleaned_data['presse'],
    #                 passage_car=form.cleaned_data['passage_car'],
    #                 diff_canal=form.cleaned_data['diff_canal'],
    #                 canal_infos=form.cleaned_data['canal_infos'],
    #                 aime_animaux=form.cleaned_data['aime_animaux'],
    #                 type_animal_aime=form.cleaned_data['type_animal_aime'],
    #                 connait_protocole_var=form.cleaned_data['connait_protocole_var'],
    #                 dernier_var_animal_type=form.cleaned_data['dernier_var_animal_type'],
    #                 dernier_var_animal_date=form.cleaned_data['dernier_var_animal_date'],
    #                 mesures_elimination_rage=form.cleaned_data['mesures_elimination_rage'],
    #                 appreciation_cout_var=form.cleaned_data['appreciation_cout_var'],
    #                 created_by=request.user,
    #             )
    #
    #             # Récupérer le protocole choisi ou prendre "IPC" par défaut
    #             protocole = form.cleaned_data.get('protocole_vaccination')
    #             if not protocole:
    #                 protocole = ProtocoleVaccination.objects.filter(nom="Pré-Exposition-ID").first()
    #
    #             if protocole:
    #                 # Définition des intervalles entre les visites
    #                 intervals = [
    #                     protocole.intervale_visite1_2,
    #                     protocole.intervale_visite2_3,
    #                     protocole.intervale_visite3_4,
    #                     protocole.intervale_visite4_5
    #                 ]
    #
    #                 # Transformation des intervalles en entiers
    #                 try:
    #                     intervals = [int(i.replace("Jours", "").strip()) if i else None for i in intervals]
    #                 except ValueError:
    #                     intervals = [None] * 4  # Gérer les erreurs de conversion
    #
    #                 # Définition des paramètres du protocole
    #                 date_rdv = now().date()  # Premier rendez-vous = aujourd'hui
    #                 doses_restantes = protocole.nombre_doses
    #                 visites_restantes = protocole.nombre_visite
    #                 dose_numero = 1
    #                 duree_max = timedelta(days=protocole.duree) if protocole.duree else None  # Durée max du protocole
    #                 date_fin_max = date_rdv + duree_max if duree_max else None  # Date limite des rendez-vous
    #
    #                 # Création des rendez-vous en respectant les règles
    #                 for i in range(visites_restantes):
    #                     if doses_restantes <= 0:
    #                         break  # Stop si toutes les doses ont été administrées
    #
    #                     # Vérifier si la date du rendez-vous dépasse la durée maximale
    #                     if date_fin_max and date_rdv > date_fin_max:
    #                         break  # Ne pas créer de rendez-vous après la durée max
    #
    #                     # Calcul des doses pour ce rendez-vous
    #                     doses_pour_ce_rdv = min(doses_restantes, protocole.nbr_dose_par_rdv or 1)
    #
    #                     # Création du rendez-vous
    #                     RendezVousVaccination.objects.create(
    #                         patient=patient,
    #                         preexposition=preexposition,
    #                         protocole=protocole,
    #                         date_rendez_vous=date_rdv,
    #                         dose_numero=dose_numero,
    #                         est_effectue=False,
    #                         created_by=request.user
    #                     )
    #
    #                     # Mise à jour des doses et de la prochaine date
    #                     doses_restantes -= doses_pour_ce_rdv
    #                     dose_numero += doses_pour_ce_rdv
    #
    #                     if i < len(intervals) and intervals[i]:
    #                         date_rdv += timedelta(days=intervals[i])
    #
    #             messages.success(request,
    #                              "Le dossier de vaccination, le patient et les rendez-vous ont été enregistrés avec succès ! ✅")
    #             return redirect(reverse("preexposition_list"))
    #
    #     # Gestion des erreurs du formulaire
    #     error_messages = [
    #         f"<strong>{form.fields[field].label if field in form.fields else field}</strong>: {', '.join(errors)}"
    #         for field, errors in form.errors.items()]
    #     error_text = "Veuillez corriger les erreurs du formulaire :<br>" + "<br>".join(error_messages)
    #
    #     messages.error(request, error_text)
    #     return render(request, self.template_name, {"form": form})
    def post(self, request):
        form = ClientPreExpositionForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                # Sauvegarde du patient
                patient = form.save(commit=False)
                patient.created_by = request.user
                if hasattr(request.user, 'centre'):
                    patient.centre_ar = request.user.centre
                patient.save()

                # Sauvegarde des données de pré-exposition
                preexposition = Preexposition.objects.create(
                    client=patient,
                    voyage=form.cleaned_data['voyage'],
                    mise_a_jour=form.cleaned_data['mise_a_jour'],
                    protection_rage=form.cleaned_data['protection_rage'],
                    chien_voisin=form.cleaned_data['chien_voisin'],
                    chiens_errants=form.cleaned_data['chiens_errants'],
                    autre=form.cleaned_data['autre'],
                    autre_motif=form.cleaned_data['autre_motif'],
                    tele=form.cleaned_data['tele'],
                    radio=form.cleaned_data['radio'],
                    sensibilisation=form.cleaned_data['sensibilisation'],
                    proche=form.cleaned_data['proche'],
                    presse=form.cleaned_data['presse'],
                    passage_car=form.cleaned_data['passage_car'],
                    diff_canal=form.cleaned_data['diff_canal'],
                    canal_infos=form.cleaned_data['canal_infos'],
                    aime_animaux=form.cleaned_data['aime_animaux'],
                    type_animal_aime=form.cleaned_data['type_animal_aime'],
                    connait_protocole_var=form.cleaned_data['connait_protocole_var'],
                    dernier_var_animal_type=form.cleaned_data['dernier_var_animal_type'],
                    dernier_var_animal_date=form.cleaned_data['dernier_var_animal_date'],
                    mesures_elimination_rage=form.cleaned_data['mesures_elimination_rage'],
                    appreciation_cout_var=form.cleaned_data['appreciation_cout_var'],
                    created_by=request.user,
                )

                protocole = form.cleaned_data.get('protocole_vaccination')
                if not protocole:
                    protocole = ProtocoleVaccination.objects.filter(nom="Pré-Exposition-ID").first()

                if protocole and protocole.nombre_visite and protocole.nombre_doses and protocole.nbr_dose_par_rdv:
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

                messages.success(request,
                                 "Le dossier de vaccination, le patient et les rendez-vous ont été enregistrés avec succès ! ✅")
                return redirect(reverse("preexposition_list"))

        error_messages = [
            f"<strong>{form.fields[field].label if field in form.fields else field}</strong>: {', '.join(errors)}"
            for field, errors in form.errors.items()]
        error_text = "Veuillez corriger les erreurs du formulaire :<br>" + "<br>".join(error_messages)

        messages.error(request, error_text)
        return render(request, self.template_name, {"form": form})


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


class PreExpositionDeleteView(DeleteView):
    model = Preexposition
    template_name = "pages/expositions/preexposition_confirm_delete.html"
    success_url = reverse_lazy("preexposition_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Le dossier de vaccination a été supprimé avec succès ! 🗑️")
        return super().delete(request, *args, **kwargs)


# ------- Fin Pre Expo

# --------- Post-Exposition
import django_tables2 as tables


# ✅ Vue Liste des PostExposition avec django-tables2
class PostExpositionListView(SingleTableView):
    model = PostExposition
    table_class = PostExpositionTable
    template_name = "pages/postexposition/postexposition_list.html"


def get_communes(request):
    query = request.GET.get('query', '')
    communes = Commune.objects.filter(name__icontains=query).values('id', 'name')
    return JsonResponse(list(communes), safe=False)


class PostExpositionCreateView(View):
    template_name = "pages/expositions/postexposition_form.html"

    def get(self, request):
        form = ClientPostExpositionForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ClientPostExpositionForm(request.POST)
        with transaction.atomic():
            if not request.user.is_authenticated:
                messages.error(request, "Vous devez être connecté pour effectuer cette action.")
                return redirect("account-login")  # Remplace "login" par ton URL de connexion

        if form.is_valid():
            with transaction.atomic():
                # ✅ Vérifier si le patient existe déjà
                patient = Patient.objects.filter(
                    nom=form.cleaned_data['nom'],
                    prenoms=form.cleaned_data['prenoms'],
                    date_naissance=form.cleaned_data['date_naissance'],
                    # sexe=form.cleaned_data['sexe'],
                    # contact=form.cleaned_data['contact']
                ).first()

                if not patient:
                    # ✅ Création du patient seulement s'il n'existe pas
                    patient = form.save()

                # ✅ Création de la post-exposition
                postexposition = PostExposition.objects.create(
                    client=patient,
                    date_exposition=form.cleaned_data['date_exposition'],
                    lieu_exposition=form.cleaned_data['lieu_exposition'],
                    exposition_quartier=form.cleaned_data['exposition_quartier'],
                    attaque_provoquee=form.cleaned_data['attaque_provoquee'],
                    agression=form.cleaned_data['agression'],
                    attaque_collective=form.cleaned_data['attaque_collective'],
                    professionnel=form.cleaned_data['professionnel'],
                    type_professionnel=form.cleaned_data['type_professionnel'],
                    morsure=form.cleaned_data['morsure'],
                    griffure=form.cleaned_data['griffure'],
                    lechage_saine=form.cleaned_data['lechage_saine'],
                    contactanimalpositif=form.cleaned_data['contactanimalpositif'],
                    contactpatientpositif=form.cleaned_data['contactpatientpositif'],
                    autre=form.cleaned_data['autre'],
                    autre_nature_exposition=form.cleaned_data['autre_nature_exposition'],
                    created_by=request.user,
                )

                # ✅ Récupération du protocole de vaccination (ou "IPC" par défaut)
                protocole = form.cleaned_data.get('protocole_vaccination')
                if not protocole:
                    protocole = ProtocoleVaccination.objects.filter(nom="IPC").first()

                if protocole:
                    # ✅ Définition des intervalles des visites
                    intervals = [
                        protocole.intervale_visite1_2,
                        protocole.intervale_visite2_3,
                        protocole.intervale_visite3_4,
                        protocole.intervale_visite4_5
                    ]

                    # ✅ Transformation des intervalles en entiers (Gestion des erreurs)
                    try:
                        intervals = [int(i.replace("Jours", "").strip()) if i else None for i in intervals]
                    except ValueError:
                        intervals = [None] * 4  # Gérer les erreurs de conversion

                    # ✅ Définition des paramètres du protocole
                    date_rdv = now().date()  # Premier rendez-vous = aujourd'hui
                    doses_restantes = protocole.nombre_doses
                    visites_restantes = protocole.nombre_visite
                    dose_numero = 1
                    duree_max = timedelta(days=protocole.duree) if protocole.duree else None
                    date_fin_max = date_rdv + duree_max if duree_max else None

                    # ✅ Création des rendez-vous post-exposition
                    for i in range(visites_restantes):
                        if doses_restantes <= 0:
                            break  # Stop si toutes les doses ont été administrées

                        if date_fin_max and date_rdv > date_fin_max:
                            break  # Ne pas créer de rendez-vous après la durée max

                        # ✅ Calcul des doses pour ce rendez-vous
                        doses_pour_ce_rdv = min(doses_restantes, protocole.nbr_dose_par_rdv or 1)

                        # ✅ Création du rendez-vous
                        RendezVousVaccination.objects.create(
                            patient=patient,
                            postexposition=postexposition,
                            protocole=protocole,
                            date_rendez_vous=date_rdv,
                            dose_numero=dose_numero,
                            est_effectue=False,
                            created_by=request.user
                        )

                        # Mise à jour des doses et de la prochaine date
                        doses_restantes -= doses_pour_ce_rdv
                        dose_numero += doses_pour_ce_rdv

                        if i < len(intervals) and intervals[i]:
                            date_rdv += timedelta(days=intervals[i])

                messages.success(request,
                                 "Le dossier de post-exposition, le patient et les rendez-vous ont été enregistrés avec succès ! ✅")
                return redirect(reverse("postexposition_list"))

        # ✅ Gestion des erreurs du formulaire
        error_messages = [
            f"<strong>{form.fields[field].label if field in form.fields else field}</strong>: {', '.join(errors)}"
            for field, errors in form.errors.items()
        ]
        error_text = "Veuillez corriger les erreurs du formulaire :<br>" + "<br>".join(error_messages)

        messages.error(request, error_text)
        return render(request, self.template_name, {"form": form})


# ✅ Vue Détail
class PostExpositionDetailView(DetailView):
    model = PostExposition
    template_name = "pages/postexposition/postexposition_detail.html"


# ✅ Vue Mise à Jour
class PostExpositionUpdateView(UpdateView):
    model = PostExposition
    form_class = PostExpositionForm
    template_name = "pages/postexposition/postexposition_form.html"
    success_url = reverse_lazy("postexposition_list")

    def form_valid(self, form):
        messages.success(self.request, "Le dossier post-exposition a été mis à jour avec succès ! ✅")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs du formulaire.")
        return super().form_invalid(form)


# ✅ Vue Suppression
class PostExpositionDeleteView(DeleteView):
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

#-------------------------------------------- Exposition de la rage ----------------------------

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
class RageHumaineNotificationListView(FilterView, SingleTableView):
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


class RageHumaineNotificationDetailView(DetailView):
    model = RageHumaineNotification
    template_name = "pages/rage_notification/rage_notification_detail.html"
    context_object_name = "notification"


class RageHumaineNotificationUpdateView(UpdateView):
    model = RageHumaineNotification
    form_class = RageHumaineNotificationForm
    template_name = "pages/rage_notification/rage_notification_update.html"
    success_url = reverse_lazy("notification_rage_liste")


class RageHumaineNotificationDeleteView(DeleteView):
    model = RageHumaineNotification
    template_name = "pages/rage_notification/rage_notification_confirm_delete.html"
    success_url = reverse_lazy("notification_rage_liste")


class RageNotificationCreateView(View):
    template_name = "pages/rage_notification/rage_notification_form.html"

    def get(self, request):
        form = PatientRageNotificationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PatientRageNotificationForm(request.POST)
        if form.is_valid():
            patient_data = {field.name: form.cleaned_data[field.name] for field in Patient._meta.fields if
                            field.name in form.cleaned_data}
            patient = Patient.objects.create(**patient_data)

            notification_data = {field.name: form.cleaned_data[field.name] for field in
                                 RageHumaineNotification._meta.fields if field.name in form.cleaned_data}
            notification = RageHumaineNotification.objects.create(client=patient, **notification_data)

            messages.success(request, "La notification a été enregistrée avec succès ! ✅")
            return redirect("notification_rage_liste")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
            return render(request, self.template_name, {"form": form})


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
def lots_par_vaccin(request):
    vaccin_id = request.GET.get('vaccin_id')

    if not vaccin_id:
        return JsonResponse({'error': 'ID de vaccin manquant.'}, status=400)

    try:
        lots = LotVaccin.objects.filter(
            vaccin_id=vaccin_id,
            quantite_disponible__gt=0
        ).order_by('date_expiration').select_related('vaccin')

        data = [
            {
                'id': lot.id,
                'numero': lot.numero_lot,
                'date_expiration': lot.date_expiration.isoformat() if lot.date_expiration else None,
                'stock_restant': lot.quantite_disponible,
                'vaccin_nom': lot.vaccin.nom if lot.vaccin else ''
            }
            for lot in lots
        ]

        return JsonResponse(data, safe=False)

    except Exception as e:
        logger.error(f"Erreur dans lots_par_vaccin: {str(e)}")
        return JsonResponse({'error': 'Une erreur est survenue.'}, status=500)

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


class RendezVousListView(SingleTableMixin, FilterView):
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
        return context


class FactureListView(SingleTableMixin, FilterView):
    model = Facture
    table_class = FactureTable
    template_name = "pages/factures/facture_list.html"
    # filterset_class = FactureFilter
    paginate_by = 10  # Pagination : 10 factures par page


class RendezVousDetailView(DetailView):
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


#----------------------------------- Animal ------------------------------------------------------

class AnimalListView(ListView):
    model = Animal
    template_name = 'animaux/animal_list.html'
    context_object_name = 'animaux'
    ordering = ['-created_at']


class AnimalDetailView(DetailView):
    model = Animal
    template_name = 'animaux/animal_detail.html'
    context_object_name = 'animal'


class AnimalUpdateView(UpdateView):
    model = Animal
    template_name = 'animaux/animal_form.html'
    fields = '__all__'
    success_url = reverse_lazy('animal_list')


class AnimalDeleteView(DeleteView):
    model = Animal
    template_name = 'animaux/animal_confirm_delete.html'
    success_url = reverse_lazy('animal_list')


#-------------------- Protocole de Vaccinantion ------------------------------------#

class ProtocoleVaccinationListView(ListView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_list.html'
    context_object_name = 'protocoles'


class ProtocoleVaccinationDetailView(DetailView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_detail.html'
    context_object_name = 'protocole'


class ProtocoleVaccinationUpdateView(UpdateView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_form.html'
    fields = '__all__'
    success_url = reverse_lazy('protocole_list')


class ProtocoleVaccinationDeleteView(DeleteView):
    model = ProtocoleVaccination
    template_name = 'protocoles/protocole_confirm_delete.html'
    success_url = reverse_lazy('protocole_list')


#----------------------  Vaccinantion ------------------------------------
@login_required
def attestation_vaccination(request, vaccination_id):
    vaccination = get_object_or_404(Vaccination, id=vaccination_id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 100, "ATTESTATION DE VACCINATION")

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 150, f"Nom du patient : {vaccination.patient.nom} {vaccination.patient.prenoms}")
    p.drawString(100, height - 170, f"Date de vaccination : {vaccination.date_effective.strftime('%d/%m/%Y')}")
    p.drawString(100, height - 190, f"Protocole : {vaccination.protocole.nom}")
    p.drawString(100, height - 210, f"Vaccin : {vaccination.vaccin.nom}")
    p.drawString(100, height - 230, f"Vaccin : {vaccination.vaccin.nom}")
    p.drawString(100, height - 250, f"Lot : {vaccination.dose_numero} - Volume : {vaccination.dose_ml} ml")
    p.drawString(100, height - 280, f"Voie d'injection : {vaccination.get_voie_injection_display()}")

    p.drawString(100, height - 320, f"Fait le : {datetime.now().strftime('%d/%m/%Y')}")
    p.drawString(100, height - 350, "Signature du responsable : ________________________")

    p.showPage()
    p.save()

    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf')


class VaccinationListView(LoginRequiredMixin, ListView):
    model = Vaccination
    template_name = 'pages/vaccinations/vaccination_list.html'
    context_object_name = 'vaccinations'
    ordering = ['-created_at']
    paginate_by = 10


class VaccinationDetailView(LoginRequiredMixin, DetailView):
    model = Vaccination
    template_name = 'pages/vaccinations/vaccination_detail.html'
    context_object_name = 'vaccination'


class VaccinationUpdateView(UpdateView):
    model = Vaccination
    template_name = 'vaccinations/vaccination_form.html'
    fields = '__all__'
    success_url = reverse_lazy('vaccination_list')


class VaccinationDeleteView(DeleteView):
    model = Vaccination
    template_name = 'vaccinations/vaccination_confirm_delete.html'
    success_url = reverse_lazy('vaccination_list')
