from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from trainerdex.models import DataSource, Evidence, EvidenceImage, Nickname, PresetTarget, PresetTargetGroup, Target, Trainer, TrainerCode, Update
from trainerdex.models import TrainerQuerySet

admin.site.register(PresetTargetGroup)
admin.site.register(DataSource)


@admin.register(Nickname)
class NicknameAdmin(admin.ModelAdmin):
    search_fields = (
        'nickname',
        'user__username',
        )
    list_display = (
        'nickname',
        'user',
        'active',
        )
    list_filter = ('active',)
    list_display_links = ('nickname',)


@admin.register(PresetTarget)
class PresetTargetAdmin(admin.ModelAdmin):

    list_display = ('stat', 'name', 'target_str')
    list_filter = ('stat',)
    search_fields = ('stat', 'name')


def force_check_target(modeladmin, request, queryset):
    for x in queryset:
        x.check_reached()
        x.save(update_fields=['has_reached', 'date_reached'])
force_check_target.short_description = "Check if this target has been reached"

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):

    list_display = ('trainer', 'stat', 'name', 'target_str', 'has_reached', 'date_reached')
    list_filter = ('stat', 'has_reached')
    search_fields = ('trainer__nicknames__nickname', 'trainer__username', 'stat', 'name')
    actions = [force_check_target]


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):

    autocomplete_fields = ['trainer']
    list_display = ('trainer', 'total_xp', 'update_time', 'submission_date', 'has_modified_extra_fields')
    search_fields = ('trainer__nicknames__nickname', 'trainer__username')
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(has_reached=False)


@admin.register(Trainer)
class TrainerAdmin(UserAdmin):

    list_display = [
        'nickname',
        'faction',
        'is_banned',
        'leaderboard_eligibility',
        ]
    list_filter = [
        'faction',
        'is_banned',
        'is_active',
        'is_verified',
        ]
    search_fields = [
        'nicknames__nickname',
        'first_name',
        'username',
        ]
    readonly_fields = [
        'old_id',
        'last_login',
        'date_joined',
        'last_modified',
        ]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Authentication'), {'fields': ('username', 'password', 'email', 'old_id')}),
        (_('Trainer info'), {'fields': ('first_name', 'last_name', 'faction', 'country')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_banned', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('start_date', 'last_login', 'date_joined', 'last_modified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'faction', 'country', 'start_date'),
        })
    )
    
    inlines = [
        TargetInline,
        TrainerCodeInline,
    ]
    
    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ['username']
        return self.readonly_fields
    
    def get_queryset(self, request) -> TrainerQuerySet:
        return super().get_queryset(request).prefetch_related('targets').prefetch_related('trainer_code')


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
