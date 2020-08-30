import django.contrib.postgres.fields
from django.contrib.auth.models import AbstractUser as ABS
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from django_countries.fields import CountryField
from django_lifecycle import LifecycleModelMixin, hook

from trainerdex.validators import PokemonGoUsernameValidator


class AbstractUser(LifecycleModelMixin, ABS):
    """The model used to represent a user in the database"""

    username = django.contrib.postgres.fields.CICharField(
        verbose_name=pgettext_lazy("nickname__title", "nickname"),
        max_length=15,
        unique=True,
        help_text=_(
            "Required. 3-15 characters. Letters and digits only. Must match Pokemon Go Nickname."
        ),
        validators=[PokemonGoUsernameValidator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    last_modified = models.DateTimeField(_("last modified"), auto_now=True)

    country = CountryField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("profile__country__title", "country"),
        help_text=pgettext_lazy(
            "profile__country__help",
            "Where this account plays the most. Used to place in localized leaderboards",
        ),
    )

    is_banned = models.BooleanField(
        default=False,
        verbose_name=pgettext_lazy("profile__banned__title", "banned"),
        help_text=pgettext_lazy(
            "profile__banned__help",
            "Designates whether this user should be treated as banned. Select this instead of deleting accounts.",
        ),
    )

    @hook("after_update", when="username", has_changed=True)
    def email_user_about_name_change(self) -> None:
        # TODO: Actually email the user
        pass

    @hook("before_save", when="is_banned", is_now=True)
    def deactivate_banned_user(self) -> None:
        self.is_active = False

    @hook("after_save", when="is_banned", was=False, is_now=True)
    def alert_banned_user(self) -> None:
        # TODO: Email the user alerting them they've been banned!
        pass

    class Meta(ABS.Meta):
        abstract = True
