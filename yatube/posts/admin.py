from django.contrib import admin

from .models import Group, Post, Follow, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'author', 'created')
    search_fields = ('text',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
