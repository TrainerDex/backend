# import json

from django.contrib import admin

# from django.utils.safestring import mark_safe
# from django.utils.translation import gettext_lazy as _

from allauth.socialaccount.admin import SocialAccountAdmin as BaseSocialAccountAdmin
from allauth.socialaccount.models import SocialAccount

# from pygments import highlight
# from pygments.formatters import HtmlFormatter
# from pygments.lexers import JsonLexer

# from core.models import DiscordGuild, DiscordGuildMembership, DiscordGuildSettings, DiscordUser

admin.site.unregister(SocialAccount)


@admin.register(SocialAccount)
class SocialAccountAdmin(BaseSocialAccountAdmin):
    search_fields = ["user", "uid"]


# class DiscordSettingsInline(admin.StackedInline):
#     model = DiscordGuildSettings
#     fieldsets = (
#         ('Localization', {'fields': ('language', 'timezone',)}),
#         ('Welcomer', {'fields': ('renamer', 'renamer_with_level', 'renamer_with_level_format',)}),
#         ('TrainerDex', {'fields': ('welcomer', 'welcomer_message_new', 'welcomer_message_existing', 'welcomer_channel', 'monthly_gains_channel',)}),
#         )
#     verbose_name = _("Discord Server Settings")
#     verbose_name_plural = _("Discord Server Settings")
#     can_delete = False
#
# class JSONAdmin(admin.ModelAdmin):
#
#     def data_prettified(self, instance):
#         """Function to display pretty version of our data"""
#
#         # Convert the data to sorted, indented JSON
#         response = json.dumps(instance.data, sort_keys=True, indent=2)
#
#         # Get the Pygments formatter
#         formatter = HtmlFormatter(style='colorful')
#
#         # Highlight the data
#         response = highlight(response, JsonLexer(), formatter)
#
#         # Get the stylesheet
#         style = "<style>" + formatter.get_style_defs() + "</style><br>"
#
#         # Safe the output
#         return mark_safe(style + response)
#     data_prettified.short_description = 'data'
#
# @admin.register(DiscordGuild)
# class DiscordGuildAdmin(JSONAdmin):
#     fieldsets = (
#         (None, {'fields': ('id', 'name', 'owner')}),
#         ('Debug', {'fields': ('data_prettified', 'cached_date'), 'classes': ('collapse',)}),
#         )
#     inlines = [DiscordSettingsInline]
#     search_fields = ('id', 'data__name')
#     list_display = ('name', 'id', '_outdated', 'has_data', 'has_access', 'owner', 'cached_date')
#
#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return ('id', 'name', 'owner', 'data_prettified', 'cached_date')
#         else:
#             return ('name', 'owner', 'data_prettified', 'cached_date')
#
#
# @admin.register(DiscordUser)
# class DiscordUserAdmin(JSONAdmin):
#     fields = ('user', 'uid', 'last_login', 'date_joined', 'data_prettified')
#     search_fields = ('user__username', 'uid')
#     list_display = ('__str__', 'uid', 'last_login', 'date_joined', 'user')
#     readonly_fields = ('uid', 'last_login', 'date_joined', 'data_prettified')
#
# @admin.register(DiscordGuildMembership)
# class DiscordGuildMembershipAdmin(JSONAdmin):
#     fields = ('guild', 'user', 'data_prettified', 'cached_date', 'active', 'nick_override')
#     autocomplete_fields = ['guild', 'user']
#     search_fields = ('guild__data__name', 'guild__id', 'user__user__username', 'user__user__trainer__nickname__nickname', 'data__nick', 'data__user__username')
#     list_display = ('user', '__str__', 'active', 'cached_date')
#     list_filter = ('guild', 'active', 'cached_date')
#
#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return ('guild', 'user', 'data_prettified', 'cached_date')
#         else:
#             return ('data_prettified', 'cached_date')