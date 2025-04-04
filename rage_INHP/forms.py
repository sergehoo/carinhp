import phonenumbers
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils.safestring import mark_safe

from rage.models import Patient, situation_matrimoniales_choices, Sexe_choices, Goupe_sanguin_choices, Commune, \
    ProtocoleVaccination, Symptom, Echantillon, Vaccination, Vaccins, Caisse, Preexposition, PostExposition, \
    nbr_lesions_CHOICES, DistrictSanitaire, RageHumaineNotification, ESPECE_CHOICES, MAPI

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


class PatientForm(forms.ModelForm):
    nom = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Nom'})
    )
    prenoms = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Prénoms'})
    )
    telephone = forms.CharField(required=True,
                                widget=forms.TextInput(
                                    attrs={'type': 'tel', 'class': 'form-control form-control-lg form-control-outlined',
                                           'placeholder': '0701020304', 'id': 'phone'}))
    situation_matrimoniale = forms.ChoiceField(
        required=True,
        choices=situation_matrimoniales_choices,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined'})
    )
    lieu_naissance = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Lieu de naissance'})
    )
    date_naissance = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-lg form-control-outlined', 'type': 'date'})
    )
    genre = forms.ChoiceField(
        required=True,
        choices=Sexe_choices,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined'})
    )
    nationalite = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Nationalité'})
    )
    profession = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Profession'})
    )

    # Champs non obligatoires
    nbr_enfants = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Nombre d\'enfants'})
    )
    groupe_sanguin = forms.ChoiceField(
        required=False,
        choices=Goupe_sanguin_choices,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined'})
    )
    niveau_etude = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Niveau d\'études'})
    )
    employeur = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Employeur'})
    )
    commune = forms.ModelChoiceField(
        queryset=Commune.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined'})
    )
    lieu_habitation = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Lieu d’habitation'})
    )
    poids = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Poids (kg)'})
    )
    contact_proche = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Contact proche'})
    )
    patient_mineur = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    accompagnateur = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Accompagnateur'})
    )

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenoms', 'telephone', 'situation_matrimoniale', 'lieu_naissance', 'date_naissance',
            'genre', 'nationalite', 'profession', 'nbr_enfants', 'groupe_sanguin', 'niveau_etude',
            'employeur', 'commune', 'lieu_habitation', 'poids', 'contact_proche', 'patient_mineur', 'accompagnateur'
        ]

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        try:
            parsed_number = phonenumbers.parse(telephone, 'CI')
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Invalid phone number format.")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError("Invalid phone number.")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

    def clean(self):
        """ Vérifier si le patient existe déjà """
        cleaned_data = super().clean()
        nom = cleaned_data.get('nom')
        prenoms = cleaned_data.get('prenoms')
        telephone = cleaned_data.get('telephone')

        if nom and prenoms and telephone:
            # Vérifier si un patient avec les mêmes informations existe déjà
            if Patient.objects.filter(nom=nom, prenoms=prenoms, telephone=telephone).exists():
                raise ValidationError("Ce patient existe déjà dans la base de données.")

        return cleaned_data

    def clean_mandatory(self):
        """ Vérification des champs obligatoires """
        cleaned_data = super().clean()
        required_fields = ['nom', 'prenoms', 'telephone', 'situation_matrimoniale', 'lieu_naissance', 'date_naissance',
                           'genre', 'nationalite', 'profession']

        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, "Ce champ est obligatoire.")

        return cleaned_data


class ClientForm(forms.ModelForm):
    # accompagnateur_nature = forms.ChoiceField(required=False, label="Vètements déchirés ?")

    class Meta:
        model = Patient
        exclude = ['status',
                   'gueris',
                   'decede',
                   'cause_deces',
                   'date_deces', 'commune', 'centre_ar',
                   'created_by']
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.TextInput(attrs={'class': 'form-control'}),
            # 'commune': forms.Select(attrs={'class': 'form-control'}),
            # 'centre_ar': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'patient_mineur': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'accompagnateur': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_contact': forms.NumberInput(attrs={'class': 'form-control'}),
            'accompagnateur_adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_nature': forms.Select(attrs={'class': 'form-control'}),
            'accompagnateur_niveau_etude': forms.Select(attrs={'class': 'form-control'}),

            'proprietaire_animal': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'typeanimal': forms.TextInput(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                self.fields[field_name].widget = forms.CheckboxInput(attrs={'class': 'switch'})


class PreExpositionForm(forms.ModelForm):
    mesures_elimination_rage = forms.MultipleChoiceField(
        choices=mesure_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Preexposition
        fields = '__all__'
        exclude = ['client']
        widgets = {
            # 'client': forms.Select(attrs={'class': 'form-control'}),
            # Motif de vaccination
            'nom': forms.TextInput(attrs={'class': 'form-control', }),
            'autre_motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # Information sur la vaccination
            'canal_infos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # Connaissance et attitude
            'type_animal_aime': forms.Select(attrs={'class': 'form-control'}),
            'mesures_elimination_rage': forms.Select(attrs={'class': 'form-control '}),
            # Suivi vaccination
            'date_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_effective': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dose_ml': forms.NumberInput(attrs={'class': 'form-control'}),
            'lot': forms.TextInput(attrs={'class': 'form-control'}),
            'voie_administration': forms.Select(attrs={'class': 'form-control'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
            'conduite_animal_mordeur': forms.Select(attrs={'class': 'form-control'}),
            'appreciation_cout_var': forms.Select(attrs={'class': 'form-control'}),
            'reactions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'doses_recues': forms.NumberInput(attrs={'class': 'form-control'}),
            'dernier_var_animal_type': forms.TextInput(attrs={'class': 'form-control'}),
            'dernier_var_animal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Applique un widget de type checkbox stylisé à tous les champs BooleanField
    #     for field_name, field in self.fields.items():
    #         if isinstance(field, forms.BooleanField):
    #             self.fields[field_name].widget = forms.CheckboxInput(attrs={'class': 'checkbox-lg'})
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            if field.required:
                # Ajouter un astérisque au label
                # mark_safe() pour injecter du HTML (ex : <span>*</span>)
                field.label = mark_safe(f'{field.label} <span class="text-danger">*</span>')

                # Ajouter l'attribut HTML 'required' si le widget ne l'a pas déjà
                if 'required' not in field.widget.attrs:
                    field.widget.attrs['required'] = 'required'

            if isinstance(field, forms.BooleanField):
                self.fields[field_name].widget = forms.CheckboxInput(attrs={'class': 'switch'})

    def clean(self):
        cleaned_data = super().clean()
        autre = cleaned_data.get("autre")
        autre_motif = cleaned_data.get("autre_motif")

        if autre and not autre_motif:
            raise ValidationError({"autre_motif": "Veuillez préciser le motif si 'Autre' est sélectionné."})

        date_prevue = cleaned_data.get("date_prevue")
        date_effective = cleaned_data.get("date_effective")

        if date_effective and date_prevue and date_effective < date_prevue:
            raise ValidationError({"date_effective": "La date effective ne peut pas être antérieure à la date prévue."})

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
        fields = '__all__'  # Inclut tous les champs du modèle sans exception
        widgets = {
            # Identification du patient
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_proche': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_mineur': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accompagnateur_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'accompagnateur_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),

            # Exposition
            'date_exposition': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_exposition': forms.TextInput(attrs={'class': 'form-control'}),
            'exposition_commune': forms.TextInput(attrs={'class': 'form-control'}),
            'exposition_quartier': forms.TextInput(attrs={'class': 'form-control'}),

            #Circonstances
            'attaque_provoquee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'agression': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attaque_collective': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'professionnel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'type_professionnel': forms.Select(attrs={'class': 'form-control'}),

            # Nature de l’exposition
            'morsure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'griffure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lechage_saine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lechage_lesee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'autre': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'autre_nature_exposition': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Localisation de l'exposition
            'tete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cou': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'membre_superieur': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preciser_membre_sup': forms.TextInput(attrs={'class': 'form-control'}),
            'tronc': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preciser_tronc': forms.TextInput(attrs={'class': 'form-control'}),
            'organes_genitaux_externes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'membre_inferieur': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preciser_membre_inf': forms.TextInput(attrs={'class': 'form-control'}),
            'saignement_immediat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nbrlesions': forms.Select(attrs={'class': 'form-control'}),
            'vetements_presents': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dechires': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # 'nombre_lesions': forms.NumberInput(attrs={'class': 'form-control'}),

            # Animal
            'espece': forms.Select(attrs={'class': 'form-control'}),
            'autre_animal': forms.TextInput(attrs={'class': 'form-control'}),
            'statut_animal': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),

            'contact_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),
            'retour_info_proprietaire': forms.TextInput(attrs={'class': 'form-control'}),

            'avis': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'convocation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prophylaxie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'correctement_vaccine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'non_vaccine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vacinconnu': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nonajours': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'inconnu': forms.BooleanField(
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                label="Connu",
                required=False  # Facultatif : permet d'éviter une erreur si la case n'est pas cochée
            ),

            'errant': forms.BooleanField(
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                label="errant",
                required=False  # Facultatif : permet d'éviter une erreur si la case n'est pas cochée
            ),
            'date_derniere_vaccination': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            # Gravité et Surveillance
            'gravite_oms': forms.Select(attrs={'class': 'form-control'}),
            'surveillance_veterinaire': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'certificat': forms.TextInput(attrs={'class': 'form-control'}),
            'piece_jointe': forms.FileInput(attrs={'class': 'form-control'}),
            'date_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'Date_depot_car': forms.TextInput(attrs={'class': 'form-control'}),
            'Decision_de_poursuite_tar': forms.TextInput(attrs={'class': 'form-control'}),
            'Decision_d_arrete_tar': forms.TextInput(attrs={'class': 'form-control'}),

            # Diagnostic et Prise en charge
            'prelevement_animal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'diagnostic_laboratoire': forms.Select(attrs={'class': 'form-control'}),
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            # Dossier Médical
            'antecedents_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'probleme_coagulation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'details_problemes': forms.TextInput(attrs={'class': 'form-control'}),
            'immunodepression': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'details_immo': forms.TextInput(attrs={'class': 'form-control'}),
            'grossesse': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'details_grosesse': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'traitements_en_cours': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Antécédents vaccinaux
            'vat_dernier_injection': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vat_rappel': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vat_lot': forms.TextInput(attrs={'class': 'form-control'}),
            'vaccin_antirabique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'carnet_vaccinal': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Prise en charge
            'lavage_plaies': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'desinfection_plaies': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sutures': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'serum_antitetanique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'antibiotiques': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'details_antibiotiques': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Vaccination Antirabique
            'delai_traitement': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'immunoglobulines': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'details_vaccination': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Sérologie
            'serologie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'details_serologie': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Issue de la prise en charge
            'issue': forms.Select(attrs={'class': 'form-control'}),
            'observance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'evolution_patient': forms.Select(attrs={'class': 'form-control'}),
            'cause_deces': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date_deces': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            # Enregistrement
        }

    def __init__(self, *args, **kwargs):
        super(PostExpositionForm, self).__init__(*args, **kwargs)
        self.fields['nom'].required = True
        self.fields['prenoms'].required = True
        self.fields['contact'].required = True
        self.fields['date_naissance'].required = True
        self.fields['sexe'].required = True
        self.fields['commune'].required = True


class RageHumaineNotificationForm(forms.ModelForm):
    class Meta:
        model = RageHumaineNotification
        fields = '__all__'  # Inclure tous les champs

        widgets = {
            'date_notification': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_exposition': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_debut_vaccination': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_premiers_signes': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_hospitalisation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_deces': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),

            'hopital': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.TextInput(attrs={'class': 'form-control'}),
            'agent_declarant': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'cel': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),

            'lieu_exposition': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'precision_siege': forms.TextInput(attrs={'class': 'form-control'}),
            'precis_animal_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'autres_labos': forms.TextInput(attrs={'class': 'form-control'}),
            'produit_desinfection': forms.TextInput(attrs={'class': 'form-control'}),
            'lieu_hospitalisation': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_agent': forms.TextInput(attrs={'class': 'form-control'}),

            'nature_exposition': forms.Select(attrs={'class': 'form-control'}),
            'siege_lesion': forms.Select(attrs={'class': 'form-control'}),
            'categorie_lesion': forms.Select(attrs={'class': 'form-control'}),
            'animal_responsable': forms.Select(attrs={'class': 'form-control'}),
            'animal_suspect_rage': forms.Select(attrs={'class': 'form-control'}),
            'devenir_animal': forms.Select(attrs={'class': 'form-control'}),
            'protocole_vaccination': forms.Select(attrs={'class': 'form-control'}),
            'evolution': forms.Select(attrs={'class': 'form-control'}),
            'resultat_analyse': forms.Select(attrs={'class': 'form-control'}),
            'vaccination_antirabique': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'soins_locaux': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'desinfection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'trouble_comportement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'agitation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hospitalisation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClientPostExpositionForm(forms.ModelForm):
    """Formulaire combiné pour Patient et PostExposition"""

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

    # Champs spécifiques à PostExposition
    client = forms.ModelChoiceField(queryset=Patient.objects.all(), required=False,
                                    empty_label="Sélectionner un patient",

                                    widget=forms.Select(attrs={'class': 'form-control'}))
    date_exposition = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    lieu_exposition = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    exposition_commune = forms.ModelChoiceField(queryset=Commune.objects.all(),
                                                widget=forms.Select(attrs={'class': 'form-control', 'x-model': 'search',
                                                                           'x-on:input': 'filterOptions()'}),
                                                required=False)
    exposition_quartier = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)

    circonstance = forms.ChoiceField(choices=[
        ('Attaque provoquée', 'Attaque provoquée'),
        ('Agression', 'Agression'),
        ('Attaque collective', 'Attaque collective'),
        ('Professionnel', 'Professionnel')
    ], widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    attaque_provoquee = forms.BooleanField(required=False)
    agression = forms.BooleanField(required=False)
    attaque_collective = forms.BooleanField(required=False)
    professionnel = forms.BooleanField(required=False)
    type_professionnel = forms.ChoiceField(
        choices=[('Manipulation / Soins', 'Manipulation / Soins'), ('Laboratoire', 'Laboratoire')],
        widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    morsure = forms.BooleanField(required=False)
    griffure = forms.BooleanField(required=False)
    lechage_saine = forms.BooleanField(required=False, label="Léchage")
    contactanimalpositif = forms.BooleanField(required=False, label="Contact animal positif")
    contactpatientpositif = forms.BooleanField(required=False, label="Contact patient positif")
    autre = forms.BooleanField(required=False)
    autre_nature_exposition = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                                              required=False)

    tete = forms.BooleanField(required=False)
    cou = forms.BooleanField(required=False)
    membre_superieur = forms.BooleanField(required=False)
    preciser_membre_sup = forms.CharField(required=False)
    tronc = forms.BooleanField(required=False)
    preciser_tronc = forms.CharField(required=False)
    organes_genitaux_externes = forms.BooleanField(required=False)
    membre_inferieur = forms.BooleanField(required=False)
    preciser_membre_inf = forms.CharField(required=False)
    saignement_immediat = forms.BooleanField(required=False)
    vetements_presents = forms.BooleanField(required=False)
    dechires = forms.BooleanField(required=False, label="Vètements déchirés ?")
    siege_exposition = forms.CharField(required=False)

    nbrlesions = forms.ChoiceField(choices=nbr_lesions_CHOICES, required=False, label="Nombre lesions")

    espece = forms.ChoiceField(choices=[
        ('Chien', 'Chien'), ('Chat', 'Chat'), ('Singe', 'Singe'), ('Chauve-souris', 'Chauve-souris'), ('Autre', 'Autre')
    ], widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    domestic = forms.BooleanField(required=False, label="L'animal est il Domestique ?")

    autre_animal = forms.CharField(required=False)
    connais_proprio = forms.BooleanField(required=False, label="Informations sur le Propriétaire par la victime ?")
    # statut_animal = forms.CharField(required=False)
    # nom_proprietaire = forms.CharField(required=False)
    # contact_proprietaire = forms.CharField(required=False)
    # info_proprietaire = forms.IntegerField(required=False)
    # retour_info_proprietaire = forms.CharField(required=False)
    avis = forms.BooleanField(required=False)
    convocation = forms.BooleanField(required=False)
    prophylaxie = forms.BooleanField(required=False)

    correctement_vaccine = forms.BooleanField(required=False)
    non_vaccine = forms.BooleanField(required=False)
    vacinconnu = forms.BooleanField(required=False, label="inconnu")
    nonajours = forms.BooleanField(required=False, label="Non à jours")

    connu = forms.BooleanField(required=False)
    disponible = forms.BooleanField(required=False)
    disparu = forms.BooleanField(required=False)
    mort = forms.BooleanField(required=False)
    errant = forms.BooleanField(required=False)
    abatu = forms.BooleanField(required=False, label="Abattu")
    autrestatut = forms.BooleanField(required=False, label="Autre")
    date_derniere_vaccination = forms.DateField(required=False,
                                                widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gravite_oms = forms.ChoiceField(choices=[('I', 'I'), ('II', 'II'), ('III', 'III')],
                                    widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    surveillance_veterinaire = forms.BooleanField(required=False,
                                                  label="Mise sous surveillance vétérinaire")
    certificat = forms.CharField(required=False)
    piece_jointe = forms.FileField(required=False)
    date_etablissement = forms.DateField(required=False)
    Date_depot_car = forms.DateField(required=False)
    Decision_de_poursuite_tar = forms.CharField(required=False)
    Decision_d_arrete_tar = forms.CharField(required=False)
    prelevement_animal = forms.BooleanField(required=False)
    diagnostic_laboratoire = forms.ChoiceField(choices=[('Positif', 'Positif'), ('Négatif', 'Négatif')],
                                               widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    date_diagnostic = forms.DateField(required=False)
    antecedents_medicaux = forms.CharField(required=False)
    probleme_coagulation = forms.BooleanField(required=False)
    details_problemes = forms.CharField(required=False)
    immunodepression = forms.BooleanField(required=False)
    details_immo = forms.CharField(required=False)
    grossesse = forms.BooleanField(required=False, label="Grossesse en cours")
    details_grosesse = forms.CharField(required=False)
    allergies = forms.CharField(required=False)
    detail_traitements_en_cours = forms.CharField(required=False)
    traitements_en_cours = forms.BooleanField(required=False)
    vaccin_antirabique = forms.BooleanField(required=False)
    carnet_vaccinal = forms.CharField(required=False)
    lavage_plaies = forms.BooleanField(required=False, label="Lavage de la Plaie (Eau+Savon)")
    desinfection_plaies = forms.BooleanField(required=False)
    delai_apres_exposition = forms.CharField(required=False)
    produits_utilises = forms.CharField(required=False)
    sutures = forms.BooleanField(required=False)
    serum_antitetanique = forms.BooleanField(required=False)
    antibiotiques = forms.BooleanField(required=False)
    details_antibiotiques = forms.CharField(required=False)
    protocole_vaccination = forms.ModelChoiceField(queryset=ProtocoleVaccination.objects.all(), required=False)
    details_vaccination = forms.CharField(required=False)
    serologie = forms.BooleanField(required=False)
    details_serologie = forms.CharField(required=False)
    issue = forms.ChoiceField(choices=[('Perdu de vue', 'Perdu de vue'), ('Arrêté', 'Arrêté'), ('Terminé', 'Terminé')],
                              required=False)
    agent_enregistreur = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(ClientPostExpositionForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            # Ajoute `required` sur les champs obligatoires
            if field.required:
                field.widget.attrs['required'] = 'required'

            # Vérifie si le label est `None` et le remplace par le nom du champ
            label = field.label if field.label else field_name.replace("_", " ").capitalize()
            if field.required:
                field.label = mark_safe(f"{label} <span style='color: red;'>*</span>")

    def clean(self):
        cleaned_data = super().clean()

        autre_nature_exposition = cleaned_data.get("autre_nature_exposition")
        circonstance = cleaned_data.get("circonstance")  # Corrigé : Utilisation du bon champ

        if circonstance == "Autre" and not autre_nature_exposition:
            self.add_error("autre_nature_exposition", "Veuillez préciser la nature de l'exposition.")

        # Validation : Si le patient est décédé, cause et date doivent être renseignées
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
            'vaccin': forms.Select(attrs={'class': 'form-control', 'id': 'vaccin-select'}),
            'lot': forms.Select(attrs={'class': 'form-control', 'id': 'lot-select'}),
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
