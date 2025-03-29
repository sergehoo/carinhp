import django_filters
from django import forms

from rage.models import RendezVousVaccination, RageHumaineNotification


class RendezVousFilter(django_filters.FilterSet):
    patient = django_filters.CharFilter(field_name="patient__nom", lookup_expr="icontains", label="Patient",
                                        widget=forms.TextInput(
                                            attrs={'class': 'form-control', 'placeholder': 'Rechercher...'}))
    protocole = django_filters.CharFilter(field_name="protocole__nom", lookup_expr="icontains", label="Protocole",
                                          widget=forms.TextInput(
                                              attrs={'class': 'form-control', 'placeholder': 'Rechercher...'}))
    statut_rdv = django_filters.ChoiceFilter(choices=[
        ('Passé', 'Passé'),
        ('Aujourd\'hui', 'Aujourd\'hui'),
        ('À venir', 'À venir'),
    ], label="État du rendez-vous",
        widget=forms.Select(attrs={'class': 'form-control form-select'}))

    est_effectue = django_filters.BooleanFilter(label="Statut",
                                                widget=forms.Select(choices=[('', 'Tous'), ('true', 'Effectué'),
                                                                             ('false', 'En attente')],
                                                                    attrs={'class': 'form-control form-select '}))

    exposition = django_filters.ChoiceFilter(label="Exposition", method="filter_exposition",
                                             choices=[('preexposition', 'Pré-Exposition'),
                                                      ('postexposition', 'Post-Exposition')],
                                             widget=forms.Select(attrs={'class': 'form-select form-control'}))

    date_rendez_vous = django_filters.DateFilter(field_name="date_rendez_vous", lookup_expr="exact",
                                                 label="Date précise",
                                                 widget=forms.DateInput(
                                                     attrs={'type': 'date', 'class': 'form-control'},
                                                     format='%Y-%m-%d'))

    class Meta:
        model = RendezVousVaccination
        fields = ["patient", "protocole", "statut_rdv", "est_effectue", "exposition", "date_rendez_vous"]

    def filter_exposition(self, queryset, name, value):
        """ Filtre par type d'exposition (pré/post-exposition) """
        if value == 'preexposition':
            return queryset.filter(preexposition__isnull=False)
        elif value == 'postexposition':
            return queryset.filter(postexposition__isnull=False)
        return queryset


class RageHumaineNotificationFilter(django_filters.FilterSet):
    date_notification = django_filters.DateFilter(
        field_name="date_notification", lookup_expr='exact', label="Date de notification",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    hopital = django_filters.CharFilter(
        field_name="hopital", lookup_expr='icontains', label="Hôpital",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    agent_declarant = django_filters.CharFilter(
        field_name="agent_declarant", lookup_expr='icontains', label="Agent déclarant",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    nature_exposition = django_filters.ChoiceFilter(
        field_name="nature_exposition",
        choices=RageHumaineNotification._meta.get_field('nature_exposition').choices,
        label="Nature de l'exposition",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categorie_lesion = django_filters.ChoiceFilter(
        field_name="categorie_lesion",
        choices=RageHumaineNotification._meta.get_field('categorie_lesion').choices,
        label="Catégorie de la lésion",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    evolution = django_filters.ChoiceFilter(
        field_name="evolution",
        choices=RageHumaineNotification._meta.get_field('evolution').choices,
        label="Évolution",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = RageHumaineNotification
        fields = ['date_notification', 'hopital', 'agent_declarant', 'nature_exposition', 'categorie_lesion',
                  'evolution']
