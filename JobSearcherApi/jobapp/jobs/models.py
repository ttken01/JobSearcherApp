from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField


class User(AbstractUser):
    avatar = models.ImageField(null=True, upload_to='users/%Y/%m')
    UserRole = (
        (1, 'ADMIN'),
        (2, 'USER'),
        (3, 'HIRER'),
    )
    user_role = models.IntegerField(
        choices=UserRole,
        default=2  # Choices is a list of Tuple
    )


class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token')
    token = models.CharField(max_length=256, blank=True, null=True)


class ModelBase(models.Model):
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Waiting(ModelBase):
    user = models.ForeignKey(User, null=True,
                             on_delete=models.CASCADE)

    def __str__(self):
        return (self.user.first_name + " " + self.user.last_name)


class Category(ModelBase):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Major(ModelBase):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    category = models.ForeignKey(Category,
                                 related_name='majors',
                                 null=True,
                                 on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Post(ModelBase):
    title = models.CharField(max_length=100, null=False)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=50)
    from_salary = models.FloatField(null=True, blank=True)
    to_salary = models.FloatField(null=True, blank=True)
    gender = models.CharField(max_length=25, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=50)
    time_work = models.CharField(max_length=50)
    due = models.DateTimeField(null=True, blank=True)
    description = RichTextField()
    major = models.ForeignKey(Major, related_name='post',
                              related_query_name='my_post',
                              on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Apply(ModelBase):
    description = models.TextField()
    CV = models.FileField(null=True, upload_to='applies/%Y/%m')
    post = models.ForeignKey(Post,
                             related_name='applies',
                             on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.description


class ActionBase(ModelBase):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator')
    hirer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hirer')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Rating(ActionBase):
    rate = models.SmallIntegerField(default=0)


class Comment(ActionBase):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator_cmt')
    hirer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hirer_cmt')
    content = models.TextField()

    def __str__(self):
        return self.content

# class Tag(ModelBase):
#     name = models.CharField(max_length=50, unique=True)
#
#     def __str__(self):
#         return self.name
