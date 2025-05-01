from django.contrib import admin
from .models import Community, CommunityMember, CommunityModerator, CommunityRule, Flair, CommunitySetting

# Register your models here.
admin.site.register(Community)
admin.site.register(CommunityMember)
admin.site.register(CommunityModerator)
admin.site.register(CommunityRule)
admin.site.register(Flair)
admin.site.register(CommunitySetting)
