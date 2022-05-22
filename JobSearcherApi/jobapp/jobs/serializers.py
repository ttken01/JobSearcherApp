import hashlib
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import serializers
from .models import *
from django.db.models import Avg


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ['id', 'name', 'description', 'category']


class CategorySerializer(serializers.ModelSerializer):
    majors = MajorSerializer(read_only=True, many=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'majors']


class PostSerializer(serializers.ModelSerializer):
    avatar_user = serializers.SerializerMethodField()
    major_name = serializers.SerializerMethodField()

    def get_major_name(self, obj):
        requests = self.context['request']
        return obj.major.name

    def get_avatar_user(self, obj):
        request = self.context['request']
        path = '/static/%s' % obj.user.avatar
        return request.build_absolute_uri(path)

    class Meta:
        model = Post
        exclude = ['active']
        extra_kwargs = {
            'avatar_user': {
                'read_only': True
            },
            'major_name': {
                'read_only': True
            }
        }


class ApplySerializer(serializers.ModelSerializer):
    CV_path = serializers.SerializerMethodField(source='CV')
    avatar_user = serializers.SerializerMethodField()

    def get_avatar_user(self, obj):
        request = self.context['request']
        path = '/static/%s' % obj.user.avatar
        return request.build_absolute_uri(path)

    def get_CV_path(self, obj):
        request = self.context['request']

        if obj.CV and not obj.CV.name.startswith("/static"):
            path = '/static/%s' % obj.CV.name
            return request.build_absolute_uri(path)

    class Meta:
        model = Apply
        fields = ['id', 'description', 'CV', 'post', 'user', 'CV_path', 'avatar_user']
        extra_kwargs = {
            'CV_path': {
                'read_only': True
            }, 'CV': {
                'write_only': True
            }, 'avatar_user': {
                'read_only': True
            }
        }


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['creator', 'hirer', 'rate']


class CommentSerializer(serializers.ModelSerializer):
    avatar_user = serializers.SerializerMethodField()
    name_user = serializers.SerializerMethodField()

    def get_name_user(self, obj):
        request = self.context['request']
        name = obj.creator.first_name + " " + obj.creator.last_name
        return name

    def get_avatar_user(self, obj):
        request = self.context['request']
        path = '/static/%s' % obj.creator.avatar
        return request.build_absolute_uri(path)

    class Meta:
        model = Comment
        fields = ['id', 'creator', 'hirer', 'content', 'avatar_user', 'name_user']
        extra_kwargs = {
            'avatar_user': {
                'read_only': True
            },
            'name_user': {
                'read_only': True
            }
        }


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['user', 'token']


class UserSerializer(serializers.ModelSerializer):
    avatar_path = serializers.SerializerMethodField(source='avatar')
    rateAvg = serializers.SerializerMethodField(read_only=True)

    def get_rateAvg(self, obj):
        requests = self.context['request']
        if obj.user_role == 3:
            a = Rating.objects.filter(hirer_id=obj.id).aggregate(Avg('rate'))
            return a['rate__avg']
        return 0

    def get_avatar_path(self, obj):
        request = self.context['request']
        if obj.avatar and not obj.avatar.name.startswith("/static"):
            path = '/static/%s' % obj.avatar.name

            return request.build_absolute_uri(path)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name',
                  'username', 'password', 'email',
                  'avatar', 'avatar_path',
                  'user_role', 'is_active', 'rateAvg']
        extra_kwargs = {
            'password': {
                'write_only': True
            }, 'avatar_path': {
                'read_only': True
            }, 'avatar': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        data = validated_data.copy()
        for attr, value in validated_data.items():
            print(value)
            if attr == 'avatar':
                print(value.name)
        user = User(**data)
        user.set_password(user.password)
        user.is_active = False
        user.save()

        salt = uuid.uuid4().hex
        hash_object = hashlib.sha256(salt.encode() + str(user.id).encode())
        token = hash_object.hexdigest() + ':' + salt

        token_serializer = TokenSerializer(data={'user': user.id, 'token': token})
        if token_serializer.is_valid(raise_exception=False):
            token_serializer.save()

            fullName = f'{user.first_name} {user.last_name}'
            html_message = render_to_string('confirm-email.html', {'fullName': fullName, 'token': token})
            content = strip_tags(html_message)
            send_mail('CONFIRM EMAIL USER',
                      content,
                      settings.EMAIL_HOST_USER,
                      [user.email],
                      html_message=html_message,
                      fail_silently=False)

        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class AuthUserDetailSerializer(UserSerializer):
    rating = serializers.SerializerMethodField()

    def get_rating(self, hirer):
        request = self.context.get('request')
        if request:
            r = Rating.objects.filter(hirer=hirer).filter(creator=request.user).first()
            if r:
                return r.rate

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ['rating']


class WaitingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waiting
        fields = ['user']
