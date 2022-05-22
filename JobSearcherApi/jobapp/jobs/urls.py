from django.contrib import admin
from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(prefix='categories', viewset=views.CategoryViewSet, basename='category')
router.register(prefix='majors', viewset=views.MajorViewSet, basename='major')
router.register(prefix='posts', viewset=views.PostViewSet, basename='post')
router.register(prefix='users', viewset=views.UserViewSet, basename='user')
router.register(prefix='applies', viewset=views.ApplyViewSet, basename='apply')
router.register(prefix='waits', viewset=views.WaitingViewSet, basename='waiting')
router.register(prefix='my-posts', viewset=views.MyPostViewSet, basename='my-post')
router.register(prefix='my-applies', viewset=views.MyApplyViewSet, basename='my-apply')
router.register(prefix='comments', viewset=views.CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
    path('confirm-user/<str:pk>', views.ConfirmUserViewSet.as_view())
]
