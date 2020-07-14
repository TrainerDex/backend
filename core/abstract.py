import django.contrib.postgres.fields
from django.contrib.auth.models import AbstractUser as ABS
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_lifecycle import LifecycleModelMixin, hook

from trainerdex.validators import PokemonGoUsernameValidator


class AbstractUser(LifecycleModelMixin, ABS):
    """The model used to represent a user in the database"""
    
    username = django.contrib.postgres.fields.CICharField(
        verbose_name=pgettext_lazy("nickname__title", "nickname"),
        max_length=15,
        unique=True,
        help_text=_('Required. 3-15 characters. Letters and digits only. Must match PokemonGo Nickname.'),
        validators=[PokemonGoUsernameValidator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    
    @hook('after_update', when='username', has_changed=True)
    def email_user_about_name_change(self) -> None:
        # TODO: Actually email the user
        pass
    
    class Meta(ABS.Meta):
        abstract = True
