from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied  # Rediriger vers la page de connexion

            if request.user.roleemployee not in allowed_roles:
                raise PermissionDenied  # Bloquer l'accès

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
