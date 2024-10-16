from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, SAFE_METHODS


class NotAllowAny(BasePermission):
    def has_permission(self, request, view):
        raise NotFound


class AuthorAdminOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user
                or request.user.is_admin)
