from rest_framework import permissions

class IsProfileOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        profile_id = request.query_params.get("profile_id")
        if not profile_id:
            return False
        return str(request.user.id) == profile_id
