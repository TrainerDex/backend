from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from trainerdex.models import DataSource, Trainer, TrainerCode, Update, Evidence, EvidenceImage, Target, PresetTarget, PresetTargetGroup

admin.site.register(PresetTargetGroup)
admin.site.register(DataSource)


@admin.register(PresetTarget)
class PresetTargetAdmin(admin.ModelAdmin):

    list_display = ('name', 'stat', 'target')
    list_filter = ('stat',)
    search_fields = ('name', 'stat')


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):

    autocomplete_fields = ['trainer']
    list_display = ('trainer', 'total_xp', 'update_time', 'submission_date', 'has_modified_extra_fields')
    search_fields = ('trainer__nickname__nickname', 'trainer__username')
    ordering = ('-update_time',)
    date_hierarchy = 'update_time'


class TrainerCodeInline(admin.TabularInline):
    model = TrainerCode
    min_num = 1
    max_num = 1
    can_delete = False
    verbose_name_plural = TrainerCode._meta.verbose_name


class TargetInline(admin.TabularInline):
    model = Target
    min_num = 0


@admin.register(Trainer)
class TrainerAdmin(UserAdmin):

    list_display = [
        'nickname',
        'faction',
        'is_banned',
        'leaderboard_eligibility',
        'awaiting_verification',
        ]
    list_filter = [
        'faction',
        'is_banned',
        'is_active',
        'is_verified',
        ]
    search_fields = [
        'nickname__nickname',
        'first_name',
        'username',
        ]
    readonly_fields = [
        'old_id',
        ]
    
    # Get BaseUser fieldsets
    fieldsets = UserAdmin.fieldsets
    
    # Main set
    fieldsets[0][1]['fields'] += (
        'old_id',
        'faction',
        'start_date',
    )
    
    # Personal set
    fieldsets[1][1]['fields'] += (
        'country',
    )
    
    # Permissions Set
    fieldsets[2][1]['fields'] = (
        'is_banned',
        'is_verified',
        ) + fieldsets[2][1]['fields']
    
    # Get BaseUser fieldsets
    add_fieldsets = UserAdmin.add_fieldsets
    
    # Get top set
    add_fieldsets[0][1]['fields'] += (
        'faction',
        'start_date',
    )
    
    inlines = [
        TargetInline,
        TrainerCodeInline,
    ]
    
    def queryset(self, request):
        qs = super(TrainerAdmin, self).queryset(request)
        qs = qs.order_by('username', 'pk').distinct('pk')
        return qs


class EvidenceImageInline(admin.TabularInline):
    model = EvidenceImage
    min_num = 0


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    
    list_display = [
        'trainer',
        'approval',
        'content_type',
        'content_field',
    ]
    list_filter = [
        'approval',
        'content_type',
        'content_field',
    ]
    readonly_fields = [
        'content_object',
    ]
    fieldsets = [
        (_('Object'), {
            'fields': [
                'content_type',
                'object_pk',
                'content_object',
                'content_field',
            ],
        }),
        (None, {
            'fields': [
                'approval',
            ],
        }),
    ]
    inlines = [
        EvidenceImageInline,
    ]
