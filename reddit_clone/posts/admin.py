from django.contrib import admin
from .models import Post, PostMedia, Vote, PostImage, PostSave

# Register your models here.
admin.site.register(Post)
admin.site.register(PostMedia)
admin.site.register(Vote)
admin.site.register(PostImage)
admin.site.register(PostSave)
