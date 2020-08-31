import datetime
import json
import logging
import uuid
import os
import re
from typing import Dict, Iterator, List, Union

import django.contrib.postgres.fields
from django.conf import settings
from django.contrib.auth.models import UserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import (
    gettext_lazy as _,
    npgettext_lazy,
    pgettext,
    pgettext_lazy,
)

import humanize
from collections import defaultdict
from decimal import Decimal
from django_lifecycle import hook, LifecycleModelMixin
from exclusivebooleanfield.fields import ExclusiveBooleanField

from trainerdex.abstract import AbstractUser
from trainerdex.fields import PogoPositiveIntegerField, PogoDecimalField
from trainerdex.validators import TrainerCodeValidator, PokemonGoUsernameValidator

log = logging.getLogger("django.trainerdex")


class Faction(models.Model):
    """
    Managed by the system, automatically created via a Django data migration
    """

    TEAMLESS = 0
    MYSTIC = 1
    VALOR = 2
    INSTINCT = 3
    FACTION_CHOICES = (
        (TEAMLESS, pgettext("faction_0__short", "Teamless")),
        (MYSTIC, pgettext("faction_1__short", "Mystic")),
        (VALOR, pgettext("faction_2__short", "Valor")),
        (INSTINCT, pgettext("faction_3__short", "Instinct")),
    )

    id = models.PositiveSmallIntegerField(
        choices=FACTION_CHOICES, primary_key=True, validators=[MaxValueValidator(3)]
    )

    @property
    def name_short(self) -> str:
        CHOICES = (
            pgettext("faction_0__short", "Teamless"),
            pgettext("faction_1__short", "Mystic"),
            pgettext("faction_2__short", "Valor"),
            pgettext("faction_3__short", "Instinct"),
        )
        return CHOICES[self.id]

    @property
    def name_long(self) -> str:
        CHOICES = (
            pgettext("faction_0__long", "No Team"),
            pgettext("faction_1__long", "Team Mystic"),
            pgettext("faction_2__long", "Team Valor"),
            pgettext("faction_3__long", "Team Instinct"),
        )
        return CHOICES[self.id]

    @property
    def avatar(self) -> str:
        return static(f"img/faction/{self.id}.png")

    def __str__(self) -> str:
        return self.name_short

    def __repr__(self) -> str:
        return self.name_long

    class Meta:
        verbose_name = npgettext_lazy("faction", "team", "teams", 1)
        verbose_name = npgettext_lazy("faction", "team", "teams", 3)


class TrainerQuerySet(models.QuerySet):
    def exclude_banned(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(is_banned=True)

    def exclude_unverified(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(is_verified=False)

    def exclude_deactived(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(is_active=False)

    def exclude_empty(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(update__isnull=True)

    def default_excludes(self: models.QuerySet) -> models.QuerySet:
        return self.exclude_banned().exclude_unverified().exclude_deactived()

    def get_leaderboard(
        self, legacy_mode: bool = False, order_by: str = "total_xp"
    ) -> models.QuerySet:
        from trainerdex.leaderboard import Leaderboard

        return Leaderboard(legacy_mode, order_by, queryset=self).objects


class TrainerManager(UserManager):
    def get_queryset(self):
        return TrainerQuerySet(self.model, using=self._db)

    def exclude_banned(self) -> models.QuerySet:
        return self.get_queryset().exclude_banned()

    def exclude_unverifired(self) -> models.QuerySet:
        return self.get_queryset().exclude_unverified()

    def exclude_deactived(self) -> models.QuerySet:
        return self.get_queryset().exclude_deactived()

    def exclude_empty(self) -> models.QuerySet:
        return self.get_queryset().exclude_empty()

    def default_excludes(self) -> models.QuerySet:
        return self.get_queryset().default_excludes()

    def get_leaderboard(
        self, legacy_mode: bool = False, order_by: str = "total_xp"
    ) -> models.QuerySet:
        return self.get_queryset().get_leaderboard()


class Trainer(AbstractUser):
    """The model used to represent a Users profile in the database"""

    tid = models.PositiveIntegerField(
        editable=False,
        verbose_name=pgettext_lazy("tid", "(Deprecated) TID"),
        help_text=pgettext_lazy(
            "tid_help",
            (
                "The Trainer ID on the old TrainerDex API."
                " This is deprecated and will be removed upon the retirement of API v1,"
                " as it's now shared with the User ID."
            ),
        ),
        blank=True,
        null=True,
    )
    start_date = models.DateField(
        null=True,
        blank=False,
        validators=[MinValueValidator(datetime.date(2016, 7, 5))],
        verbose_name=pgettext_lazy("start_date", "Start Date"),
        help_text=pgettext_lazy("start_date__help", "Creation date of the Pokémon Go profile."),
    )
    faction = models.ForeignKey(
        Faction,
        on_delete=models.PROTECT,
        verbose_name=Faction._meta.verbose_name,
        help_text=pgettext_lazy("faction__help", "The team of the Pokémon Go profile."),
        default=0,
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=pgettext_lazy("is_verified", "Verified"),
        help_text=pgettext_lazy(
            "is_verified__help",
            "Designates whether this user should be treated as verified.",
        ),
    )

    evidence = GenericRelation(
        "Evidence",
        object_id_field="object_pk",
    )

    objects = TrainerManager()

    def has_evidence_been_submitted(self) -> bool:
        return self.evidence.first().images.exists()

    def has_evidence_been_approved(self) -> bool:
        return self.evidence.first().approval

    def awaiting_verification(self) -> bool:
        return self.has_evidence_been_submitted() and not any(
            self.verified, self.has_evidence_been_approved()
        )

    @property
    def leaderboard_eligibility_detail(self) -> Dict[str, bool]:
        """Returns if a user is eligibile for the leaderboard"""
        return {
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "is_not_banned": not self.is_banned,
        }

    def leaderboard_eligibility(self) -> bool:
        return all(self.leaderboard_eligibility_detail.values())

    leaderboard_eligibility.boolean = True

    @property
    def nickname(self) -> str:
        return self.username

    @property
    def avatar(self) -> str:
        class Avatar:
            def __init__(self, url):
                self.url = url

        return Avatar(self.faction.avatar)

    def __str__(self) -> str:
        return self.username

    def __repr__(self) -> str:
        return f"pk: {self.pk} nickname: {self.username} faction: {self.faction}"

    class Meta(AbstractUser.Meta):
        verbose_name = npgettext_lazy("trainer", "trainer", "trainers", 1)
        verbose_name_plural = npgettext_lazy("trainer", "trainer", "trainers", 2)


class Nickname(LifecycleModelMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=Trainer._meta.verbose_name,
        related_name="nicknames",
    )
    nickname = django.contrib.postgres.fields.CICharField(
        max_length=15,
        unique=True,
        validators=[PokemonGoUsernameValidator],
        db_index=True,
        verbose_name=npgettext_lazy("nickname", "nickname", "nicknames", 1),
    )
    active = ExclusiveBooleanField(
        on="user",
    )

    def __str__(self) -> str:
        return self.nickname

    @hook("after_save", when="active", is_now=True)
    def on_active_set_username_on_user(self) -> None:
        self.user.username = self.nickname
        self.user.save(update_fields=["username"])

    class Meta:
        ordering = ["nickname"]
        verbose_name = npgettext_lazy("nickname", "nickname", "nicknames", 1)
        verbose_name_plural = npgettext_lazy("nickname", "nickname", "nicknames", 2)


@receiver(post_save, sender=Trainer)
def create_nickname(sender, instance: Trainer, created: bool, **kwargs) -> Nickname:
    if kwargs.get("raw"):
        return None

    if created:
        return Nickname.objects.create(user=instance, nickname=instance.username, active=True)


class TrainerCode(LifecycleModelMixin, models.Model):

    trainer = models.OneToOneField(
        Trainer,
        on_delete=models.CASCADE,
        related_name="trainer_code",
        verbose_name=Trainer._meta.verbose_name,
        primary_key=True,
    )
    code = models.CharField(
        null=True,
        blank=True,
        validators=[
            TrainerCodeValidator,
            MinLengthValidator(12),
            MaxLengthValidator(15),
        ],
        max_length=15,
        verbose_name=npgettext_lazy("trainer_code", "Trainer Code", "Trainer Codes", 1),
    )

    def __str__(self) -> str:
        return str(self.trainer)

    @hook("before_save")
    def format_code(self):
        self.code = re.sub(r"\D", "", self.code)

    class Meta:
        verbose_name = npgettext_lazy("trainer_code", "Trainer Code", "Trainer Codes", 1)
        verbose_name_plural = npgettext_lazy("trainer_code", "Trainer Code", "Trainer Codes", 2)
        permissions = [
            (
                "share_trainer_code_to_groups",
                _("Trainer Code can be seen by users of groups they're in"),
            ),
            (
                "share_trainer_code_to_web",
                _("Trainer Code can be seen on the web, publicly"),
            ),
            (
                "share_trainer_code_to_api",
                _("Trainer Code can be on the API"),
            ),
        ]


class UpdateQuerySet(models.QuerySet):
    def exclude_banned_trainers(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(trainer__is_banned=True)

    def exclude_unverified_trainers(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(trainer__is_verified=False)

    def exclude_deactived_trainers(self: models.QuerySet) -> models.QuerySet:
        return self.exclude(trainer__is_active=False)

    def default_excludes(self: models.QuerySet) -> models.QuerySet:
        return (
            self.exclude_banned_trainers()
            .exclude_unverified_trainers()
            .exclude_deactived_trainers()
        )


class Update(models.Model):
    objects = UpdateQuerySet.as_manager()

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        verbose_name=Trainer._meta.verbose_name,
        related_name="updates",
    )
    update_time = models.DateTimeField(
        default=timezone.now,
        verbose_name=pgettext_lazy("update_time", "Time Updated"),
    )
    submission_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=pgettext_lazy("submission_date", "Date Submitted"),
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=pgettext_lazy("last_modified", "Last Modified"),
    )

    comment = models.TextField(
        max_length=240,
        verbose_name=pgettext_lazy("comment", "Comment"),
        null=True,
        blank=True,
    )

    metadata = models.JSONField(
        verbose_name=pgettext("metadata", "Metadata"),
        help_text=pgettext_lazy(
            "metadata__help",
            """This is a JSON dictionary allowing for as much metadata as you please.
            However, the following attributes are expected:

            `provider`: string
            `ocr`: boolean
            `image_url`: string

            """,
        ),
        default={
            "provider": "com.trainerdex",
            "ocr": False,
            "image_url": None,
        },
    )

    total_xp = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("total_xp", "Total XP"),
        reversable=False,
        sortable=True,
        levels=[
            ("1", 0),
            ("2", 1000),
            ("3", 3000),
            ("4", 6000),
            ("5", 10000),
            ("6", 15000),
            ("7", 21000),
            ("8", 28000),
            ("9", 36000),
            ("10", 45000),
            ("11", 55000),
            ("12", 65000),
            ("13", 75000),
            ("14", 85000),
            ("15", 100000),
            ("16", 120000),
            ("17", 140000),
            ("18", 160000),
            ("19", 185000),
            ("20", 210000),
            ("21", 260000),
            ("22", 335000),
            ("23", 435000),
            ("24", 560000),
            ("25", 710000),
            ("26", 900000),
            ("27", 1100000),
            ("28", 1350000),
            ("29", 1650000),
            ("30", 2000000),
            ("31", 2500000),
            ("32", 3000000),
            ("33", 3750000),
            ("34", 4750000),
            ("35", 6000000),
            ("36", 7500000),
            ("37", 9500000),
            ("38", 12000000),
            ("39", 15000000),
            ("40", 20000000),
        ],
    )

    pokedex_total_caught = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_total_caught", "Unique Species Caught"),
        reversable=False,
        sortable=False,
        levels=[],
    )
    pokedex_total_seen = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_total_seen", "Unique Species Seen"),
        reversable=False,
        sortable=False,
        levels=[],
    )
    pokedex_gen1 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen1", "Kanto"),
        help_text=pgettext_lazy(
            "pokedex_gen1__help", "Register {0} Kanto region Pokémon in the Pokédex."
        ),
        validators=[MaxValueValidator(151)],
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 100)],
        badge_id=2,
        translation_ref="badge_pokedex_entries",
    )
    pokedex_gen2 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen2", "Johto"),
        help_text=pgettext_lazy(
            "pokedex_gen2__help",
            "Register {0} Pokémon first discovered in the Johto region to the Pokédex.",
        ),
        validators=[MaxValueValidator(100)],
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 30), (_("Gold"), 70)],
        badge_id=39,
        translation_ref="badge_pokedex_entries_gen2",
    )
    pokedex_gen3 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen3_title", "Hoenn"),
        help_text=pgettext_lazy(
            "pokedex_gen3",
            "Register {0} Pokémon first discovered in the Hoenn region to the Pokédex.",
        ),
        validators=[MaxValueValidator(134)],
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 40), (_("Gold"), 90)],
        badge_id=45,
        translation_ref="badge_pokedex_entries_gen3",
    )
    pokedex_gen4 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen4", "Sinnoh"),
        help_text=pgettext_lazy(
            "pokedex_gen4__help",
            "Register {0} Pokémon first discovered in the Sinnoh region to the Pokédex.",
        ),
        validators=[MaxValueValidator(107)],
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 30), (_("Gold"), 80)],
        badge_id=51,
        translation_ref="badge_pokedex_entries_gen4",
    )
    pokedex_gen5 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen5", "Unova"),
        help_text=pgettext_lazy(
            "pokedex_gen5__help",
            "Register {0} Pokémon first discovered in the Unova region to the Pokédex.",
        ),
        validators=[MaxValueValidator(156)],
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 100)],
        badge_id=56,
        translation_ref="badge_pokedex_entries_gen5",
    )
    pokedex_gen6 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen6", "Kalos"),
        help_text=pgettext_lazy(
            "pokedex_gen6__help",
            "Register {0} Pokémon first discovered in the Kalos region to the Pokédex.",
        ),
        validators=[MaxValueValidator(72)],
        reversable=False,
        sortable=True,
        levels=[],
        translation_ref="badge_pokedex_entries_gen6",
    )
    pokedex_gen7 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen7", "Alola"),
        help_text=pgettext_lazy(
            "pokedex_gen7__help",
            "Register {0} Pokémon first discovered in the Alola region to the Pokédex.",
        ),
        validators=[MaxValueValidator(88)],
        reversable=False,
        sortable=True,
        levels=[],
        translation_ref="badge_pokedex_entries_gen7",
    )
    pokedex_gen8 = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokedex_gen8", "Galar"),
        help_text=pgettext_lazy(
            "pokedex_gen8__help",
            "Register {0} Pokémon first discovered in the Galar region to the Pokédex.",
        ),
        validators=[MaxValueValidator(87)],
        reversable=False,
        sortable=True,
        levels=[],
        badge_id=63,
        translation_ref="badge_pokedex_entries_gen8",
    )

    # Medals
    travel_km = PogoDecimalField(
        max_digits=16,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="{title} ({alt})".format(
            title=pgettext_lazy("travel_km", "Jogger"),
            alt=pgettext_lazy("travel_km__alt", "Distance Walked"),
        ),
        help_text=pgettext_lazy("travel_km__help", "Walk {0} km"),
        reversable=False,
        sortable=True,
        levels=[
            (_("Bronze"), Decimal("10")),
            (_("Silver"), Decimal("100")),
            (_("Gold"), Decimal("1000")),
        ],
        badge_id=1,
        translation_ref="badge_travel_km",
    )
    capture_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="{title} ({alt})".format(
            title=pgettext_lazy("capture_total", "Collector"),
            alt=pgettext_lazy("capture_total__alt", "Pokémon Caught"),
        ),
        help_text=pgettext_lazy("capture_total__help", "Catch {0} Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 30), (_("Silver"), 500), (_("Gold"), 2000)],
        badge_id=3,
        translation_ref="badge_capture_total",
    )
    evolved_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("evolved_total", "Scientist"),
        help_text=pgettext_lazy("evolved_total__help", "Evolve {0} Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 20), (_("Gold"), 200)],
        badge_id=5,
        translation_ref="badge_evolved_total",
    )
    hatched_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("hatched_total", "Breeder"),
        help_text=pgettext_lazy("hatched_total__help", "Hatch {0} eggs."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 500)],
        badge_id=6,
        translation_ref="badge_hatched_total",
    )
    pokestops_visited = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="{title} ({alt})".format(
            title=pgettext_lazy("pokestops_visited", "Backpacker"),
            alt=pgettext_lazy("pokestops_visited__alt", "PokéStops Visited"),
        ),
        help_text=pgettext_lazy("pokestops_visited__help", "Visit {0} PokéStops."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 100), (_("Silver"), 1000), (_("Gold"), 2000)],
        badge_id=8,
        translation_ref="badge_pokestops_visited",
    )
    big_magikarp = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("big_magikarp", "Fisher"),
        help_text=pgettext_lazy("big_magikarp__help", "Catch {0} big Magikarp."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 50), (_("Gold"), 300)],
        badge_id=11,
        translation_ref="badge_big_magikarp",
    )
    battle_attack_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("battle_attack_won", "Battle Girl"),
        help_text=pgettext_lazy("battle_attack_won__help", "Win {0} Gym battles."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=13,
        translation_ref="badge_battle_attack_won",
    )
    battle_training_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("battle_training_won", "Ace Trainer"),
        help_text=pgettext_lazy("battle_training_won__help", "Train {0} times."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=14,
        translation_ref="badge_battle_training_won",
    )
    small_rattata = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("small_rattata", "Youngster"),
        help_text=pgettext_lazy("small_rattata__help", "Catch {0} tiny Rattata."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 50), (_("Gold"), 300)],
        badge_id=36,
        translation_ref="badge_small_rattata",
    )
    pikachu = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pikachu", "Pikachu Fan"),
        help_text=pgettext_lazy("pikachu__help", "Catch {0} Pikachu."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 50), (_("Gold"), 300)],
        badge_id=37,
        translation_ref="badge_pikachu",
    )
    unown = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("unown", "Unown"),
        help_text=pgettext_lazy("unown__help", "Catch {0} Unown."),
        validators=[MaxValueValidator(28)],
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 10), (_("Gold"), 26)],
        badge_id=38,
        translation_ref="badge_unown",
    )
    raid_battle_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("raid_battle_won", "Champion"),
        help_text=pgettext_lazy("raid_battle_won__help", "Win {0} Raids."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=40,
        translation_ref="badge_raid_battle_won",
    )
    legendary_battle_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("legendary_battle_won", "Battle Legend"),
        help_text=pgettext_lazy("legendary_battle_won__help", "Win {0} Legendary Raids."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=41,
        translation_ref="badge_legendary_battle_won",
    )
    berries_fed = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("berries_fed", "Berry Master"),
        help_text=pgettext_lazy("berries_fed__help", "Feed {0} Berries at Gyms."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=42,
        translation_ref="badge_berries_fed",
    )
    hours_defended = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("hours_defended", "Gym Leader"),
        help_text=pgettext_lazy("hours_defended__help", "Defend Gyms for {0} hours."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=43,
        translation_ref="badge_hours_defended",
    )
    challenge_quests = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("challenge_quests", "Pokémon Ranger"),
        help_text=pgettext_lazy("challenge_quests__help", "Complete {0} Field Research tasks."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=46,
        translation_ref="badge_challenge_quests",
    )
    max_level_friends = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("max_level_friends", "Idol"),
        help_text=pgettext_lazy(
            "max_level_friends__help", "Become Best Friends with {0} Trainers."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 1), (_("Silver"), 2), (_("Gold"), 3)],
        badge_id=48,
        translation_ref="badge_max_level_friends",
    )
    trading = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("trading", "Gentleman"),
        help_text=pgettext_lazy("trading__help", "Trade {0} Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=49,
        translation_ref="badge_trading",
    )
    trading_distance = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("trading_distance", "Pilot"),
        help_text=pgettext_lazy(
            "trading_distance__help", "Earn {0} km across the distance of all Pokémon trades."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 1000), (_("Silver"), 10000), (_("Gold"), 1000000)],
        badge_id=50,
        translation_ref="badge_trading",
    )
    great_league = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("great_league", "Great League Veteran"),
        help_text=pgettext_lazy(
            "great_league__help", "Win {} Trainer Battles in the Great League."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 200)],
        badge_id=52,
        translation_ref="badge_great_league",
    )
    ultra_league = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("ultra_league", "Ultra League Veteran"),
        help_text=pgettext_lazy(
            "ultra_league__help", "Win {} Trainer Battles in the Ultra League."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 200)],
        badge_id=53,
        translation_ref="badge_ultra_league",
    )
    master_league = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("master_league", "Master League Veteran"),
        help_text=pgettext_lazy(
            "master_league__help", "Win {} Trainer Battles in the Master League."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 200)],
        badge_id=54,
        translation_ref="badge_master_league",
    )
    photobomb = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("photobomb", "Cameraman"),
        help_text=pgettext_lazy("photobomb__help", "Have {0} surprise encounters in AR Snapshot."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 50), (_("Gold"), 200)],
        badge_id=55,
        translation_ref="badge_photobomb",
    )
    pokemon_purified = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokemon_purified", "Purifier"),
        help_text=pgettext_lazy("pokemon_purified__help", "Purify {0} Shadow Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 500)],
        badge_id=57,
        translation_ref="badge_pokemon_purified",
    )
    rocket_grunts_defeated = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("rocket_grunts_defeated", "Hero"),
        help_text=pgettext_lazy(
            "rocket_grunts_defeated__help", "Defeat {0} Team GO Rocket Grunts."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=58,
        translation_ref="badge_rocket_grunts_defeated",
    )
    rocket_giovanni_defeated = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("rocket_giovanni_defeated", "Ulta Hero"),
        help_text=pgettext_lazy(
            "rocket_giovanni_defeated__help", "Defeat the Team GO Rocket Boss {0} times."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 1), (_("Silver"), 5), (_("Gold"), 20)],
        badge_id=59,
        translation_ref="badge_rocket_giovanni_defeated",
    )
    buddy_best = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("buddy_best", "Best Buddy"),
        help_text=pgettext_lazy("buddy_best__help", "Have {0} Best Buddies."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 1), (_("Silver"), 10), (_("Gold"), 100)],
        badge_id=60,
        translation_ref="badge_buddy_best",
    )
    wayfarer = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("wayfarer", "Wayfarer"),
        help_text=pgettext_lazy("wayfarer__help", "Earn {0} Wayfarer Agreements"),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 50), (_("Silver"), 500), (_("Gold"), 1000)],
        badge_id=68,
        translation_ref="badge_wayfarer",
    )
    total_mega_evos = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("total_mega_evos", "Successor"),
        help_text=pgettext_lazy("total_mega_evos__help", "Mega Evolve a Pokémon {0} times."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 50), (_("Gold"), 500)],
        badge_id=69,
        translation_ref="badge_total_mega_evos",
    )
    unique_mega_evos = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("unique_mega_evos", "Wayfarer"),
        help_text=pgettext_lazy(
            "unique_mega_evos__help", "Mega Evolve {0} different species of Pokémon."
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 1), (_("Silver"), 24), (_("Gold"), 36)],
        badge_id=70,
        translation_ref="badge_unique_mega_evos",
    )

    type_normal = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_normal", "Schoolkid"),
        help_text=pgettext_lazy("type_normal__help", "Catch {0} Normal-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=18,
        translation_ref="badge_type_normal",
    )
    type_fighting = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_fighting", "Black Belt"),
        help_text=pgettext_lazy("type_fighting__help", "Catch {0} Fighting-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=19,
        translation_ref="badge_type_fighting",
    )
    type_flying = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_flying", "Bird Keeper"),
        help_text=pgettext_lazy("type_flying__help", "Catch {0} Flying-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=20,
        translation_ref="badge_type_flying",
    )
    type_poison = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_poison", "Punk Girl"),
        help_text=pgettext_lazy("type_poison__help", "Catch {0} Poison-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=21,
        translation_ref="badge_type_poison",
    )
    type_ground = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_ground", "Ruin Maniac"),
        help_text=pgettext_lazy("type_ground__help", "Catch {0} Ground-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=22,
        translation_ref="badge_type_ground",
    )
    type_rock = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_rock", "Hiker"),
        help_text=pgettext_lazy("type_rock__help", "Catch {0} Rock-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=23,
        translation_ref="badge_type_rock",
    )
    type_bug = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_bug", "Bug Catcher"),
        help_text=pgettext_lazy("type_bug__help", "Catch {0} Bug-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=24,
        translation_ref="badge_type_bug",
    )
    type_ghost = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_ghost", "Hex Maniac"),
        help_text=pgettext_lazy("type_ghost__help", "Catch {0} Ghost-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=25,
        translation_ref="badge_type_ghost",
    )
    type_steel = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_steel", "Depot Agent"),
        help_text=pgettext_lazy("type_steel__help", "Catch {0} Steel-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=26,
        translation_ref="badge_type_steel",
    )
    type_fire = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_fire", "Kindler"),
        help_text=pgettext_lazy("type_fire__help", "Catch {0} Fire-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=27,
        translation_ref="badge_type_fire",
    )
    type_water = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_water", "Swimmer"),
        help_text=pgettext_lazy("type_water__help", "Catch {0} Water-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=28,
        translation_ref="badge_type_water",
    )
    type_grass = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_grass", "Gardener"),
        help_text=pgettext_lazy("type_grass__help", "Catch {0} Grass-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=29,
        translation_ref="badge_type_grass",
    )
    type_electric = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_electric", "Rocker"),
        help_text=pgettext_lazy("type_electric__help", "Catch {0} Electric-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=30,
        translation_ref="badge_type_electric",
    )
    type_psychic = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_psychic", "Psychic"),
        help_text=pgettext_lazy("type_psychic__help", "Catch {0} Pychic-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=31,
        translation_ref="badge_type_psychic",
    )
    type_ice = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_ice", "Skier"),
        help_text=pgettext_lazy("type_ice__help", "Catch {0} Ice-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=32,
        translation_ref="badge_type_ice",
    )
    type_dragon = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_dragon", "Dragon Tamer"),
        help_text=pgettext_lazy("type_dragon__help", "Catch {0} Dragon-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=33,
        translation_ref="badge_type_dragon",
    )
    type_dark = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_dark", "Delinquent"),
        help_text=pgettext_lazy("type_dark__help", "Catch {0} Dark-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=34,
        translation_ref="badge_type_dark",
    )
    type_fairy = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("type_fairy", "Fairy Tale Girl"),
        help_text=pgettext_lazy("type_fairy__help", "Catch {0} Fairy-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=35,
        translation_ref="badge_type_fairy",
    )

    gymbadges_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("gymbadges_total", "Gym Badges"),
        reversable=True,
        sortable=False,
        translation_ref="profile_category_gymbadges",
    )
    gymbadges_gold = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("gymbadges_gold", "Gold Gym Badges"),
        reversable=True,
        sortable=False,
    )
    stardust = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("stardust", "Stardust"),
        reversable=True,
        sortable=False,
        translation_ref="pokemon_info_stardust_label",
    )

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.__repr__()})"

    def __repr__(self) -> str:
        return f"trainer: {self.trainer} update_time: {self.update_time}"

    def has_modified_extra_fields(self) -> bool:
        return bool(list(self.modified_extra_fields()))

    has_modified_extra_fields.boolean = True

    @classmethod
    def field_metadata(
        self, reversable: bool = None, sortable: bool = None
    ) -> Dict[str, Union[Dict[str, Union[int, float, Decimal]], bool]]:
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data/update_fields_metadata.json",
            ),
            "r",
        ) as file:
            metadata = json.load(file)

        if reversable is not None:
            metadata = {k: v for k, v in metadata.items() if v.get("reversable") == reversable}

        if sortable is not None:
            metadata = {k: v for k, v in metadata.items() if v.get("sortable") == sortable}

        return metadata

    def modified_fields(self) -> Iterator[str]:
        fields = list(self.field_metadata().keys())

        for x in fields:
            if getattr(self, x):
                yield x

    def modified_extra_fields(self) -> Iterator[str]:
        for x in self.modified_fields():
            if x != "total_xp":
                yield x

    def clean(self) -> None:
        super().clean()
        errors = defaultdict(list)

        if not any([(getattr(self, x) is not None) for x in Update.field_metadata().keys()]):
            csv_fields = ", ".join(
                [
                    str(x.verbose_name)
                    for x in Update._meta.get_fields()
                    if x.name in Update.field_metadata().keys()
                ]
            )
            raise ValidationError(
                _("You must fill in at least one of the following fields:\n{csv_fields}").format(
                    csv_fields=csv_fields
                ),
                code="nodata",
            )

        for field in Update._meta.get_fields():
            if getattr(self, field.name) is None:
                continue

            # Get latest update with that field present, only get the important fields.
            last_update = (
                self.trainer.updates.filter(update_time__lt=self.update_time)
                .exclude(uuid=self.uuid)
                .exclude(**{field.name: None})
                .order_by("-update_time")
                .only(field.name, "update_time")
                .first()
            )

            # Overall Rules

            # Value must be higher than or equal to than previous value
            if last_update is not None and field.name in Update.field_metadata(reversable=False):
                if getattr(self, field.name) < getattr(last_update, field.name):
                    errors[field.name].append(
                        ValidationError(
                            _(
                                (
                                    "This value has previously been entered at a higher value."
                                    " Please try again ensuring the value you entered was correct."
                                )
                            ),
                            code="insufficient",
                        ),
                    )

            # Field specific Validation

            if field.name == "gymbadges_gold":

                # Max Value = 1000, unless total is at 1000

                max_gymbadges_visible = 1000
                gold = getattr(self, field.name)
                total = getattr(self, "gymbadges_total")

                # Check if gymbadges_total is filled in
                if total is None:
                    errors["gymbadges_total"].append(
                        ValidationError(
                            _("This is required since you provided data for {badge}.").format(
                                badge=field.verbose_name
                            ),
                            code="required",
                        ),
                    )
                elif total < max_gymbadges_visible and gold > total:
                    errors[field.name].append(
                        ValidationError(
                            _("Stat too high. Must be less than {badge}.").format(
                                badge=Update._meta.get_field("gymbadges_total").verbose_name
                            ),
                            code="excessive",
                        ),
                    )

            if field.name == "trading_distance":

                trading = getattr(self, "trading")

                # Check if trading is filled in
                if trading is None:
                    errors["trading"].append(
                        ValidationError(
                            _("This is required since you provided data for {badge}.").format(
                                badge=field.verbose_name
                            ),
                            code="required",
                        ),
                    )

        if errors:
            raise ValidationError(errors)

    def check_values(self, raise_: bool = False) -> Dict[str, List[ValidationError]]:
        """Checks values for anything ary

        Parameters
        ----------
        raise_: bool
            If True, will raise an error instead of returning the list of warnings.
            Useful for returning to forms.

        Exceptions
        ----------
        ValidationError: raised is raise_ is True

        Returns
        -------
        List of exceptions of raise_ False else None
        """

        warnings = defaultdict(list)

        if self.trainer.start_date:
            start_date = self.trainer.start_date
        else:
            start_date = datetime.date(2016, 7, 5)

        config = {
            "total_xp": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 10000000,
            },
            "travel_km": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": Decimal("60.0"),
            },
            "capture_total": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 800,
            },
            "evolved_total": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 250,
            },
            "hatched_total": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 60,
            },
            "pokestops_visited": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 500,
            },
            "big_magikarp": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 25,
            },
            "battle_attack_won": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 500,
            },
            "battle_training_won": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2018, 12, 13)),
                    datetime.time.min,
                ),
                "DailyLimit": 100,
            },
            "small_rattata": {
                "InterestDate": datetime.datetime.combine(
                    start_date,
                    datetime.time.min,
                ),
                "DailyLimit": 25,
            },
            "berries_fed": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2017, 6, 22)),
                    datetime.time.min,
                ),
                "DailyLimit": 100,
            },
            "hours_defended": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2017, 6, 22)),
                    datetime.time.min,
                ),
                "DailyLimit": 480,
            },
            "raid_battle_won": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2017, 6, 26)),
                    datetime.time.min,
                ),
                "DailyLimit": 100,
            },
            "legendary_battle_won": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2017, 7, 22)),
                    datetime.time.min,
                ),
                "DailyLimit": 100,
            },
            "challenge_quests": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2018, 3, 30)),
                    datetime.time.min,
                ),
                "DailyLimit": 500,
            },
            "trading": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2018, 6, 21)),
                    datetime.time.min,
                ),
                "DailyLimit": 100,
            },
            "trading_distance": {
                "InterestDate": datetime.datetime.combine(
                    max(start_date, datetime.date(2018, 6, 21)),
                    datetime.time.min,
                ),
                "DailyLimit": 1001800,  # (earth_circumference/2) * trading.DailyLimit
            },
        }

        for field in Update._meta.get_fields():
            if getattr(self, field.name) is None:
                continue  # Nothing to check!

            # Get latest update with that field present, only get the important fields.
            last_update = (
                self.trainer.updates.filter(update_time__lt=self.update_time)
                .exclude(uuid=self.uuid)
                .exclude(**{field.name: None})
                .order_by("-update_time")
                .only(field.name, "update_time")
                .first()
            )

            if config.get(field.name):
                if config.get(field.name).get("InterestDate") and config.get(field.name).get(
                    "DailyLimit"
                ):
                    rate_limits = [
                        {
                            "stat": 0,
                            "datetime": config.get(field.name).get("InterestDate"),
                        },
                    ]
                    if last_update:
                        rate_limits.append(
                            {
                                "stat": getattr(last_update, field.name),
                                "datetime": getattr(last_update, "update_time"),
                            }
                        )

                    for x in rate_limits:
                        stat_delta = getattr(self, field.name) - x["stat"]
                        delta = getattr(self, "update_time") - x["datetime"]
                        rate = stat_delta / (delta.total_seconds() / 86400)
                        DailyLimit = config.get(field.name).get("DailyLimit")
                        if rate >= DailyLimit:
                            warnings[field.name].append(
                                ValidationError(
                                    _(
                                        (
                                            "This value is high."
                                            " Your daily average is above the threshold of {threshold:,}."
                                            " Please check you haven't made a mistake."
                                            "\n\n"
                                            "Your daily average between {earlier_date} and {later_date} is {average:,}"
                                        )
                                    ).format(
                                        threshold=DailyLimit,
                                        average=rate,
                                        earlier_date=x["datetime"],
                                        later_date=getattr(self, "update_time"),
                                    ),
                                    code="excessive",
                                ),
                            )

            if field.name == "gymbadges_gold":

                _xcompare = getattr(self, "gymbadges_total")
                # Check if gymbadges_total is filled in
                if _xcompare:
                    # GoldGyms < GymsSeen
                    # Check if gymbadges_gold is more of less than gymbadges_total
                    if getattr(self, field.name) > _xcompare:
                        warnings[field.name].append(
                            ValidationError(
                                _(
                                    (
                                        "The {badge} you entered is too high."
                                        " Please check for typos and other mistakes."
                                        " You can't have more gold gyms than gyms in Total."
                                        " {value:,}/{expected:,}"
                                    )
                                ).format(
                                    badge=field.verbose_name,
                                    value=getattr(self, field.name),
                                    expected=_xcompare,
                                )
                            )
                        )
                else:
                    warnings[field.name].append(
                        ValidationError(
                            _("You must fill in {other_badge} if filling in {this_badge}.").format(
                                this_badge=field.verbose_name,
                                other_badge=Update._meta.get_field("gymbadges_total").verbose_name,
                            )
                        )
                    )

            if field.name == "trading_distance":

                trading = getattr(self, "trading")
                earth_circumference = 20037.5085
                max_distance = int(earth_circumference / 2)
                rate = getattr(self, field.name) / _xcompare

                # Check if trading is filled in
                if trading:
                    # Pilot / Gentleman < Half Earth
                    if rate >= max_distance:
                        warnings[field.name].append(
                            ValidationError(
                                _(
                                    (
                                        "This value is high."
                                        " Your distance per trade average is above the threshold of {threshold:,}/trade."
                                        " Please check you haven't made a mistake."
                                        "\n\n"
                                        "Your average is {average:,}/trade"
                                    )
                                ).format(
                                    threshold=max_distance,
                                    average=rate,
                                ),
                                code="excessive",
                            ),
                        )
                else:
                    warnings[field.name].append(
                        ValidationError(
                            _("You must fill in {other_badge} if filling in {this_badge}.").format(
                                this_badge=field.verbose_name,
                                other_badge=Update._meta.get_field("trading").verbose_name,
                            )
                        )
                    )

        if raise_ and warnings:
            ValidationError(warnings)
        elif not raise_:
            return warnings

    class Meta:
        get_latest_by = "update_time"
        ordering = ["-update_time"]
        verbose_name = npgettext_lazy("update", "update", "updates", 1)
        verbose_name_plural = npgettext_lazy("update", "update", "updates", 2)


class Evidence(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=Q(app_label="trainerdex", model__in=["trainer", "update"]),
        verbose_name="model",
    )
    object_pk = models.CharField(max_length=36)
    content_object = GenericForeignKey("content_type", "object_pk")
    content_field = models.CharField(
        max_length=max(
            len("update.") + len(max(Update.field_metadata().keys(), key=len)),
            len("trainer.profile"),
        ),
        choices=[
            ("trainer.profile", Trainer._meta.verbose_name.title()),
        ]
        + [
            (
                f"update.{f.name}",
                f"{Update._meta.verbose_name.title()}.{f.verbose_name}",
            )
            for f in Update._meta.fields
            if f.name in Update.field_metadata()
        ],
    )

    approval = models.BooleanField(
        default=False,
    )

    @property
    def trainer(self) -> Trainer:
        if isinstance(self.content_object, Trainer):
            return self.content_object
        elif isinstance(self.content_object, Update):
            return self.content_object.trainer
        return None

    def __str__(self) -> str:
        return _("Evidence for {evidence_type} and {trainer}").format(
            evidence_type=self.content_field, trainer=self.trainer
        )

    def clean(self) -> None:
        # Checking the content_field is a valid field in the model for content_type
        print(self.content_field, self.content_type.model)
        if self.content_field.split(".")[0] != self.content_type.model:
            raise ValidationError(
                {"content_field": _("Content Field doesn't match Content Object")}
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_pk", "content_field"],
                name="unique_request",
            ),
        ]
        verbose_name = npgettext_lazy("evidence", "evidence", "evidence", 1)
        verbose_name_plural = npgettext_lazy("evidence", "evidence", "evidence", 2)


@receiver(post_save, sender=Trainer)
def create_evidence(sender, instance: Trainer, created: bool, **kwargs) -> Evidence:
    if kwargs.get("raw"):
        return None

    if created:
        evidence, new = Evidence.objects.get_or_create(
            content_type=ContentType.objects.get(app_label="trainerdex", model="trainer"),
            object_pk=instance.pk,
            content_field="trainer.profile",
        )
        return evidence


class EvidenceImage(models.Model):
    evidence = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=Evidence._meta.verbose_name,
    )
    image = models.ImageField(
        width_field="width",
        height_field="height",
        blank=False,
    )


class BaseTarget(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("name"))
    stat = models.CharField(
        max_length=len(max(Update.field_metadata().keys(), key=len)),
        choices=[
            (f.name, f.verbose_name)
            for f in Update._meta.fields
            if f.name in Update.field_metadata()
            and not Update.field_metadata().get(f.name).get("reversable")
        ],
        verbose_name=pgettext("stat", "stat"),
    )
    _target = models.CharField(
        max_length=max(10, Update._meta.get_field("travel_km").max_digits),
        verbose_name=npgettext_lazy("target", "target", "targets", 1),
    )

    def target() -> Dict:
        def fget(self) -> Union[int, Decimal]:
            return Update._meta.get_field(self.stat).to_python(self._target)

        def fset(self, value: Union[int, Decimal]) -> str:
            value = Update._meta.get_field(self.stat).get_prep_value(value)
            self._target = str(value)

        def fdel(self) -> None:
            pass

        return locals()

    target = property(**target())

    @property
    def unit(self):
        return Update.field_metadata().get(self.stat).get("unit", "")

    def __target_str_(self) -> str:
        return f"{self.target:0,}{self.unit}"

    __target_str_.short_description = _target.verbose_name

    target_str = property(__target_str_)

    def __str__(self) -> str:
        return f"{self.name} ({self.stat}: {humanize.intcomma(self.target)})"

    def clean(self) -> None:
        self.target = self._target

    class Meta:
        abstract = True
        verbose_name = npgettext_lazy("target", "target", "targets", 1)
        verbose_name_plural = npgettext_lazy("target", "target", "targets", 2)
        ordering = ["stat", "_target"]


class Target(LifecycleModelMixin, BaseTarget):
    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        verbose_name=Trainer._meta.verbose_name,
        related_name="targets",
    )
    has_reached = models.BooleanField(
        default=False,
        verbose_name=pgettext_lazy("has_reached", "reached"),
        help_text=pgettext_lazy(
            "has_reached__help",
            "Designates whether this target has been reached.",
        ),
    )
    date_reached = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=pgettext_lazy("date_reached__name", "date reached"),
        help_text=pgettext_lazy(
            "date_reached__help", "The date the target was reached, if known."
        ),
    )

    @hook("before_create")
    def check_reached(self):
        qs = (
            self.trainer.updates.annotate(value=F(self.stat))
            .exclude(value__isnull=True)
            .exclude(value__lt=self.target)
            .order_by("value")
        )

        log.debug(f"Checking {self.stat} @ {self.target}\n{qs}")
        if qs.exists():
            log.debug(f"{qs.first().value} >= {self.target}: {qs.first().value >= self.target}")

        if qs.exists() and qs.first().value >= self.target:
            self.has_reached = True
            self.date_reached = qs.first().update_time
        else:
            self.has_reached = False
            self.date_reached = None

    def __str__(self) -> str:
        return f"{'✅' if self.has_reached else '❌'} {super().__str__()}"

    class Meta(BaseTarget.Meta):
        constraints = [
            models.UniqueConstraint(fields=["stat", "_target", "trainer"], name="unique_target"),
        ]


class PresetTarget(BaseTarget):
    name = models.CharField(max_length=200, null=False, blank=False)
    group = models.ForeignKey(
        "PresetTargetGroup",
        on_delete=models.CASCADE,
        related_name="targets",
    )

    def add_to_trainer(self, trainer: Trainer) -> List[Union[Target, bool]]:
        return Target.objects.update_or_create(
            trainer=trainer,
            stat=self.stat,
            _target=self._target,
            defaults={"name": self.name},
        )

    class Meta(BaseTarget.Meta):
        verbose_name = BaseTarget.Meta.verbose_name + " (Preset)"
        verbose_name_plural = BaseTarget.Meta.verbose_name_plural + " (Preset)"
        ordering = None
        order_with_respect_to = "group"


class PresetTargetGroup(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=200)

    def add_to_trainer(self, trainer: Trainer) -> List[List[Union[Target, bool]]]:
        return [x.add_to_trainer(trainer) for x in self.targets.all()]

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = npgettext_lazy("target", "target group", "target groups", 1)
        verbose_name_plural = npgettext_lazy("target", "target group", "target groups", 2)
