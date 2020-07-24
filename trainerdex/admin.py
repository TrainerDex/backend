from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from core.mixins import AddFieldsetsMixin
from trainerdex.models import (
    DataSource,
    Evidence,
    EvidenceImage,
    Nickname,
    PresetTarget,
    PresetTargetGroup,
    Target,
    Trainer,
    TrainerCode,
    Update,
)
from trainerdex.models import TrainerQuerySet

admin.site.register(PresetTargetGroup)
admin.site.register(DataSource)


@admin.register(Nickname)
class NicknameAdmin(admin.ModelAdmin):
    search_fields = [
        "nickname",
        "user__username",
    ]
    list_display = [
        "nickname",
        "user",
        "active",
    ]
    list_filter = ["active"]
    list_display_links = ["nickname"]


@admin.register(PresetTarget)
class PresetTargetAdmin(admin.ModelAdmin):

    list_display = ["stat", "name", "target_str"]
    list_filter = ["stat"]
    search_fields = ["stat", "name"]


def force_check_target(modeladmin, request, queryset):
    for x in queryset:
        x.check_reached()
        x.save(update_fields=["has_reached", "date_reached"])


force_check_target.short_description = "Check if this target has been reached"


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):

    list_display = [
        "trainer",
        "stat",
        "name",
        "target_str",
        "has_reached",
        "date_reached",
    ]
    list_filter = ["stat", "has_reached"]
    search_fields = [
        "trainer__nicknames__nickname",
        "trainer__username",
        "stat",
        "name",
    ]
    actions = [force_check_target]


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):

    autocomplete_fields = ["trainer"]
    list_display = [
        "trainer",
        "total_xp",
        "update_time",
        "submission_date",
        "has_modified_extra_fields",
    ]
    search_fields = ["trainer__nicknames__nickname", "trainer__username"]
    ordering = ["-update_time"]
    date_hierarchy = "update_time"
    readonly_fields = [
        "submission_date",
        "last_modified",
        "pokedex_gen6",
        "pokedex_gen7",
        "pokedex_gen8",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "trainer",
                    "update_time",
                    "submission_date",
                    "last_modified",
                    "gymbadges_total",
                    "gymbadges_gold",
                    "stardust",
                ]
            },
        ),
        (
            _("Basic Info"),
            {"fields": ["travel_km", "capture_total", "pokestops_visited", "total_xp"]},
        ),
        (
            _("Medals"),
            {
                "fields": [
                    "evolved_total",
                    "hatched_total",
                    "big_magikarp",
                    "battle_attack_won",
                    "battle_training_won",
                    "small_rattata",
                    "pikachu",
                    "unown",
                    "raid_battle_won",
                    "legendary_battle_won",
                    "berries_fed",
                    "hours_defended",
                    "challenge_quests",
                    "max_level_friends",
                    "trading",
                    "trading_distance",
                    "great_league",
                    "ultra_league",
                    "master_league",
                    "photobomb",
                    "pokemon_purified",
                    "rocket_grunts_defeated",
                    "buddy_best",
                    "wayfarer",
                ]
            },
        ),
        (
            _("Type Medals"),
            {
                "fields": [
                    "type_normal",
                    "type_fighting",
                    "type_flying",
                    "type_poison",
                    "type_ground",
                    "type_rock",
                    "type_bug",
                    "type_ghost",
                    "type_steel",
                    "type_fire",
                    "type_water",
                    "type_grass",
                    "type_electric",
                    "type_psychic",
                    "type_ice",
                    "type_dragon",
                    "type_dark",
                    "type_fairy",
                ]
            },
        ),
        (
            _("Pokédex"),
            {
                "fields": [
                    "pokedex_total_caught",
                    "pokedex_total_seen",
                    "pokedex_gen1",
                    "pokedex_gen2",
                    "pokedex_gen3",
                    "pokedex_gen4",
                    "pokedex_gen5",
                    "pokedex_gen6",
                    "pokedex_gen7",
                    "pokedex_gen8",
                ]
            },
        ),
    ]


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
        "nickname",
        "faction",
        "is_banned",
        "leaderboard_eligibility",
    ]
    list_filter = [
        "faction",
        "is_banned",
        "is_active",
        "is_verified",
    ]
    search_fields = [
        "nicknames__nickname",
        "first_name",
        "username",
    ]
    readonly_fields = [
        "old_id",
        "last_login",
        "date_joined",
        "last_modified",
    ]
    date_hierarchy = "start_date"
    fieldsets = [
        (_("Authentication"), {"fields": ["username", "password", "email", "old_id"]}),
        (
            _("Trainer info"),
            {"fields": ["first_name", "last_name", "faction", "country"]},
        ),
        (
            _("Permissions"),
            {
                "fields": [
                    "is_active",
                    "is_banned",
                    "is_verified",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
        (
            _("Important dates"),
            {"fields": ["start_date", "last_login", "date_joined", "last_modified"]},
        ),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "faction",
                    "country",
                    "start_date",
                ),
            },
        )
    ]
    inlines = [
        TargetInline,
        TrainerCodeInline,
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ["username"]
        return self.readonly_fields

    def get_queryset(self, request) -> TrainerQuerySet:
        return (
            super()
            .get_queryset(request)
            .prefetch_related("targets")
            .prefetch_related("trainer_code")
        )


class EvidenceImageInline(admin.TabularInline):
    model = EvidenceImage
    min_num = 0


@admin.register(Evidence)
class EvidenceAdmin(AddFieldsetsMixin, admin.ModelAdmin):

    list_display = [
        "trainer",
        "approval",
        "content_type",
        "content_field",
    ]
    list_filter = [
        "approval",
        "content_type",
        "content_field",
    ]
    readonly_fields = [
        "content_object",
    ]

    fieldsets = [
        (
            _("Object"),
            {
                "classes": ("wide",),
                "fields": ("content_object", "content_field", "approval"),
            },
        ),
    ]
    add_fieldsets = [
        (_("Object"), {"fields": ["content_type", "object_pk", "content_field",],}),
    ]
    inlines = [
        EvidenceImageInline,
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ["content_field"]
        return self.readonly_fields
