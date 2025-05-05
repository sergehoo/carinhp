from rage.core.version import get_version
from rage.models import PolesRegionaux


# def menu_context(request):
#     if request.user.is_authenticated:
#         user = request.user
#
#         # Récupérer les pôles régionaux, régions et districts en fonction du rôle
#         if user.roleemployee == 'National':
#             poles = PolesRegionaux.objects.prefetch_related('regions').all()
#
#         elif user.roleemployee == 'Regional':
#             poles = PolesRegionaux.objects.filter(regions__id=user.region_id).prefetch_related('regions')
#
#         elif user.roleemployee == 'DistrictSanitaire':
#             poles = PolesRegionaux.objects.filter(regions__districts__id=user.district_id).distinct()
#
#         elif user.roleemployee == 'CentreAntirabique':
#             poles = PolesRegionaux.objects.filter(regions__districts__centres__employees__user=user).distinct()
#
#         else:
#             poles = []
#
#         return {'poles': poles}
#
#     return {}  # Si l'utilisateur n'est pas connecté, retourner un contexte vide


def check_new_version(request):
    current = get_version()
    if request.session.get("current_version") != current:
        request.session["new_version"] = current
        request.session["current_version"] = current


APP_VERSION = get_version()
