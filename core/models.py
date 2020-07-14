# import datetime
# from typing import Dict, List, Union
# import logging
#
# import requests
# from allauth.socialaccount.models import SocialAccount
# from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.db import models
# from django.utils.translation import gettext_lazy as _, ngettext
# from django.utils import timezone
# from django_lifecycle import LifecycleModelMixin, hook
# from pytz import common_timezones
#
# log = logging.getLogger('django.trainerdex')
#
#
# class DiscordGuild(LifecycleModelMixin, models.Model):
#     id = models.BigIntegerField(
#         primary_key=True,
#         verbose_name="ID",
#     )
#     data = django.contrib.postgres.fields.JSONField(
#         null=True,
#         blank=True,
#     )
#     cached_date = models.DateTimeField(auto_now_add=True)
#     has_access = models.BooleanField(default=False)
#     members = models.ManyToManyField(
#         'DiscordUser',
#         through='DiscordGuildMembership',
#         through_fields=('guild', 'user'),
#     )
#
#     # Localization settings
#     language = models.CharField(default=settings.LANGUAGE_CODE, choices=settings.LANGUAGES, max_length=len(max(settings.LANGUAGES, key=lambda x: len(x[0]))[0]))
#     timezone = models.CharField(default=settings.TIME_ZONE, choices=((x, x) for x in common_timezones), max_length=len(max(common_timezones, key=len)))
#
#     # Needed for automatic renaming features
#     rename_users_on_join = models.BooleanField(
#         default=True,
#         verbose_name=_('Rename users when they join.'),
#         help_text=_("This setting will rename a user to their Pokémon Go username whenever they join your server and when their name changes on here."),
#     )
#     rename_users_on_update = models.BooleanField(
#         default=True,
#         verbose_name=_('Rename users when they update.'),
#         help_text=_("This setting will rename a user to their Pokémon Go username whenever they update their stats."),
#     )
#     renamer_with_level_format = models.CharField(
#         default='false',
#         verbose_name=_('Add levels to a users name'),
#         max_length=50,
#         choices=[
#             ('false' 'None'),
#             ('int', _("Plain ol' Numbers")),
#             ('circled_level', _("Circled Numbers ㊵")),
#             ],
#     )
#
#     def _outdated(self) -> bool:
#         return (timezone.now()-self.cached_date) > datetime.timedelta(hours=1)
#     _outdated.boolean = True
#     outdated = property(_outdated)
#
#     def has_data(self) -> bool:
#         return bool(self.data)
#     has_data.boolean = True
#     has_data.short_description = _('got data')
#
#     def __str__(self) -> str:
#         return self.data.get('name', self.id)
#
#     @hook('before_save')
#     def refresh_from_api(self) -> None:
#         logging.info(f"Updating DiscordGuild {self.id}")
#         try:
#             base_url = 'https://discordapp.com/api/v{version_number}'.format(version_number=6)
#             r = requests.get(f"{base_url}/guilds/{guild_id}", headers={'Authorization': f"Bot {settings.DISCORD_TOKEN}"})
#             r.raise_for_status()
#         except requests.exceptions.HTTPError:
#             log.exception("Failed to get server information from Discord")
#             self.data = {}
#             self.has_access = False
#         else:
#             self.data = r.json()
#             self.has_access = True
#         finally:
#             self.cached_date = timezone.now()
#
#     @hook('after_save')
#     @transaction.atomic
#     def sync_members(self) -> Dict[str, List[str]]:
#         try:
#             def get_guild_members(guild_id: int, limit: int = 1000) -> Dict[str, Union[str, int]]:
#                 base_url = 'https://discordapp.com/api/v{version_number}'.format(version_number=6)
#                 previous = None
#                 more = True
#                 result = []
#                 while more:
#                     r = requests.get(f"{base_url}/guilds/{guild_id}/members", headers={'Authorization': f"Bot {settings.DISCORD_TOKEN}"}, params={'limit': limit, 'after': previous})
#                     r.raise_for_status()
#                     more = bool(r.json())
#                     if more:
#                         result += r.json()
#                         previous = result[-1]['user']['id']
#                 return result
#             guild_api_members = get_guild_members(self.id)
#         except requests.exceptions.HTTPError:
#             log.exception("Failed to get server information from Discord")
#             return {'warning': ["Failed to get server information from Discord"]}
#
#         # Replace with a update_or_create() loop
#
#         active_members = []
#         created = 0
#         updated = 0
#
#         for x in guild_api_members:
#             if SocialAccount.objects.filter(provider='discord', uid=x["user"]["id"]).exists():
#                 x, y = DiscordGuildMembership.objects.update_or_create(
#                     guild=self,
#                     user=SocialAccount.objects.get(provider='discord', uid=x["user"]["id"]),
#                     defaults={
#                         'active': True,
#                         'data': x,
#                         'cached_date': timezone.now(),
#                     },
#                 )
#                 active_members.append(x)
#                 if y:
#                     created += 1
#                 else:
#                     updated += 1
#
#         inactive_members = DiscordGuildMembership.objects.filter(guild=self, active=True).exclude(user__uid__in=[x["user"]["id"] for x in guild_api_members]).update(active=False)
#
#         return {
#             'success': [
#                 ngettext(
#                     "Imported {success} of {total} valid member to {guild} ({created} added, {updated} updated)",
#                     "Imported {success} of {total} valid members to {guild} ({created} added, {updated} updated)",
#                     total,
#                 ).format(
#                     success=len(active_members),
#                     total=len(guild_api_members),
#                     guild=self,
#                     created=created,
#                     updated=updated,
#                 ),
#             ],
#             'warning': [
#                 ngettext(
#                     "{count} member left {guild}",
#                     "{count} members left {guild}",
#                     inactive_members,
#                 ).format(
#                     count=inactive_members,
#                     guild=self
#                 ),
#             ],
#         }
#
#     class Meta:
#         verbose_name = _("Discord Guild")
#         verbose_name_plural = _("Discord Guilds")
#
#
# class DiscordUserManager(models.Manager):
#     def get_queryset(self):
#         return super().get_queryset().filter(provider='discord')
#
#     def create(self, **kwargs):
#         kwargs.update({'provider': 'discord'})
#         return super().create(**kwargs)
#
#
# class DiscordUser(SocialAccount):
#     objects = DiscordUserManager()
#
#     @property
#     def username(self) -> str:
#         return self.extra_data.get('username')
#
#     @property
#     def discriminator(self) -> Union[str, int]:
#         return self.extra_data.get('discriminator')
#
#     def __str__(self) -> str:
#         if self.username and self.discriminator:
#             return f"{self.username}#{self.discriminator}"
#         else:
#             return str(self.user)
#
#     class Meta:
#         proxy = True
#         verbose_name = _("Discord User")
#         verbose_name_plural = _("Discord Users")
#
#
# class DiscordGuildMembership(models.Model):
#     guild = models.ForeignKey(
#         DiscordGuild,
#         on_delete=models.CASCADE,
#     )
#     user = models.ForeignKey(
#         DiscordUser,
#         on_delete=models.CASCADE,
#     )
#     active = models.BooleanField(
#         default=True,
#     )
#     nick_override = models.CharField(
#         null=True,
#         blank=True,
#         max_length=32,
#     )
#
#     data = django.contrib.postgres.fields.JSONField(
#         null=True,
#         blank=True,
#     )
#     cached_date = models.DateTimeField(
#         null=True,
#         blank=True,
#     )
#
#     def _outdated(self) -> bool:
#         return (timezone.now()-self.cached_date) > datetime.timedelta(days=1)
#     _outdated.boolean = True
#     outdated = property(_outdated)
#
#     def _change_nick(self, nick: str) -> None:
#         base_url = 'https://discordapp.com/api/v{version_number}'.format(version_number=6)
#         if len(nick) > 32:
#             raise ValidationError('nick too long')
#         log.info(f"Renaming {self} to {nick}")
#         r = requests.patch(f"{base_url}/guilds/{self.guild.id}/members/{self.user.uid}", headers={'Authorization': f"Bot {settings.DISCORD_TOKEN}"}, json={'nick': nick})
#         log.info(r.status_code)
#         log.info(r.text)
#         self.refresh_from_api()
#
#
#     @property
#     def nick(self) -> str:
#         return self.data.get('nick')
#
#     @property
#     def display_name(self) -> str:
#         if self.nick:
#             return self.nick
#         else:
#             return self.user
#
#     def __str__(self) -> str:
#         return f"{self.display_name} in {self.guild}"
#
#     @hook('before_save')
#     def refresh_from_api(self) -> None:
#         log.info(f"Updating {self}")
#         try:
#             base_url = 'https://discordapp.com/api/v{version_number}'.format(version_number=6)
#             r = requests.get(f"{base_url}/guilds/{self.guild.id}/members/{self.user.uid}", headers={'Authorization': f"Bot {settings.DISCORD_TOKEN}"})
#             r.raise_for_status()
#         except requests.exceptions.HTTPError:
#             log.exception("Failed to get server information from Discord")
#         else:
#             self.data = r.json()
#             if not self.user.extra_data:
#                 self.user.extra_data = self.data['user']
#                 self.user.save(update_fields=['extra_data'])
#             self.cached_date = timezone.now()
#
#     def clean(self) -> None:
#         if self.user.provider != 'discord':
#             raise ValidationError(_("{} is not of type 'discord'").format(self.user))
#
#     class Meta:
#         verbose_name = _("Discord Member")
#         verbose_name_plural = _("Discord Members")
#         unique_together = (("guild", "user"),)
