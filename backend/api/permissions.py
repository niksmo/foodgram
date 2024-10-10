from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission


class NotAllowAny(BasePermission):
    def has_permission(self, request, view):
        raise NotFound
