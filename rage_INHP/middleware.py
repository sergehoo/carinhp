from django.shortcuts import redirect


# class RoleBasedRedirectMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         role_paths = {
#             'National': '/National/',
#             'Regional': '/Regional/',
#             'DistrictSanitaire': '/DistrictSanitaire/',
#             'dashboard': '/dashboard/',
#         }
#
#         if request.user.is_authenticated and request.path == '/':
#             return redirect(role_paths.get(request.user.roleemployee, '/'))
#
#         return self.get_response(request)

class PermissionDeniedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        from django.core.exceptions import PermissionDenied
        if isinstance(exception, PermissionDenied):
            # Rediriger vers la page de connexion ou une page d'erreur spécifique
            return redirect('permission_denied')  # Remplacez par le nom de votre URL
        return None