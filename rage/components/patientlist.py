from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django_unicorn.components import UnicornView

from rage.models import Patient


# class PatientlistView(UnicornView):
#     search = ""
#     genre = ""
#     nationalite = ""
#     status = ""
#     patients = []
#     page = 1
#     per_page = 10
#     total_pages = 1
#
#     def mount(self):
#         """Chargement initial des patients"""
#         self.filter_patients()
#
#     def updated(self, name):
#         """Déclencher le filtrage lorsqu'un champ est modifié"""
#         if name in ["search", "genre", "nationalite", "status"]:
#             self.page = 1  # Réinitialiser à la première page après un filtrage
#         self.filter_patients()
#
#     def filter_patients(self):
#         """Appliquer les filtres en fonction des sélections de l'utilisateur"""
#         queryset = Patient.objects.all()
#
#         if self.search:
#             queryset = queryset.filter(
#                 Q(nom__icontains=self.search) |
#                 Q(prenoms__icontains=self.search) |
#                 Q(code_patient__icontains=self.search)
#             )
#         if self.genre:
#             queryset = queryset.filter(genre=self.genre)
#         if self.nationalite:
#             queryset = queryset.filter(nationalite=self.nationalite)
#         if self.status:
#             queryset = queryset.filter(status=self.status)
#
#         queryset = queryset.order_by('-created_at')
#
#         paginator = Paginator(queryset, self.per_page)
#         page_obj = paginator.get_page(self.page)
#         self.total_pages = paginator.num_pages
#         self.patients = list(page_obj.object_list)
#
#     def next_page(self):
#         if self.page < self.total_pages:
#             self.page += 1
#             self.filter_patients()
#
#     def prev_page(self):
#         if self.page > 1:
#             self.page -= 1
#             self.filter_patients()
#
#     def reset_filters(self):
#         """Réinitialiser tous les filtres et revenir à la première page"""
#         self.search = ""
#         self.genre = ""
#         self.nationalite = ""
#         self.status = ""
#         self.page = 1
#         self.filter_patients()

class PatientlistView(UnicornView):
    search = ""
    sexe = ""
    commune = ""
    status = ""
    patients = []
    page = 1
    total_pages = 1

    def mount(self):
        self.filter_patients()

    def filter_patients(self):
        # queryset = Patient.objects.all()
        user = self.request.user
        queryset = Patient.objects.all()

        # 🔥 Restriction basée sur le role de l'utilisateur connecté
        if user.roleemployee == 'CentreAntirabique':
            queryset = queryset.filter(centre_ar=user.centre)

        elif user.roleemployee == 'DistrictSanitaire':
            if user.centre and user.centre.district:
                queryset = queryset.filter(centre_ar__district=user.centre.district)

        elif user.roleemployee == 'Regional':
            if user.centre and user.centre.district and user.centre.district.region:
                queryset = queryset.filter(
                    centre_ar__district__region=user.centre.district.region
                )

        # National → pas de filtrage

        if self.search:
            queryset = queryset.filter(
                models.Q(nom__icontains=self.search) | models.Q(prenoms__icontains=self.search)
            )

        if self.sexe:
            queryset = queryset.filter(sexe=self.sexe)

        if self.commune:
            queryset = queryset.filter(residence_commune=self.commune)

        if self.status:
            queryset = queryset.filter(status=self.status)

        self.total_pages = queryset.count() // 10 + 1
        self.patients = queryset[(self.page - 1) * 20:self.page * 20]

    def reset_filters(self):
        self.search = ""
        self.sexe = ""
        self.commune = ""
        self.status = ""
        self.filter_patients()

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.filter_patients()

    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.filter_patients()
