from django.db.models import Model
from rest_framework.exceptions import NotFound
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class NotAllowAny(BasePermission):
    def has_permission(self, request, view):
        raise NotFound


class IsAuthorAdminOrReadOnly(BasePermission):
    def has_object_permission(self, request: Request, view,
                              obj: Model) -> bool:
        return (request.method in SAFE_METHODS
                or obj.author == request.user
                or request.user.is_admin)
