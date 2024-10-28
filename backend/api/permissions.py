from django.db.models import Model
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsAuthorAdminOrReadOnly(BasePermission):
    def has_object_permission(self, request: Request, view,
                              obj: Model) -> bool:
        return (request.method in SAFE_METHODS
                or obj.author == request.user)
