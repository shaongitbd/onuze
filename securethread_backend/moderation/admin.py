from django.contrib import admin
from .models import Report, BanAppeal

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'content_type', 'reason', 'status', 'created_at', 'community')
    list_filter = ('status', 'content_type', 'community')
    search_fields = ('reporter__username', 'reason', 'details')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('reporter', 'resolved_by', 'community')
    
@admin.register(BanAppeal)
class BanAppealAdmin(admin.ModelAdmin):
    list_display = ('user', 'appeal_type', 'status', 'created_at', 'community')
    list_filter = ('status', 'appeal_type')
    search_fields = ('user__username', 'reason', 'evidence')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('user', 'community', 'reviewed_by')
