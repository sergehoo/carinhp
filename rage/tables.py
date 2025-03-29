import django_tables2 as tables
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django_tables2 import A

from rage.models import RendezVousVaccination, Facture, Preexposition, PostExposition, RageHumaineNotification
from rage_INHP.forms import VaccinationForm, PaiementForm

from datetime import datetime, timedelta, date, time
from django.utils.timezone import make_aware, is_naive


class PreExpositionTable(tables.Table):
    client_nom = tables.Column(accessor="client.nom", verbose_name="Nom")
    client_prenoms = tables.Column(accessor="client.prenoms", verbose_name="Prénoms")
    codeexpo = tables.Column(verbose_name="Code Expo")
    # date_prevue = tables.Column(verbose_name="Date Prévue")
    # doses_recues = tables.Column(verbose_name="Doses Reçues")
    # voie_administration = tables.Column(verbose_name="Voie d'Administration")
    # observance_vaccinale = tables.BooleanColumn(verbose_name="Observance Vaccinale")

    # Colonne dynamique pour les motifs de vaccination
    motifs_vaccination = tables.Column(empty_values=(), orderable=False, verbose_name="Motifs de Vaccination")

    # Actions
    actions = tables.TemplateColumn(
        template_name="expositions/partials/preexposition_actions.html",
        orderable=False
    )

    class Meta:
        model = Preexposition
        template_name = "django_tables2/bootstrap4.html"
        fields = (
            "client_nom", "client_prenoms", "codeexpo", "motifs_vaccination"
        )

    def render_motifs_vaccination(self, value, record):
        """
        Récupère et affiche les motifs sélectionnés sous forme de liste.
        """
        motifs = []
        if record.voyage:
            motifs.append('<span class="label label-primary label-inline font-weight-lighter mr-2">Voyage</span>')
        if record.mise_a_jour:
            motifs.append('<span class="label label-info label-inline font-weight-lighter mr-2">Mise à jour</span>')
        if record.protection_rage:
            motifs.append(
                '<span class="label label-success label-inline font-weight-lighter mr-2">Protection Rage</span>')
        if record.chien_voisin:
            motifs.append(
                '<span class="label label-warning label-inline font-weight-lighter mr-2">Chien du voisin</span>')
        if record.chiens_errants:
            motifs.append(
                '<span class="label label-danger label-inline font-weight-lighter mr-2">Chiens errants</span>')
        if record.autre and record.autre_motif:
            motifs.append(
                f'<span class="label label-dark label-inline font-weight-lighter mr-2">Autre ({record.autre_motif})</span>')
        elif record.autre:
            motifs.append('<span class="label label-dark label-inline font-weight-lighter mr-2">Autre</span>')

        return mark_safe("".join(motifs)) if motifs else mark_safe(
            '<span class="label label-secondary label-inline font-weight-lighter mr-2">Aucun</span>')


class RendezVousTable(tables.Table):
    date_rendez_vous = tables.Column(verbose_name="Date")
    patient = tables.Column(verbose_name="Patient", accessor="patient.nom")
    protocole = tables.Column(verbose_name="Protocole", accessor="protocole")

    dose_numero = tables.Column(verbose_name="Dose #")
    est_effectue = tables.Column(verbose_name="Statut", accessor="est_effectue")
    statut_rdv = tables.Column(verbose_name="État", empty_values=())
    exposition = tables.Column(verbose_name="Exposition", empty_values=(), orderable=False)
    observation_timer = tables.Column(verbose_name="Observation mapi", empty_values=(), orderable=False)

    actions = tables.TemplateColumn(
        template_name="rendez_vous/partials/rendez_vous_actions.html",
        orderable=False,
        verbose_name="Actions",
        extra_context={"vaccination_form": VaccinationForm()}
    )

    def render_patient(self, record):
        """ Affiche Nom + Prénom du patient """
        return f"{record.patient.nom} {record.patient.prenoms}"

    def render_dose_numero(self, value):
        """ Affiche le numéro de dose avec un suffixe en exposant """
        if value == 1:
            return format_html(f"{value}<sup>ère</sup> dose")  # 1ère
        return format_html(f"{value}<sup>ème</sup> dose")  # 2ème, 3ème, etc.

    def render_est_effectue(self, value):
        if value:
            return format_html('<span class="badge badge-success">Effectué</span>')
        return format_html('<span class="badge badge-warning">En attente</span>')

    def render_statut_rdv(self, record):
        """ Affichage dynamique du statut du rendez-vous (Passé, Aujourd'hui, À venir) """
        today = date.today()
        if record.date_rendez_vous < today:
            return format_html('<span class="badge badge-danger">Passé</span>')
        elif record.date_rendez_vous == today:
            return format_html('<span class="badge badge-primary">Aujourd\'hui</span>')
        else:
            return format_html('<span class="badge badge-info">À venir</span>')

    def render_exposition(self, record):
        """ Affiche 'Pré-Exposition' ou 'Post-Exposition' """
        if record.preexposition:
            return format_html('<span class="badge badge-success ">Pré-Exposition</span>')
        elif record.postexposition:
            return format_html('<span class="badge badge-danger">Post-Exposition</span>')
        return "-"

    def render_observation_timer(self, record):
        from datetime import time

        vaccination = record.patient.vaccination_set.filter(
            protocole=record.protocole,
            date_effective=record.date_rendez_vous
        ).first()

        if not vaccination or not vaccination.date_effective:
            return format_html('<span class="text-muted">-</span>')

        start_time = datetime.combine(vaccination.date_effective, time.min)
        if is_naive(start_time):
            start_time = make_aware(start_time)

        end_time = start_time + timedelta(minutes=15)
        current_time = now()

        if current_time >= end_time:
            return format_html('<span class="badge bg-success">Observation terminée</span>')

        remaining_seconds = int((end_time - current_time).total_seconds())
        timer_id = f"timer-{record.pk}"

        html = f"""
        <div x-data="observationTimer({remaining_seconds})" class="text-center space-y-1">
            <span x-text="formatted" class="badge bg-warning text-dark"></span>
            <div class="progress" style="height: 5px;">
                <div class="progress-bar bg-warning" role="progressbar"
                    :style="'width: ' + percent + '%'" :class="ended ? 'bg-success' : 'bg-warning'">
                </div>
            </div>
            <template x-if="ended">
                <div class="alert alert-success mt-1 p-1" x-show="showToast" x-transition>
                    ✅ Observation terminée
                </div>
            </template>
        </div>

        <script>
            function observationTimer(initialSeconds) {{
                return {{
                    seconds: initialSeconds,
                    total: initialSeconds,
                    percent: 100,
                    formatted: '',
                    ended: false,
                    showToast: false,
                    init() {{
                        this.update();
                        this.tick();
                    }},
                    tick() {{
                        if (this.seconds <= 0) {{
                            this.ended = true;
                            this.formatted = "Observation terminée";
                            this.showToast = true;
                            return;
                        }}
                        setTimeout(() => {{
                            this.seconds--;
                            this.update();
                            this.tick();
                        }}, 1000);
                    }},
                    update() {{
                        const min = Math.floor(this.seconds / 60);
                        const sec = this.seconds % 60;
                        this.formatted = `${{min}} min ${{sec < 10 ? '0' + sec : sec}} sec`;
                        this.percent = Math.floor((this.seconds / this.total) * 100);
                    }}
                }};
            }}
        </script>
        """
        return mark_safe(html)

    class Meta:
        model = RendezVousVaccination
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            "date_rendez_vous", "patient", "protocole", "dose_numero", "est_effectue", "statut_rdv",
            "observation_timer",
            "exposition")


class FactureTable(tables.Table):
    id = tables.Column(verbose_name="ID")
    patient = tables.Column(verbose_name="Patient")
    montant_total = tables.Column(verbose_name="Montant Total (CFA)")
    montant_paye = tables.Column(verbose_name="Montant Payé (CFA)")
    reste_a_payer = tables.Column(verbose_name="Reste à Payer (CFA)")
    statut_paiement = tables.Column(verbose_name="Statut", accessor="get_statut_paiement_display")
    date_facture = tables.DateColumn(verbose_name="Date Facture", format="d-m-Y")

    actions = tables.TemplateColumn(
        template_name="factures/partials/facture_actions.html",
        orderable=False,
        verbose_name="Actions",
        extra_context={"paiement_form": PaiementForm()}
    )

    class Meta:
        model = Facture
        template_name = "django_tables2/bootstrap5.html"
        fields = ("id", "patient", "montant_total", "montant_paye", "reste_a_payer", "statut_paiement", "date_facture")


class PostExpositionTable(tables.Table):
    nom = tables.LinkColumn("postexposition_detail", args=[A("pk")], accessor="client.nom",
                            verbose_name="Nom du Patient")
    prenoms = tables.Column(accessor="client.prenoms", verbose_name="Prénom")
    age = tables.Column(accessor="client.calculate_age", verbose_name="Âge")
    date_naissance = tables.Column(accessor="client.date_naissance", verbose_name="Date de naissance")
    sexe = tables.Column(accessor="client.sexe", verbose_name="Sexe")
    residence_commune = tables.Column(accessor="client.residence_commune", verbose_name="Commune de résidence")
    date_exposition = tables.DateColumn(format="d/m/Y", verbose_name="Date Exposition")
    gravite_oms = tables.Column(verbose_name="Gravité OMS")

    actions = tables.TemplateColumn(
        template_name="expositions/partials/postexposition_actions.html",
        orderable=False,
        verbose_name="Actions"
    )

    class Meta:
        model = PostExposition
        template_name = "django_tables2/bootstrap4.html"
        fields = (
            "nom", "prenoms", "date_naissance", "age", "sexe", "date_exposition", "residence_commune", "gravite_oms")


class RageHumaineNotificationTable(tables.Table):
    actions = tables.TemplateColumn(
        template_name='expositions/partials/rage_notification_actions.html',
        orderable=False,
        verbose_name="Actions"
    )
    nom = tables.LinkColumn("postexposition_detail", args=[A("pk")], accessor="client.nom",
                            verbose_name="Nom")
    prenoms = tables.Column(accessor="client.prenoms", verbose_name="Prénom")
    age = tables.Column(accessor="client.calculate_age", verbose_name="Âge", orderable=False)
    # date_naissance = tables.Column(accessor="client.date_naissance", verbose_name="Date de naissance")
    sexe = tables.Column(accessor="client.sexe", verbose_name="Sexe")
    residence_commune = tables.Column(accessor="client.residence_commune", verbose_name="Adresse")
    categorie_lesion = tables.Column(verbose_name="Gravité")
    date_notification = tables.DateColumn(format="d/m/Y", verbose_name="Notifié le")

    class Meta:
        model = RageHumaineNotification
        template_name = "django_tables2/bootstrap4.html"  # Utilisation de Bootstrap 4
        fields = (
            "nom", "prenoms", "age", "sexe", "residence_commune", 'date_notification', 'hopital', 'nature_exposition',
            'categorie_lesion', 'actions')
