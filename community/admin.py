from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.mixins import AddFieldsetsMixin
from community.models import Community


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    search_fields = ['handle', 'name']
    readonly_fields = []
    autocomplete_fields = ['members']
    list_display = ['handle', 'name', 'country_flag', 'language', 'timezone']
    list_filter = ['country', 'language']
    list_display_links = ['name']
    fieldsets = [
        (None, {'fields': ['handle', 'name', 'description']}),
        (_("Details"), {'fields': ['language', 'timezone', 'country', 'can_see', 'can_join']}),
        (_("Members"), {'fields': ['members']}),
    ]
    add_fieldsets = [
        (None, {'fields': ['handle', 'name', 'description']}),
        (_("Details"), {'fields': ['language', 'timezone', 'country', 'can_see', 'can_join']}),
    ]
    
    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ['handle']
        return self.readonly_fields
