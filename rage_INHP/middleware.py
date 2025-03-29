from django.shortcuts import redirect


class RoleBasedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        role_paths = {
            'National': '/National/',
            'Regional': '/Regional/',
            'DistrictSanitaire': '/DistrictSanitaire/',
            'dashboard': '/dashboard/',
        }

        if request.user.is_authenticated and request.path == '/':
            return redirect(role_paths.get(request.user.roleemployee, '/'))

        return self.get_response(request)
