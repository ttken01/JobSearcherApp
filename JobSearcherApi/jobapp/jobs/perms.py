from rest_framework import permissions
from .models import User, Waiting


class OwnerPerms(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return request.user == obj.user


class CommentOwnerPerms(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.creator


class PostCreateHirerPerms(permissions.IsAuthenticated):

    # def has_object_permission(self, request, view, obj):
    #     return request.user_role == 3

    def has_permission(self, request, view):
        return request.user and request.user.user_role == 3


class UserOwnerPerms(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet.
        return obj == request.user


class UserAdminOwnerPerms(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet.
        return request.user.is_superuser


class WaitingHirerPerms(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if Waiting.objects.filter(user_id=request.user.id).count() > 0:
            return False
        else:
            return request.user.user_role != 3


class RatingPerms(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.user_role == 3
