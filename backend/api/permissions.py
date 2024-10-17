from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, SAFE_METHODS


class NotAllowAny(BasePermission):
    def has_permission(self, request, view):
        raise NotFound


class IsOwnerAdminOrReadOnly(BasePermission):
    def __init__(self, owner_attr='stub') -> None:
        self.owner_attr = owner_attr

    def has_object_permission(self, request, view, obj) -> bool:
        return (request.method in SAFE_METHODS
                or getattr(obj, self.owner_attr, False) == request.user
                or request.user.is_admin)
