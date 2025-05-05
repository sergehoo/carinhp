import phonenumbers
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import inlineformset_factory
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from phonenumber_field.formfields import PhoneNumberField as FormPhoneNumberField


from rage.models import Patient, situation_matrimoniales_choices, Sexe_choices, Goupe_sanguin_choices, Commune, \
    ProtocoleVaccination, Symptom, Echantillon, Vaccination, Vaccins, Caisse, Preexposition, PostExposition, \
    nbr_lesions_CHOICES, DistrictSanitaire, RageHumaineNotification, ESPECE_CHOICES, MAPI, OUI_NON_CHOICES, \
    Retour_CHOICES, Membre_Superieur_CHOICES, Tete_Cou_CHOICES, Grossesse_SEMAINES_CHOICES, delai_CHOICES, \
    NIVEAU_ETUDE_CHOICES, LotVaccin, EmployeeUser, CentreAntirabique, Membre_Inferieur_CHOICES, Tronc_CHOICES, \
    CARACASSE_CHOICES, InjectionImmunoglobuline, STATUT_VACCINAL_CHOICES

mesure_CHOICES = [('Abattage des chiens', 'Abattage des chiens'),
                  ('Eviter d’avoir un chien', 'Eviter d’avoir un chien'),
                  ('Vacciner les chiens', 'Vacciner les chiens'),
                  ('Eviter la divagation des chiens ', 'Eviter la divagation des chiens'),
                  ('Organiser des séances de CCC', 'Organiser des séances de CCC'),
                  ('Vacciner la population contre la rage', 'Vacciner la population contre la rage'),
                  ('Sensibiliser particulièrement les propriétaires de chien',
                   'Sensibiliser particulièrement les propriétaires de chien'),
                  ('Intégrer rage dans le programme des cours au primaire',
                   'Intégrer rage dans le programme des cours au primaire'),
                  ]

conduite_CHOICES = [('Abattage', 'Abattage'), ('Surveillance vétérinaire', 'Surveillance vétérinaire'),
                    ('Ne rien faire', 'Ne rien faire'),
                    ('Autre', 'Autre')]

LIEU_EXPOSITION_CHOICES = [
    # 🏠 Milieu familial / privé
    ('a_domicile', 'À domicile'),
    ('Domicile_proche', 'Domicile d\'un proche'),
    ('Rue', 'Dans la rue'),
    ('Sur la route du champ', 'Sur la route du champ'),
    ('Dans un champ', 'Dans un champ'),
    ('Dans une Ferme', 'Dans une ferme'),
    ('Dans un Abattoir', 'Dans un abattoir'),
    ('Clinique vétérinaire', 'Clinique vétérinaire'),
    ('Sur une aire de Jeux', 'Sur une aire de Jeux'),
    ('Autre', 'Autre'),
]


class ClientForm(forms.ModelForm):
    # accompagnateur_nature = forms.ChoiceField(required=False, label="Vètements déchirés ?")
    contact = FormPhoneNumberField(region='CI', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    accompagnateur_contact = FormPhoneNumberField(region='CI', widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Patient
        exclude = ['status',
                   'gueris',
                   'decede',
                   'cause_deces',
                   'date_deces', 'centre_ar',
                   'created_by', 'mpi_upi']
        fields = '__all__'
        labels = {
            'accompagnateur': "Nom et prénom de l'accompagnateur",
            'accompagnateur_contact': "Contact",
            'accompagnateur_adresse': "Adresse",
            'accompagnateur_nature': "Quel est sa relation avec le patient ?",
            'accompagnateur_niveau_etude': "Niveau d'étude ",
            'secteur_activite': "Profession",
            'num_cmu': "Numeros CMU",
            'cni_num': "Numeros CNI/NNI",
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            # 'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control '}),
            'num_cmu': forms.TextInput(attrs={'class': 'form-control'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control'}),
            'cni_num': forms.TextInput(attrs={'class': 'form-control'}),
            'cni_nni': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(choices=NIVEAU_ETUDE_CHOICES, attrs={'class': 'form-control'}),
            # 'commune': forms.Select(attrs={'class': 'form-control'}),
            # 'centre_ar': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(
                attrs={'class': 'form-control select2', 'id': 'kt_select2_1', 'name': 'param'}),
            # 'patient_mineur': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'secteur_activite': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            # 'village': forms.TextInput(attrs={'class': 'form-control'}),
            'autretypeanimal': forms.TextInput(attrs={'class': 'form-control'}),

            'accompagnateur': forms.TextInput(attrs={'class': 'form-control'}),
            # 'accompagnateur_contact': forms.NumberInput(attrs={'class': 'form-control'}),
            'accompagnateur_adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_nature': forms.Select(attrs={'class': 'form-control'}),
            'accompagnateur_niveau_etude': forms.Select(attrs={'class': 'form-control'}),

            'proprietaire_animal': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'typeanimal': forms.TextInput(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commune'].required = True
        self.fields['date_naissance'].required = True
        self.fields['secteur_activite'].required = True
        self.fields['niveau_etude'].required = True
        self.fields['poids'].required = True
        # Tous les champs requis affichent une astérisque rouge
        for field_name, field in self.fields.items():
            if field.required:
                label = field.label or field_name.replace('_', ' ').capitalize()
                field.label = mark_safe(f"{label} <span style='color:red;'>*</span>")


class PreExpositionForm(forms.ModelForm):
    # mesures_elimination_rage = forms.MultipleChoiceField(
    #     choices=mesure_CHOICES,
    #     widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'})
    # )

    class Meta:
        model = Preexposition
        exclude = ['client']
        widgets = {
            'codeexpo': forms.TextInput(attrs={'class': 'form-control'}),
            'autre_motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'canal_infos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'type_animal_aime': forms.Select(attrs={'class': 'form-control'}),
            'conduite_animal_mordeur': forms.Select(attrs={'class': 'form-control'}),
            'appreciation_cout_var': forms.Select(attrs={'class': 'form-control'}),
            'dernier_var_animal_type': forms.TextInput(attrs={'class': 'form-control'}),
            'dernier_var_animal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'protocole_vaccination': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            # Ajouter form-control à tous sauf Checkbox/Radio
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)):
                existing_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f"{existing_classes} form-control".strip()

            # Ajouter l’astérisque rouge pour les champs requis
            if field.required:
                field.label = mark_safe(f"{field.label} <span class='text-danger'>*</span>")
                field.widget.attrs['required'] = 'required'

    def clean(self):
        cleaned_data = super().clean()

        autre = cleaned_data.get("autre")
        autre_motif = cleaned_data.get("autre_motif")
        if autre == "Oui" and not autre_motif:
            self.add_error("autre_motif", "Veuillez préciser le motif si 'Autre' est sélectionné.")

        date_prevue = cleaned_data.get("date_prevue")
        date_effective = cleaned_data.get("date_effective")
        if date_effective and date_prevue and date_effective < date_prevue:
            self.add_error("date_effective", "La date effective ne peut pas être antérieure à la date prévue.")

        return cleaned_data


class PreExpositionUpdateForm(forms.ModelForm):
    mesures_elimination_rage = forms.MultipleChoiceField(
        choices=mesure_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    conduite_animal_mordeur = forms.MultipleChoiceField(
        choices=conduite_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    class Meta:
        model = Preexposition
        fields = '__all__'
        exclude = ['client', 'created_by', 'created_at']
        widgets = {
            'codeexpo': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'autre_motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'canal_infos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'type_animal_aime': forms.Select(attrs={'class': 'form-control'}),
            'date_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_effective': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dose_ml': forms.NumberInput(attrs={'class': 'form-control'}),
            'lot': forms.TextInput(attrs={'class': 'form-control'}),
            'voie_administration': forms.Select(attrs={'class': 'form-control'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
            'appreciation_cout_var': forms.Select(attrs={'class': 'form-control'}),
            'reactions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'doses_recues': forms.NumberInput(attrs={'class': 'form-control'}),
            'dernier_var_animal_type': forms.TextInput(attrs={'class': 'form-control'}),
            'dernier_var_animal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'protocole_vaccination': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ajout des astérisques pour les champs requis
        for field_name, field in self.fields.items():
            if field.required:
                field.label = mark_safe(f'{field.label} <span class="text-danger">*</span>')
                if 'required' not in field.widget.attrs:
                    field.widget.attrs['required'] = 'required'

            # Style spécial pour les checkbox
            # if isinstance(field, forms.BooleanField):
            #     field.widget.attrs['class'] = 'form-check-input'

    def clean(self):
        cleaned_data = super().clean()

        # Validation des champs conditionnels
        autre = cleaned_data.get("autre")
        autre_motif = cleaned_data.get("autre_motif")
        if autre and not autre_motif:
            raise ValidationError({"autre_motif": "Veuillez préciser le motif si 'Autre' est sélectionné."})

        date_prevue = cleaned_data.get("date_prevue")
        date_effective = cleaned_data.get("date_effective")
        if date_effective and date_prevue and date_effective < date_prevue:
            raise ValidationError({"date_effective": "La date effective ne peut pas être antérieure à la date prévue."})

        return cleaned_data


class ClientPreExpositionForm(forms.ModelForm):
    """Formulaire combiné pour Patient et Preexposition"""

    # Champs spécifiques à Preexposition
    voyage = forms.BooleanField(required=False)
    mise_a_jour = forms.BooleanField(required=False, label="Mise à jours calendrier vaccinal")
    protection_rage = forms.BooleanField(required=False, label="Protection contre la rage")
    chien_voisin = forms.BooleanField(required=False, label="Chien dans le voisinage")
    chiens_errants = forms.BooleanField(required=False)
    autre = forms.BooleanField(required=False)
    autre_motif = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)

    tele = forms.BooleanField(required=False)
    radio = forms.BooleanField(required=False)
    sensibilisation = forms.BooleanField(required=False, label="Séances de sensibilisations")
    proche = forms.BooleanField(required=False, label="Un Proche ")
    presse = forms.BooleanField(required=False, label="Presse ecrite")
    passage_car = forms.BooleanField(required=False, label="Passage au CAR")
    diff_canal = forms.BooleanField(required=False)
    canal_infos = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)
    conduite_animal_mordeur = forms.MultipleChoiceField(choices=conduite_CHOICES,
                                                        widget=forms.SelectMultiple(attrs={'class': 'form-control'}))

    aime_animaux = forms.BooleanField(required=False, label="Aimez-vous les animaux de compagnie ?")
    type_animal_aime = forms.ChoiceField(choices=ESPECE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}),
                                         required=False)
    connait_protocole_var = forms.BooleanField(required=False,
                                               label="Connaissez vous le protocole vaccinale du Chien ?")
    dernier_var_animal_type = forms.CharField(required=False)
    dernier_var_animal_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    mesures_elimination_rage = forms.MultipleChoiceField(choices=mesure_CHOICES,
                                                         widget=forms.SelectMultiple(attrs={'class': 'form-control', }),
                                                         required=False)
    appreciation_cout_var = forms.ChoiceField(choices=[('Elevé', 'Elevé'), ('Acceptable', 'Acceptable'),
                                                       ('Pas à la portée de tous', 'Pas à la portée de tous'),
                                                       ('Moins couteux', 'Moins couteux')],
                                              widget=forms.Select(attrs={'class': 'form-control'}))

    # date_prevue = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    # lot = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    # observance_vaccinale = forms.BooleanField(required=False)

    class Meta:
        model = Patient
        exclude = ['status', 'gueris', 'decede', 'cause_deces', 'date_deces', 'centre_ar', 'created_by']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'num_cmu': forms.TextInput(attrs={'class': 'form-control'}),
            'cni_num': forms.TextInput(attrs={'class': 'form-control'}),
            'cni_nni': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'village': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'patient_mineur': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'accompagnateur': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_contact': forms.NumberInput(attrs={'class': 'form-control'}),
            'accompagnateur_adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_nature': forms.Select(attrs={'class': 'form-control'}),
            'accompagnateur_niveau_etude': forms.Select(attrs={'class': 'form-control'}),

            'proprietaire_animal': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'typeanimal': forms.Select(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        super(ClientPreExpositionForm, self).__init__(*args, **kwargs)
        self.fields['nom'].required = True
        self.fields['prenoms'].required = True
        self.fields['contact'].required = True
        self.fields['date_naissance'].required = True
        self.fields['sexe'].required = True
        self.fields['commune'].required = True

    def clean(self):
        cleaned_data = super().clean()

        autre = cleaned_data.get("autre")
        autre_motif = cleaned_data.get("autre_motif")
        if autre and not autre_motif:
            raise ValidationError({"autre_motif": "Veuillez préciser le motif si 'Autre' est sélectionné."})

        date_prevue = cleaned_data.get("date_prevue")
        dernier_var_animal_date = cleaned_data.get("dernier_var_animal_date")
        if dernier_var_animal_date and date_prevue and dernier_var_animal_date > date_prevue:
            raise ValidationError(
                {"dernier_var_animal_date": "La date du dernier vaccin ne peut pas être après la date prévue."})

        return cleaned_data


class PostExpositionForm(forms.ModelForm):
    class Meta:
        model = PostExposition
        fields = '__all__'
        exclude = ['created_by', 'convocation', 'prophylaxie', 'observance']

        widgets = {
            # Identification du patient
            'client': forms.Select(attrs={'class': 'form-control'}),

            # Exposition
            'date_exposition': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_exposition': forms.Select(choices=LIEU_EXPOSITION_CHOICES, attrs={'class': 'form-control'}),
            'exposition_commune': forms.Select(
                attrs={'class': 'form-control select2', 'id': 'kt_select2_2', 'name': 'param'}),
            'exposition_quartier': forms.TextInput(attrs={'class': 'form-control'}),

            'circonstance': forms.Select(attrs={'class': 'form-control'}),

            # Circonstances
            'attaque_provoquee': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'agression': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'attaque_collective': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'professionnel': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'type_professionnel': forms.Select(attrs={'class': 'form-control'}),

            # Nature de l’exposition
            'morsure': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'griffure': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'lechage_saine': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'lechage_lesee': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'contactanimalpositif': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'contactpatientpositif': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'autre': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'autre_nature_exposition': forms.TextInput(attrs={'class': 'form-control'}),

            # Siège de l’exposition
            'tete_cou': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'preciser_tetecou': forms.SelectMultiple(choices=Tete_Cou_CHOICES,
                                                     attrs={'class': 'form-control select2', 'id': "kt_select2_34",
                                                            'name': "param", 'multiple': "multiple"}),
            'membre_superieur': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'preciser_membre_sup': forms.SelectMultiple(choices=Membre_Superieur_CHOICES,
                                                        attrs={'class': 'form-control select2', 'id': "kt_select2_3",
                                                               'name': "param", 'multiple': "multiple"}),
            'tronc': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'preciser_tronc': forms.SelectMultiple(choices=Tronc_CHOICES,
                                                   attrs={'class': 'form-control select2', 'id': "kt_select2_32",
                                                          'name': "param", 'multiple': "multiple"}),

            'membre_inferieur': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'preciser_membre_inf': forms.SelectMultiple(choices=Membre_Inferieur_CHOICES,
                                                        attrs={'class': 'form-control select2', 'id': "kt_select2_33",
                                                               'name': "param", 'multiple': "multiple"}),

            'organes_genitaux_externes': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'saignement_immediat': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'vetements_presents': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'dechires': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'siege_exposition': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'vetements_dechires': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'nbrlesions': forms.Select(choices=nbr_lesions_CHOICES, attrs={'class': 'form-control'}),

            # Animal
            'espece': forms.Select(attrs={'class': 'form-control'}),
            'autre_animal': forms.TextInput(attrs={'class': 'form-control'}),
            'domestic': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'connais_proprio': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'nom_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),
            'info_proprietaire': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'retour_info_proprietaire': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),

            'avis': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'convocation': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'prophylaxie': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),

            'correctement_vaccine': forms.Select(choices=STATUT_VACCINAL_CHOICES, attrs={'class': 'form-control'}),
            # 'non_vaccine': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            # 'nonajours': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            # 'vacinconnu': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'carnet_Vaccin': forms.FileInput(attrs={'class': 'form-control'}),

            'connu': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'disponible': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'errant': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'disparu': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'mort': forms.Select(choices=CARACASSE_CHOICES, attrs={'class': 'form-control'}),
            'abatu': forms.Select(choices=CARACASSE_CHOICES, attrs={'class': 'form-control'}),
            'autre_statut': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'autre_statut_precis': forms.TextInput(attrs={'class': 'form-control'}),
            'date_derniere_vaccination': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            # Gravité et Surveillance
            'gravite_oms': forms.Select(attrs={'class': 'form-control'}),
            'surveillance_veterinaire': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'certificat': forms.TextInput(attrs={'class': 'form-control'}),
            'piece_jointe': forms.FileInput(attrs={'class': 'form-control'}),
            'date_etablissement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Date_depot_car': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Decision_de_poursuite_tar': forms.TextInput(attrs={'class': 'form-control'}),
            'Decision_d_arrete_tar': forms.TextInput(attrs={'class': 'form-control'}),

            # Diagnostic et Prise en charge
            'prelevement_animal': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'diagnostic_laboratoire': forms.Select(attrs={'class': 'form-control'}),
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            # Dossier Médical
            'antecedents_medicaux': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_antecedents': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'kt_tagify_1', 'name': 'tags',
                       'placeholder': 'Ajoutez des antécédents séparés par des virgules'}),
            'probleme_coagulation': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_problemes': forms.TextInput(attrs={'class': 'form-control'}),
            'immunodepression': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_immo': forms.TextInput(attrs={'class': 'form-control'}),
            'grossesse': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_grosesse': forms.Select(choices=Grossesse_SEMAINES_CHOICES, attrs={'class': 'form-control'}),
            'allergies': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_allergies': forms.TextInput(attrs={'class': 'form-control'}),
            'traitements_en_cours': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'details_traitements': forms.TextInput(attrs={'class': 'form-control'}),

            # Antécédents vaccinaux
            'vat_dernier_injection': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vat_rappel': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vat_lot': forms.TextInput(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'vaccin_antirabique': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'carnet_vaccinal': forms.FileInput(attrs={'class': 'form-control'}),
            'carnet_vaccinal_verso': forms.FileInput(attrs={'class': 'form-control'}),

            # Prise en charge
            'lavage_plaies': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'delai_apres_exposition': forms.Select(choices=delai_CHOICES, attrs={'class': 'form-control'}),
            'delai_apres_desinfection': forms.Select(choices=delai_CHOICES, attrs={'class': 'form-control'}),
            'desinfection_plaies': forms.Select(choices=delai_CHOICES, attrs={'class': 'form-control'}),
            'sutures': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'serum_antitetanique': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'antibiotiques': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_antibiotiques': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'produits_utilises': forms.TextInput(attrs={'class': 'form-control'}),

            # Vaccination Antirabique
            'delai_traitement': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'immunoglobulines': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'details_vaccination': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),

            # Sérologie
            'serologie': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'details_serologie': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),

            # Issue de la prise en charge
            'issue': forms.Select(attrs={'class': 'form-control'}),
            'observance': forms.Select(choices=OUI_NON_CHOICES, attrs={'class': 'form-control'}),
            'evolution_patient': forms.Select(attrs={'class': 'form-control'}),
            'cause_deces': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'maxlength': 500}),
            'date_deces': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'protocole_vaccination': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['espece'].required = True
        self.fields['lieu_exposition'].required = True
        self.fields['exposition_commune'].required = True
        self.fields['circonstance'].required = True
        self.fields['connu'].required = True
        self.fields['disponible'].required = True
        self.fields['errant'].required = True
        self.fields['disparu'].required = True
        self.fields['mort'].required = True
        self.fields['abatu'].required = True
        self.fields['correctement_vaccine'].required = True
        # self.fields['non_vaccine'].required = True
        # self.fields['nonajours'].required = True
        # self.fields['vacinconnu'].required = True
        self.fields['vaccin_antirabique'].required = True
        self.fields['lavage_plaies'].required = True
        self.fields['desinfection_plaies'].required = True
        # self.fields['profession'].required = True
        labels = {
            # Identification
            'client': "Patient associé",
            'date_exposition': "Date de l'exposition",
            'lieu_exposition': "Lieu de l'exposition",
            'exposition_commune': "Commune d'exposition",
            'exposition_quartier': "Quartier d'exposition",

            # Circonstances
            'circonstance': "Circonstance de l'exposition",
            'attaque_provoquee': "Attaque provoquée ?",
            'agression': "Agression ?",
            'attaque_collective': "Attaque collective ?",
            'professionnel': "Exposition professionnelle ?",
            'type_professionnel': "Circonstance chez professionnel",

            # Nature de l'exposition
            'morsure': "Morsure",
            'griffure': "Griffure",
            'lechage_saine': "Léchage sur peau saine",
            'lechage_lesee': "Léchage sur peau lésée",
            'contactanimalpositif': "Contact animal positif",
            'contactpatientpositif': "Contact patient suspect/positif",
            'autre': "Autre type d'exposition",
            'autre_nature_exposition': "Préciser autre nature",

            # Siège de l’exposition
            'tete_cou': "Atteinte à la tête et cou",
            'preciser_tetecou': "Préciser tête et cou",
            'membre_superieur': "Atteinte membre supérieur",
            'preciser_membre_sup': "Préciser membre e supérieur",
            'tronc': "Atteinte au tronc",
            'preciser_tronc': "Préciser tronc",
            'membre_inferieur': "Atteinte membre inférieur",
            'preciser_membre_inf': "Préciser membre inférieur",

            'organes_genitaux_externes': "Atteinte organes génitaux externes",

            'saignement_immediat': "Saignement immédiat",
            'vetements_presents': "Vêtements présents",
            'dechires': "Vêtements déchirés",
            'siege_exposition': "Détail siège exposition",
            'vetements_dechires': "Vêtements déchirés ?",
            'nbrlesions': "Nombre de lésions",

            # Animal
            'espece': "Espèce de l'animal",
            'autre_animal': "Autre animal",
            'domestic': "Animal domestique",
            'connais_proprio': "Connaissance du propriétaire",
            'nom_proprietaire': "Nom du propriétaire",
            'contact_proprietaire': "Contact du propriétaire",
            'info_proprietaire': "Informations sur le propriétaire par la victime ",
            'retour_info_proprietaire': "Retour du CAR au propriétaire (AVIS)",

            'correctement_vaccine': "Statut Vaccinal ",
            # 'nonajours': "Non à jour",
            # 'vacinconnu': "Statut vaccinal Inconnu",
            'carnet_Vaccin': "Joindre preuve de Vaccination",
            'carnet_vaccinal_verso': "Joindre le verso du carnet",

            # Gravité
            'gravite_oms': "Gravité (OMS)",

            # Surveillance
            'surveillance_veterinaire': "Surveillance vétérinaire",
            'certificat': "N° du certificat",
            'piece_jointe': "Pièce jointe",
            'date_etablissement': "Date établissement certificat",
            'Date_depot_car': "Date dépôt CAR",
            'Decision_de_poursuite_tar': "Décision de poursuite TAR",
            'Decision_d_arrete_tar': "Décision d'arrêt TAR",

            # Diagnostic
            'prelevement_animal': "Prélèvement d'échantillons animal",
            'diagnostic_laboratoire': "Diagnostic laboratoire",
            'date_diagnostic': "Date du diagnostic",

            # Dossier médical
            'antecedents_medicaux': "Antécédents médicaux",
            'probleme_coagulation': "Problème de coagulation",
            'details_problemes': "Détails des problèmes",
            'immunodepression': "Immunodépression",
            'details_immo': "Détails immunodépression",
            'grossesse': "Grossesse",
            'details_grosesse': "Terme grossesse",
            'allergies': "Allergies",
            'traitements_en_cours': "Traitements en cours",

            # Vaccination antirabique
            'vat_dernier_injection': "Date dernière injection VAT",
            'vat_rappel': "Date rappel VAT",
            'vat_lot': "Lot du VAT",
            'vaccin_antirabique': 'vaccin antirabique antérrieur',
            'carnet_vaccinal': "Carnet vaccinal",
            'delai_traitement': "Délai après exposition",
            'immunoglobulines': "Immunoglobulines administrées",
            'details_vaccination': "Détails vaccination",
            'lavage_plaies': "Lavage des plaies (eau + savon)",
            'desinfection_plaies': "Désinfection des plaies",
            'sutures': "Sutures réalisées",
            'serum_antitetanique': "Sérum antitétanique",
            'antibiotiques': "Antibiotiques administrés",
            'details_antibiotiques': "Détails antibiotiques",
            'serologie': "Sérologie",
            'details_serologie': "Détails sérologie",

            # Issue
            'issue': "Issue de la prise en charge",
            'protocole_vaccination': "Protocole de vaccination",
            'evolution_patient': "Évolution du patient",
            'cause_deces': "Cause du décès",
            'date_deces': "Date du décès",
        }

        if self.instance and self.instance.details_antecedents:
            if isinstance(self.instance.details_antecedents, list):
                self.fields['details_antecedents'].initial = ','.join(self.instance.details_antecedents)
            elif isinstance(self.instance.details_antecedents, str):
                self.fields['details_antecedents'].initial = self.instance.details_antecedents

        # Tous les champs requis affichent une astérisque rouge
        for field_name, field in self.fields.items():
            label_text = labels.get(field_name,
                                    field.label or field_name.replace('_', ' ').replace('vat', 'VAT').capitalize())
            if field.required:
                field.label = mark_safe(f"{label_text} <span style='color:red;'>*</span>")
            else:
                field.label = label_text

    # def clean_details_antecedents(self):
    #     data = self.cleaned_data.get('details_antecedents')
    #     if data:
    #         # Tagify renvoie une chaîne CSV
    #         return [tag.strip() for tag in data.split(',') if tag.strip()]
    #     return []

    def clean(self):
        cleaned_data = super().clean()
        patient_mineur = cleaned_data.get('patient_mineur')

        # Champs obligatoires si patient est mineur
        if patient_mineur:
            required_fields = [
                'accompagnateur',
                'accompagnateur_contact',
                'accompagnateur_nature',
                'accompagnateur_niveau_etude'
            ]

            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Ce champ est obligatoire pour un patient mineur.")

        return cleaned_data

class RageHumaineNotificationForm(forms.ModelForm):
    class Meta:
        model = RageHumaineNotification

        # Liste explicite des champs (on exclut created_at)
        fields = [
            "client",
            "date_notification",
            "hopital", "service", "agent_declarant",
            "adresse", "telephone", "cel", "email",
            "exposition",
            "date_exposition", "lieu_exposition", "pays",
            "nature_exposition", "autre_nature_exposition",
            "siege_lesion", "precision_siege", "categorie_lesion",
            "animal_responsable", "precis_animal_responsable",
            "animal_suspect_rage", "devenir_animal", "prelevement_animal",
            "resultat_analyse", "labo_pathologie_animale", "autres_labos",
            "soins_locaux", "desinfection", "produit_desinfection",
            "vaccination_antirabique", "date_debut_vaccination", "protocole_vaccination",
            "date_premiers_signes", "trouble_comportement", "agitation",
            "hospitalisation", "date_hospitalisation", "lieu_hospitalisation",
            "evolution", "date_deces",
            "signature_agent",
        ]

        widgets = {
            # ForeignKey → Select
            "client":                        forms.Select(attrs={"class": "form-control"}),
            "exposition":                    forms.Select(attrs={"class": "form-control"}),
            "lieu_exposition":               forms.Select(attrs={"class": "form-control"}),
            "signature_agent":               forms.Select(attrs={"class": "form-control"}),

            # Dates
            "date_notification":             forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_exposition":               forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_debut_vaccination":        forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_premiers_signes":          forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_hospitalisation":          forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_deces":                    forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            # Text inputs
            "hopital":                       forms.TextInput(attrs={"class": "form-control"}),
            "service":                       forms.TextInput(attrs={"class": "form-control"}),
            "agent_declarant":               forms.TextInput(attrs={"class": "form-control"}),
            "adresse":                       forms.TextInput(attrs={"class": "form-control"}),
            "telephone":                     forms.TextInput(attrs={"class": "form-control"}),
            "cel":                           forms.TextInput(attrs={"class": "form-control"}),
            "email":                         forms.EmailInput(attrs={"class": "form-control"}),
            "pays":                          forms.TextInput(attrs={"class": "form-control"}),
            "autre_nature_exposition":       forms.TextInput(attrs={"class": "form-control"}),
            "precision_siege":               forms.TextInput(attrs={"class": "form-control"}),
            "precis_animal_responsable":     forms.TextInput(attrs={"class": "form-control"}),
            "autres_labos":                  forms.TextInput(attrs={"class": "form-control"}),
            "produit_desinfection":          forms.TextInput(attrs={"class": "form-control"}),
            "lieu_hospitalisation":          forms.TextInput(attrs={"class": "form-control"}),

            # ChoiceFields → Select
            "nature_exposition":             forms.Select(attrs={"class": "form-control"}),
            "siege_lesion":                  forms.Select(attrs={"class": "form-control"}),
            "categorie_lesion":              forms.Select(attrs={"class": "form-control"}),
            "animal_responsable":            forms.Select(attrs={"class": "form-control"}),
            "animal_suspect_rage":           forms.Select(attrs={"class": "form-control"}),
            "devenir_animal":                forms.Select(attrs={"class": "form-control"}),
            "prelevement_animal":            forms.Select(attrs={"class": "form-control"}),
            "resultat_analyse":              forms.Select(attrs={"class": "form-control"}),
            "labo_pathologie_animale":       forms.Select(attrs={"class": "form-control"}),
            "soins_locaux":                  forms.Select(attrs={"class": "form-control"}),
            "desinfection":                  forms.Select(attrs={"class": "form-control"}),
            "vaccination_antirabique":       forms.Select(attrs={"class": "form-control"}),
            "protocole_vaccination":         forms.Select(attrs={"class": "form-control"}),
            "trouble_comportement":          forms.Select(attrs={"class": "form-control"}),
            "agitation":                     forms.Select(attrs={"class": "form-control"}),
            "hospitalisation":               forms.Select(attrs={"class": "form-control"}),
            "evolution":                     forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Assurez-vous toujours que la signature accepte *args et **kwargs,
        puis appelez super() avant toute personnalisation.
        """
        super().__init__(*args, **kwargs)
        # Exemple : vider le placeholder du champ « autre_nature_exposition » tant que non nécessaire
        self.fields["autre_nature_exposition"].widget.attrs.update({
            "placeholder": "Précisez si « Autres »"
        })
# class RageHumaineNotificationForm(forms.ModelForm):
#     class Meta:
#         model = RageHumaineNotification
#         fields = '__all__'  # Inclure tous les champs
#
#         widgets = {
#             'date_notification': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'date_exposition': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'date_debut_vaccination': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'date_premiers_signes': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'date_hospitalisation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'date_deces': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#
#             'hopital': forms.TextInput(attrs={'class': 'form-control'}),
#             'service': forms.TextInput(attrs={'class': 'form-control'}),
#             'agent_declarant': forms.TextInput(attrs={'class': 'form-control'}),
#             'adresse': forms.TextInput(attrs={'class': 'form-control'}),
#             'telephone': forms.TextInput(attrs={'class': 'form-control'}),
#             'cel': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#
#             'lieu_exposition': forms.TextInput(attrs={'class': 'form-control'}),
#             'pays': forms.TextInput(attrs={'class': 'form-control'}),
#             'precision_siege': forms.TextInput(attrs={'class': 'form-control'}),
#             'precis_animal_responsable': forms.TextInput(attrs={'class': 'form-control'}),
#             'autres_labos': forms.TextInput(attrs={'class': 'form-control'}),
#             'produit_desinfection': forms.TextInput(attrs={'class': 'form-control'}),
#             'lieu_hospitalisation': forms.TextInput(attrs={'class': 'form-control'}),
#             'signature_agent': forms.TextInput(attrs={'class': 'form-control'}),
#
#             'nature_exposition': forms.Select(attrs={'class': 'form-control'}),
#             'siege_lesion': forms.Select(attrs={'class': 'form-control'}),
#             'categorie_lesion': forms.Select(attrs={'class': 'form-control'}),
#             'animal_responsable': forms.Select(attrs={'class': 'form-control'}),
#             'animal_suspect_rage': forms.Select(attrs={'class': 'form-control'}),
#             'devenir_animal': forms.Select(attrs={'class': 'form-control'}),
#             'protocole_vaccination': forms.Select(attrs={'class': 'form-control'}),
#             'evolution': forms.Select(attrs={'class': 'form-control'}),
#             'resultat_analyse': forms.Select(attrs={'class': 'form-control'}),
#             'vaccination_antirabique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'soins_locaux': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'desinfection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'trouble_comportement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'agitation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'hospitalisation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
#
#         def __init__(self, *args, **kwargs):
#             # ATTENTION : la signature doit impérativement être (*args, **kwargs)
#             super().__init__(*args, **kwargs)
#             # Exemple : limiter le queryset de client si besoin
#             # self.fields['client'].queryset = Client.objects.filter(actif=True)


class ClientPostExpositionForm(forms.ModelForm):
    class Meta:
        model = PostExposition
        fields = '__all__'
        exclude = ['created_by', 'vaccin_antirabique', 'convocation']
        widgets = {
            # Identification Patient
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'num_cmu': forms.TextInput(attrs={'class': 'form-control'}),
            'cni_num': forms.TextInput(attrs={'class': 'form-control'}),
            'cni_nni': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'village': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'patient_mineur': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'accompagnateur': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_contact': forms.NumberInput(attrs={'class': 'form-control'}),
            'accompagnateur_adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_nature': forms.Select(attrs={'class': 'form-control'}),
            'accompagnateur_niveau_etude': forms.Select(attrs={'class': 'form-control'}),

            'proprietaire_animal': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'typeanimal': forms.Select(attrs={'class': 'form-control'}),

            'date_exposition': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_exposition': forms.TextInput(attrs={'class': 'form-control'}),
            'exposition_commune': forms.Select(
                attrs={'class': 'form-control select2', 'id': 'kt_select2_1', 'name': 'param'}),
            'exposition_quartier': forms.TextInput(attrs={'class': 'form-control'}),

            # Circonstance
            'circonstance': forms.Select(attrs={'class': 'form-control'}),
            'type_professionnel': forms.Select(attrs={'class': 'form-control'}),

            # Détails Animal
            'espece': forms.Select(attrs={'class': 'form-control'}),
            'autre_animal': forms.TextInput(attrs={'class': 'form-control'}),

            # Informations Vétérinaire
            'gravite_oms': forms.Select(attrs={'class': 'form-control'}),
            'diagnostic_laboratoire': forms.Select(attrs={'class': 'form-control'}),
            'certificat': forms.TextInput(attrs={'class': 'form-control'}),
            'piece_jointe': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'siege_exposition': forms.Textarea(attrs={'class': 'form-control'}),
            'antecedents_medicaux': forms.Textarea(attrs={'class': 'form-control'}),
            'details_problemes': forms.TextInput(attrs={'class': 'form-control'}),
            'details_immo': forms.TextInput(attrs={'class': 'form-control'}),
            'details_grosesse': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control'}),
            'traitements_en_cours': forms.Textarea(attrs={'class': 'form-control'}),
            'carnet_vaccinal': forms.Textarea(attrs={'class': 'form-control'}),
            'delai_traitement': forms.Textarea(attrs={'class': 'form-control'}),
            'immunoglobulines': forms.Textarea(attrs={'class': 'form-control'}),
            'details_vaccination': forms.Textarea(attrs={'class': 'form-control'}),
            'details_antibiotiques': forms.Textarea(attrs={'class': 'form-control'}),
            'details_serologie': forms.Textarea(attrs={'class': 'form-control'}),
            'cause_deces': forms.Textarea(attrs={'class': 'form-control'}),
            'protocole_vaccination': forms.Select(attrs={'class': 'form-control'}),
            'issue': forms.Select(attrs={'class': 'form-control'}),
            'evolution_patient': forms.Select(attrs={'class': 'form-control'}),
            'nbrlesions': forms.TextInput(attrs={'class': 'form-control'}),
            'produits_utilises': forms.TextInput(attrs={'class': 'form-control'}),
            'preciser_membre_sup': forms.TextInput(attrs={'class': 'form-control'}),
            'preciser_tronc': forms.TextInput(attrs={'class': 'form-control'}),
            'preciser_membre_inf': forms.TextInput(attrs={'class': 'form-control'}),

            'date_derniere_vaccination': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_etablissement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Date_depot_car': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_deces': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'Decision_de_poursuite_tar': forms.TextInput(attrs={'class': 'form-control'}),
            'Decision_d_arrete_tar': forms.TextInput(attrs={'class': 'form-control'}),

            'nom_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),
            'info_proprietaire': forms.NumberInput(attrs={'class': 'form-control'}),
            'retour_info_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),
        }

    OUI_NON_FIELDS = [
        # Circonstance Exposition
        'attaque_provoquee', 'agression', 'attaque_collective', 'professionnel',
        'morsure', 'griffure', 'lechage_saine', 'lechage_lesee',
        'contactanimalpositif', 'contactpatientpositif', 'autre',

        # Siège Exposition
        'tete', 'cou', 'membre_superieur', 'tronc', 'organes_genitaux_externes', 'membre_inferieur',
        'saignement_immediat', 'vetements_presents', 'dechires', 'vetements_dechires',

        # Animal
        'domestic', 'connais_proprio', 'correctement_vaccine', 'non_vaccine', 'nonajours', 'vacinconnu',
        'inconnu', 'errant', 'disparu', 'mort', 'abatu',

        # Surveillance
        'surveillance_veterinaire', 'prelevement_animal',

        # Médical
        'probleme_coagulation', 'immunodepression', 'grossesse', 'vaccin_antirabique', 'lavage_plaies',
        'desinfection_plaies', 'sutures', 'serum_antitetanique', 'serologie', 'observance'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.OUI_NON_FIELDS:
            if field_name in self.fields:
                self.fields[field_name].widget = forms.Select(
                    choices=OUI_NON_CHOICES,
                    attrs={'class': 'form-control'}
                )

        # Tous les champs requis affichent une astérisque rouge
        for field_name, field in self.fields.items():
            if field.required:
                label = field.label or field_name.replace('_', ' ').capitalize()
                field.label = mark_safe(f"{label} <span style='color:red;'>*</span>")

    def clean(self):
        cleaned_data = super().clean()
        circonstance = cleaned_data.get("circonstance")
        autre_nature_exposition = cleaned_data.get("autre_nature_exposition")

        if circonstance == "Autre" and not autre_nature_exposition:
            self.add_error("autre_nature_exposition", "Veuillez préciser la nature de l'exposition.")

        evolution_patient = cleaned_data.get("evolution_patient")
        if evolution_patient == "Décédé":
            if not cleaned_data.get("cause_deces"):
                self.add_error("cause_deces", "Veuillez indiquer la cause du décès.")
            if not cleaned_data.get("date_deces"):
                self.add_error("date_deces", "Veuillez indiquer la date du décès.")

        return cleaned_data


class PatientRageNotificationForm(forms.ModelForm):
    """Formulaire combiné pour Patient et RageHumaineNotification"""

    class Meta:
        model = Patient
        exclude = ['status', 'gueris', 'decede', 'cause_deces', 'date_deces', 'centre_ar', 'created_by']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'secteur_activite': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'village': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_mineur': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accompagnateur': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_contact': forms.NumberInput(attrs={'class': 'form-control'}),
            'accompagnateur_adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_nature': forms.Select(attrs={'class': 'form-control'}),
            'accompagnateur_niveau_etude': forms.Select(attrs={'class': 'form-control'}),
        }

    # Champs spécifiques à RageHumaineNotification
    date_notification = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    hopital = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    service = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    agent_declarant = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    adresse = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    cel = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    # Informations sur l'exposition
    date_exposition = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    lieu_exposition = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    exposition_commune = forms.ModelChoiceField(queryset=Commune.objects.all(),
                                                widget=forms.Select(attrs={'class': 'form-control'}),
                                                required=False)
    district_sanitaire_exposition = forms.ModelChoiceField(queryset=DistrictSanitaire.objects.all(),
                                                           widget=forms.Select(attrs={'class': 'form-control'}),
                                                           required=False)
    nature_exposition = forms.ChoiceField(choices=[
        ('Morsure', 'Morsure'), ('Griffure', 'Griffure'), ('Léchage', 'Léchage'),
        ('Simple manipulation', 'Simple manipulation'), ('Autres', 'Autres')
    ], widget=forms.Select(attrs={'class': 'form-control'}))
    siege_lesion = forms.ChoiceField(choices=[
        ('Tête et cou', 'Tête et cou'), ('Membre supérieur', 'Membre supérieur'),
        ('Tronc', 'Tronc'), ('OGE', 'OGE'), ('Membre inférieur', 'Membre inférieur')
    ], widget=forms.Select(attrs={'class': 'form-control'}))

    # Prophylaxie post-exposition
    soins_locaux = forms.BooleanField(required=False, label="Soins locaux : lavage de la plaie")
    desinfection = forms.BooleanField(required=False, label="Désinfection")
    produit_desinfection = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    vaccination_antirabique = forms.BooleanField(required=False, label="Vaccination antirabique")
    date_debut_vaccination = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                                             required=False)
    protocole_vaccination = forms.ChoiceField(choices=[('Essen', 'Essen'), ('Zagreb', 'Zagreb'), ('ID', 'ID')],
                                              widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("nature_exposition") == "Autres" and not cleaned_data.get("produit_desinfection"):
            raise ValidationError(
                {"produit_desinfection": "Veuillez préciser le produit utilisé pour la désinfection."})

        if cleaned_data.get("vaccination_antirabique") and not cleaned_data.get("date_debut_vaccination"):
            raise ValidationError({"date_debut_vaccination": "Veuillez renseigner la date de début de vaccination."})

        return cleaned_data


class SymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du symptôme'}),
        }


class EchantillonForm(forms.ModelForm):
    class Meta:
        model = Echantillon
        fields = ['patient', 'maladie', 'mode_preleve', 'date_collect', 'site_collect', 'agent_collect',
                  'status_echantillons', 'resultat']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'maladie': forms.Select(attrs={'class': 'form-control'}),
            'mode_preleve': forms.Select(attrs={'class': 'form-control'}),
            'date_collect': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'site_collect': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lieu de prélèvement'}),
            'agent_collect': forms.Select(attrs={'class': 'form-control'}),
            'status_echantillons': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Statut de l’échantillon'}),
            'resultat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VaccinationForm(forms.ModelForm):
    class Meta:
        model = Vaccination
        fields = ['vaccin', 'lot', 'voie_injection', 'dose_ml', 'date_effective']
        widgets = {
            'vaccin': forms.Select(
                attrs={'class': 'form-control vaccin-select select2', 'name': 'param'}),
            'lot': forms.Select(
                attrs={'class': 'form-control lot-select select2'}),
            'voie_injection': forms.Select(attrs={'class': 'form-control'}),
            'dose_ml': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_effective': forms.DateInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class VaccinsForm(forms.ModelForm):
    class Meta:
        model = Vaccins
        fields = ['nom', 'unite']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            # 'lot': forms.TextInput(attrs={'class': 'form-control'}),
            # 'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'unite': forms.Select(attrs={'class': 'form-control'}),
            # 'date_expiration': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # 'fournisseur': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Caisse
        fields = ['montant', 'mode_paiement']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'})
        }


class MAPIForm(forms.ModelForm):
    class Meta:
        model = MAPI
        fields = ['date_apparition', 'description', 'gravite', 'traitement_administre', 'evolution']
        widgets = {
            'date_apparition': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gravite': forms.Select(attrs={'class': 'form-control'}),
            'traitement_administre': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'evolution': forms.Select(attrs={'class': 'form-control'}),
        }


class VaccinForm(forms.ModelForm):
    class Meta:
        model = Vaccins
        fields = ['nom', 'nbr_dose', 'unite', 'prix']

        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'nbr_dose': forms.NumberInput(attrs={'class': 'form-control'}),
            'unite': forms.Select(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class LotVaccinForm(forms.ModelForm):
    class Meta:
        model = LotVaccin
        fields = ['numero_lot', 'vaccin', 'date_fabrication', 'date_expiration', 'quantite_initiale']
        widgets = {
            'date_fabrication': forms.DateInput(attrs={'type': 'date'}),
            'date_expiration': forms.DateInput(attrs={'type': 'date'}),
            'vaccin': forms.Select(attrs={'class': 'form-control'}),
        }


class EmployeeUserForm(UserCreationForm):
    class Meta:
        model = EmployeeUser
        fields = ('username', 'civilite', 'first_name', 'last_name', 'email',
                  'contact', 'fonction', 'roleemployee', 'centre', 'groups')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'roleemployee': forms.Select(attrs={'class': 'form-control'}),
            'centre': forms.Select(attrs={'class': 'form-control'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.fields['roleemployee'].initial == 'National':
            self.fields['roleemployee'].choices = [
                ('CentreAntirabique', 'Centre Antirabique'),
                ('DistrictSanitaire', 'District Sanitaire'),
            ]
        self.fields['groups'].label = "Permissions"


class EmployeeUserUpdateForm(UserChangeForm):
    password = None  # Ne pas afficher le champ password dans l'édition

    class Meta:
        model = EmployeeUser
        fields = ('username', 'civilite', 'first_name', 'last_name', 'email',
                  'contact', 'fonction', 'roleemployee', 'centre', 'is_active', 'groups')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'roleemployee': forms.Select(attrs={'class': 'form-control'}),
            'centre': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        centre_queryset = kwargs.pop('centre_queryset', None)
        super().__init__(*args, **kwargs)

        if centre_queryset is not None:
            self.fields['centre'].queryset = centre_queryset

        if not self.instance.is_superuser and self.instance.roleemployee != 'National':
            self.fields['roleemployee'].choices = [
                ('CentreAntirabique', 'Centre Antirabique'),
                ('DistrictSanitaire', 'District Sanitaire'),
            ]


class CentreAntirabiqueForm(forms.ModelForm):
    class Meta:
        model = CentreAntirabique
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control select2', 'id': 'kt_select2_1', 'name': 'param'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'geom': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].required = True


class InjectionImmunoglobulineForm(forms.ModelForm):
    class Meta:
        model = InjectionImmunoglobuline
        fields = [
            'patient', 'refus_injection', 'motif_refus', 'type_produit', 'dose_ml', 'voie_injection',
            'site_injection', 'numero_lot', 'date_peremption', 'laboratoire_fabricant', 'commentaire'
        ]
        exclude =['patient']
        widgets = {
            'patient': forms.HiddenInput(),
            'refus_injection': forms.CheckboxInput(attrs={'class': 'form-check-input','role': 'switch','id': 'refusInjectionSwitch'
}),
            'motif_refus': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'motifRefusField'}),
            'type_produit': forms.TextInput(attrs={'class': 'form-control'}),
            'dose_ml': forms.NumberInput(attrs={'class': 'form-control'}),
            'voie_injection': forms.Select(attrs={'class': 'form-control'}),
            'site_injection': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'numero_lot': forms.TextInput(attrs={'class': 'form-control'}),
            'date_peremption': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'laboratoire_fabricant': forms.TextInput(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        refus = cleaned_data.get("refus_injection")

        if refus:
            if not cleaned_data.get("motif_refus"):
                self.add_error("motif_refus", "Veuillez préciser le motif du refus.")
        else:
            required_fields = ['type_produit', 'dose_ml', 'voie_injection']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Ce champ est requis si le patient accepte l'injection.")

        return cleaned_data
