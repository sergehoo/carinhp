from import_export import resources

from rage.models import RageHumaineNotification, ProtocoleVaccination, LotVaccin, Vaccins


class RageHumaineNotificationResource(resources.ModelResource):
    class Meta:
        model = RageHumaineNotification
        fields = ('id', 'date_notification', 'hopital', 'agent_declarant', 'nature_exposition', 'categorie_lesion',
                  'evolution')  # Champs à exporter
        export_order = (
            'id', 'date_notification', 'hopital', 'agent_declarant', 'nature_exposition', 'categorie_lesion',
            'evolution')


class ProtocoleVaccinationResource(resources.ModelResource):
    class Meta:
        model = ProtocoleVaccination
        fields = (
            'id', 'type__nom_protocole', 'nom', 'duree', 'intervale_visite1_2', 'intervale_visite2_3',
            'intervale_visite3_4', 'intervale_visite4_5', 'nombre_visite', 'nombre_doses',
            'nbr_dose_par_rdv', 'technique__nom', 'volume_doses', 'created_by__username', 'created_at'
        )
        export_order = fields


class VaccinsResource(resources.ModelResource):
    class Meta:
        model = Vaccins
        fields = ('id', 'nom', 'unite', 'created_by__username', 'created_at')
        export_order = fields


class LotVaccinResource(resources.ModelResource):
    class Meta:
        model = LotVaccin
        fields = (
            'id',
            'numero_lot',
            'vaccin__nom',
            'centre__nom',
            'date_fabrication',
            'date_expiration',
            'quantite_initiale',
            'quantite_disponible',
        )
        export_order = fields
