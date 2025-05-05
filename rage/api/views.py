from django.http import JsonResponse

from rage.models import HealthRegion, DistrictSanitaire


def get_regions_by_pole(request):
    pole_id = request.GET.get('pole')
    regions = HealthRegion.objects.filter(poles__id=pole_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)


def get_districts_by_region(request):
    region_id = request.GET.get('region')
    districts = DistrictSanitaire.objects.filter(region__id=region_id).values('id', 'nom')
    return JsonResponse(list(districts), safe=False)
