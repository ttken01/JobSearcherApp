from audioop import max

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.template.loader import render_to_string
from rest_framework.views import APIView

from .models import *
from .serializers import *
from .paginators import PostPaginator
from .perms import *
from django.core.mail import send_mail
from django.utils.html import strip_tags


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.filter(active=True)
    serializer_class = CategorySerializer


class MajorViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Major.objects.filter(active=True)
    serializer_class = MajorSerializer


class PostViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.CreateAPIView,
                  generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = Post.objects.filter(active=True).order_by('created_date')
    serializer_class = PostSerializer
    pagination_class = PostPaginator
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update']:
            return [OwnerPerms()]
        if self.action == 'create':
            return [PostCreateHirerPerms()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        q = self.queryset

        # tìm kiếm theo title
        keyw = self.request.query_params.get('keyword')
        if keyw:
            q = q.filter(title__icontains=keyw)

        # tìm kiếm theo mã ngành
        majorId = self.request.query_params.get('major_id')
        if majorId:
            q = q.filter(major_id=majorId)

        # tìm kiếm theo địa điểm
        local = self.request.query_params.get('location')
        if local:
            q = q.filter(location__icontains=local)

        fromSala = self.request.query_params.get('from_salary')
        toSala = self.request.query_params.get('to_salary')

        # tìm kiếm theo mức lương lớn hơn fromSala
        if fromSala:
            q = q.filter(from_salary__gt=fromSala)

        # tìm kiếm mức lương bé hơn toSala
        if toSala:
            q = q.filter(to_salary__lt=toSala)

        old = self.request.query_params.get('old')
        if old:
            return q.order_by('created_date')

        return q.order_by('created_date').reverse()

    @swagger_auto_schema(
        operation_description='Get the applies of a job',
        responses={
            status.HTTP_200_OK: ApplySerializer()
        }
    )
    @action(methods=['get'], detail=True, url_path='applies')
    def get_applies(self, request, pk):
        post = self.get_object()
        applies = post.applies.select_related('user').filter(active=True).order_by('created_date').reverse()

        kw = request.query_params.get('kw')

        if kw:
            applies = applies.filter(description__icontains=kw)

        return Response(data=ApplySerializer(applies, many=True, context={'request': request}).data,
                        status=status.HTTP_200_OK)


class ApplyViewSet(viewsets.ViewSet, generics.CreateAPIView,
                   generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = Apply.objects.all()
    serializer_class = ApplySerializer

    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update']:
            return [OwnerPerms()]

        return [permissions.IsAuthenticated()]


class CommentViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [CommentOwnerPerms()]
        return [permissions.IsAuthenticated()]


class UserViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView,
                  generics.UpdateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return AuthUserDetailSerializer

        return UserSerializer

    def get_permissions(self):
        if self.action == 'rating':
            return [RatingPerms()]
        if self.action == 'current_user':
            return [permissions.IsAuthenticated()]
        if self.action in ['update', 'partial_update']:
            return [UserOwnerPerms()]
        if self.action == 'list':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(methods=['get'], url_path="current-user", detail=False)
    def current_user(self, request):
        return Response(self.serializer_class(request.user, context={'request': request}).data,
                        status=status.HTTP_200_OK)

    @action(methods=['get'], url_path="hirer-user", detail=False)
    def hirer_user(self, request):
        user = User.objects.filter(user_role=3)
        keyw = self.request.query_params.get('keyword')
        if keyw:
            a = user.filter(first_name__icontains=keyw)
            if a.count() == 0:
                a = user.filter(last_name__icontains=keyw)
            user = a
        if request.user.is_authenticated:
            return Response(data=AuthUserDetailSerializer(user, many=True, context={'request': request}).data,
                            status=status.HTTP_200_OK)
        return Response(data=UserSerializer(user, many=True, context={'request': request}).data,
                        status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='rating', detail=True)
    def rating(self, request, pk):
        hirer = self.get_object()
        creator = request.user

        r, _ = Rating.objects.get_or_create(hirer=hirer, creator=creator)
        r.rate = request.data.get('rate', 0)
        try:
            r.save()
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(data=AuthUserDetailSerializer(hirer, context={'request': request}).data,
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description='Get the applies of a job',
        responses={
            status.HTTP_200_OK: CommentSerializer()
        }
    )
    @action(methods=['get'], detail=True, url_path='comments')
    def get_comment(self, request, pk):
        user = self.get_object()
        comments = user.hirer_cmt.select_related('creator').order_by('created_date').reverse()

        kw = request.query_params.get('kw')

        if kw:
            comments = comments.filter(description__icontains=kw)

        return Response(data=CommentSerializer(comments, many=True, context={'request': request}).data,
                        status=status.HTTP_200_OK)


class ConfirmUserViewSet(APIView):

    def get(self, request, pk, format=None):
        tokenObj = Token.objects.filter(token=pk).first()

        user = User.objects.filter(id=tokenObj.user.id).first()

        if user:
            user_serializer = UserSerializer(user, data={'is_active': True}, partial=True)
            if user_serializer.is_valid(raise_exception=False):
                user_serializer.save()

                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


class WaitingViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Waiting.objects.all()
    serializer_class = WaitingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [WaitingHirerPerms()]
        return [permissions.IsAdminUser()]

    def create(self, request):
        user = request.user
        # content = 'Xin chào ' + user.first_name + ' ' + user.last_name + \
        #           ', yêu cầu đăng ký nhà tuyển dụng của bạn đang được xử lý. Vui lòng chờ trong 1-2 ngày '
        fullName = f'{user.first_name} {user.last_name}'
        html_message = render_to_string('mail.html', {'fullName': fullName})
        content = strip_tags(html_message)
        send_mail('Đăng Ký Nhà Tuyển Dụng',
                  content,
                  settings.EMAIL_HOST_USER,
                  [user.email],
                  html_message=html_message,
                  fail_silently=False)

        wait = Waiting.objects.create(user=user)
        serializer = WaitingSerializer(wait)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyPostViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = PostPaginator

    def get_queryset(self):
        user = self.request.user
        return Post.objects.filter(user=user)

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['get'], url_path="hirer-post", detail=False)
    def hirer_post(self, request):
        id = self.request.query_params.get('id')
        post = Post.objects.filter(user_id=id)
        return Response(data=PostSerializer(post, many=True, context={'request': request}).data,
                        status=status.HTTP_200_OK)


class MyApplyViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = ApplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Apply.objects.filter(user=user)
