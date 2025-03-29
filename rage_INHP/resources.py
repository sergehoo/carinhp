from import_export import resources

from rage.models import RageHumaineNotification


class RageHumaineNotificationResource(resources.ModelResource):
    class Meta:
        model = RageHumaineNotification
        fields = ('id', 'date_notification', 'hopital', 'agent_declarant', 'nature_exposition', 'categorie_lesion',
                  'evolution')  # Champs à exporter
        export_order = (
        'id', 'date_notification', 'hopital', 'agent_declarant', 'nature_exposition', 'categorie_lesion', 'evolution')
