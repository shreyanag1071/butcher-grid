from rest_framework.permissions import BasePermission
from .models import User


class IsFarmOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.FARM_OWNER

    def has_object_permission(self, request, view, obj):
        facility = getattr(obj, "facility", obj)
        return facility.owner == request.user


class IsRegulator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.REGULATOR


class IsEnvAgency(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ENVIRONMENTAL_AGENCY
        )


class IsRegulatoryStaff(BasePermission):
    """Regulators or environmental agency staff."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            User.Role.REGULATOR,
            User.Role.ENVIRONMENTAL_AGENCY,
        )


class IsOwnerOrRegulator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role in (User.Role.REGULATOR, User.Role.ENVIRONMENTAL_AGENCY):
            return True
        facility = getattr(obj, "facility", obj)
        return facility.owner == request.user
