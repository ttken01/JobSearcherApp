import requests
from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.template.response import TemplateResponse

from .models import *
from django.utils.html import mark_safe, format_html
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.urls import path, reverse


class ApplyInlineAdmin(admin.StackedInline):
    model = Apply
    fk_name = 'post'
    extra = 0


class PostForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Post
        fields = '__all__'


class PostAdmin(admin.ModelAdmin):
    form = PostForm
    search_fields = ['title']
    list_display = ['title', 'id', 'user']
    list_filter = ['user']
    inlines = [ApplyInlineAdmin, ]


class MajorInlineAdmin(admin.StackedInline):
    model = Major
    fk_name = 'category'  # tên khoá ngoại (tuỳ chọn)


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['name', 'created_date']
    list_display = ['id', 'name', 'created_date']
    inlines = [MajorInlineAdmin, ]


class MajorAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['name', 'created_date']
    list_display = ['id', 'name', 'created_date', 'statsview']

    def statsview(self, obj):
        url = reverse('admin:confirm_url')
        return format_html('<a class="button" href="{}">Xem Thống Kê</a>', url)

    def get_urls(self):
        return [
                   path('major-stats/', self.stats_view, name='confirm_url')
               ] + super().get_urls()

    def stats_view(self, request):
        if request.method == "POST":
            quarterly = request.POST['quarterly']
            y = request.POST['years']
            kw = request.POST['kw']
            where = ""
            if kw != '' or quarterly != '' or y != '':
                where = " where "

            if quarterly != '':
                queryq = ""
                if quarterly == '1':
                    queryq = " month(jobs_apply.created_date) in (1,2,3) "
                if quarterly == '2':
                    queryq = " month(jobs_apply.created_date) in (4,5,6) "
                if quarterly == '3':
                    queryq = " month(jobs_apply.created_date) in (7,8,9) "
                if quarterly == '4':
                    queryq = " month(jobs_apply.created_date) in (10,11,12) "

                where += queryq

            if y != '':
                queryq = " YEAR(jobs_apply.created_date) = " + y
                if quarterly != '':
                    where += "and"
                where += queryq

            if kw != '':
                if quarterly != '' or y != '':
                    where += " and"
                queryq = " jobs_major.name like '%%" + kw + "%%' "
                where += queryq

            c = Post.objects.filter(active=True).count()
            stats = Major.objects.raw(
                "select jobs_major.id, count(jobs_apply.id) as count, jobs_major.name from ((jobs_major inner join jobs_post on jobs_major.id=jobs_post.major_id) "
                "inner join jobs_apply on jobs_post.id=jobs_apply.post_id) "
                + where +
                " group by jobs_major.id ,jobs_major.name")
            yearss = Apply.objects.raw("select YEAR(created_date) as ye, id from jobs_apply group by ye")

            return TemplateResponse(request,
                                    'admin/post-stats.html', {
                                        'count': c,
                                        'stats': stats,
                                        'years': yearss
                                    })
        c = Post.objects.filter(active=True).count()
        # where = request.get.pop('quarterly', None)
        # if where:
        #     print(where)
        stats = Major.objects.raw('select jobs_major.id, count(jobs_apply.id) as count, jobs_major.name '
                                  'from ((jobs_major inner join jobs_post on jobs_major.id=jobs_post.major_id) '
                                  'inner join jobs_apply on jobs_post.id=jobs_apply.post_id) '
                                  'group by jobs_major.id ,jobs_major.name')

        yearss = Apply.objects.raw("select YEAR(created_date) as ye, id from jobs_apply group by ye")

        return TemplateResponse(request,
                                'admin/post-stats.html', {
                                    'count': c,
                                    'stats': stats,
                                    'years': yearss
                                })


class WaitingInlineAdmin(admin.StackedInline):
    model = Waiting
    fk_name = 'user'
    extra = 0


class UserAdmin(admin.ModelAdmin):
    search_fields = ['username']
    readonly_fields = ['image_admin']
    list_display = ['username', 'id', 'user_role', 'is_active']
    list_filter = ['user_role']
    inlines = [WaitingInlineAdmin, ]

    def image_admin(self, obj):
        if obj:
            return mark_safe(
                '<img src="/static/{url}" width="240" />'.format(url=obj.avatar.name)
            )


class WaitingAdmin(admin.ModelAdmin):
    list_display = [str, 'active']


class ApplyAdmin(admin.ModelAdmin):
    list_display = ['description', 'id', 'user', 'post', 'post_id']


admin.site.site_header = 'Jobs Searcher Project'
admin.site.index_title = 'Management Area'
admin.site.site_title = 'HTML'
admin.site.site_url = '/admin/jobs/major/major-stats'
# admin.site.


admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Major, MajorAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Apply, ApplyAdmin)
admin.site.register(Waiting, WaitingAdmin)
admin.site.register(Comment)
