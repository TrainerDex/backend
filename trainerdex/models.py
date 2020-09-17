import datetime
import logging
import uuid
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
from trainerdex.fields import PogoDecimalField, PogoPositiveIntegerField
from trainerdex.validators import FriendCodeValidator, PokemonGoUsernameValidator

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
        (TEAMLESS, pgettext("team_name_team0_abbr", "Teamless")),
        (MYSTIC, pgettext("team_name_team1_abbr", "Mystic")),
        (VALOR, pgettext("team_name_team2_abbr", "Valor")),
        (INSTINCT, pgettext("team_name_team3_abbr", "Instinct")),
    )

    id = models.PositiveSmallIntegerField(
        choices=FACTION_CHOICES, primary_key=True, validators=[MaxValueValidator(3)]
    )

    @property
    def name_short(self) -> str:
        CHOICES = (
            pgettext("team_name_team0_abbr", "Teamless"),
            pgettext("team_name_team1_abbr", "Mystic"),
            pgettext("team_name_team2_abbr", "Valor"),
            pgettext("team_name_team3_abbr", "Instinct"),
        )
        return CHOICES[self.id]

    @property
    def name_long(self) -> str:
        CHOICES = (
            pgettext("team_name_team0", "No Team"),
            pgettext("team_name_team1", "Team Mystic"),
            pgettext("team_name_team2", "Team Valor"),
            pgettext("team_name_team3", "Team Instinct"),
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
        verbose_name=pgettext_lazy("profile_start_date", "Start Date"),
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
    def codename(self) -> str:
        return self.username

    nickname = codename

    @property
    def avatar(self) -> str:
        class Avatar:
            def __init__(self, url):
                self.url = url

        return Avatar(self.faction.avatar)

    def __str__(self) -> str:
        return self.username

    def __repr__(self) -> str:
        return f"pk: {self.pk} codename: {self.username} faction: {self.faction}"

    class Meta(AbstractUser.Meta):
        verbose_name = npgettext_lazy("trainer", "trainer", "trainers", 1)
        verbose_name_plural = npgettext_lazy("trainer", "trainer", "trainers", 2)


class Codename(LifecycleModelMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=Trainer._meta.verbose_name,
        related_name="codenames",
    )
    codename = django.contrib.postgres.fields.CICharField(
        max_length=15,
        unique=True,
        validators=[PokemonGoUsernameValidator],
        db_index=True,
        verbose_name=npgettext_lazy("codename", "Nickname", "Nicknames", 1),
    )
    active = ExclusiveBooleanField(
        on="user",
    )

    def __str__(self) -> str:
        return self.codename

    @hook("after_save", when="active", is_now=True)
    def on_active_set_username_on_user(self) -> None:
        self.user.username = self.codename
        self.user.save(update_fields=["username"])

    class Meta:
        ordering = ["codename"]
        verbose_name = npgettext_lazy("codename", "Nickname", "Nicknames", 1)
        verbose_name_plural = npgettext_lazy("codename", "Nickname", "Nicknames", 2)


@receiver(post_save, sender=Trainer)
def create_codename(sender, instance: Trainer, created: bool, **kwargs) -> Codename:
    if kwargs.get("raw"):
        return None

    if created:
        return Codename.objects.create(user=instance, codename=instance.username, active=True)


class FriendCode(LifecycleModelMixin, models.Model):

    trainer = models.OneToOneField(
        Trainer,
        on_delete=models.CASCADE,
        related_name="friend_code",
        verbose_name=Trainer._meta.verbose_name,
        primary_key=True,
    )
    code = models.CharField(
        null=True,
        blank=True,
        validators=[
            FriendCodeValidator,
            MinLengthValidator(12),
            MaxLengthValidator(15),
        ],
        max_length=15,
        verbose_name=pgettext_lazy("friend_code_title", "Trainer Code"),
    )

    def __str__(self) -> str:
        return str(self.trainer)

    @hook("before_save")
    def format_code(self):
        self.code = re.sub(r"\D", "", self.code)

    class Meta:
        verbose_name = pgettext_lazy("friend_code_title", "Trainer Code")
        permissions = [
            (
                "share_friend_code_to_groups",
                _("Trainer Code can be seen by users of groups they're in"),
            ),
            (
                "share_friend_code_to_web",
                _("Trainer Code can be seen on the web, publicly"),
            ),
            (
                "share_friend_code_to_api",
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
        default=dict,
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_title", "Kanto"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries", "Register {0} Kanto region Pokémon in the Pokédex."
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_title", "Johto"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen2",
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_gen3_title", "Hoenn"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen3",
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_gen4_title", "Sinnoh"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen4",
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_gen5_title", "Unova"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen5",
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_gen6_title", "Kalos"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen6",
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_gen7_title", "Alola"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen7",
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
        verbose_name=pgettext_lazy("badge_pokedex_entries_gen8_title", "Galar"),
        help_text=pgettext_lazy(
            "badge_pokedex_entries_gen8",
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
            title=pgettext_lazy("badge_travel_km_title", "Jogger"),
            alt=pgettext_lazy("avatar_detail_walking_distance", "Distance Walked"),
        ),
        help_text=pgettext_lazy("badge_travel_km", "Walk {0:0,g} km."),
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
            title=pgettext_lazy("badge_capture_total_title", "Collector"),
            alt=pgettext_lazy("avatar_detail_pokemon_caught", "Pokémon Caught"),
        ),
        help_text=pgettext_lazy("badge_capture_total", "Catch {0} Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 30), (_("Silver"), 500), (_("Gold"), 2000)],
        badge_id=3,
        translation_ref="badge_capture_total",
    )
    evolved_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_evolved_total_title", "Scientist"),
        help_text=pgettext_lazy("badge_evolved_total", "Evolve {0} Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 20), (_("Gold"), 200)],
        badge_id=5,
        translation_ref="badge_evolved_total",
    )
    hatched_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_hatched_total_title", "Breeder"),
        help_text=pgettext_lazy("badge_hatched_total", "Hatch {0} eggs."),
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
            title=pgettext_lazy("badge_pokestops_visited_title", "Backpacker"),
            alt=pgettext_lazy("profile_pokestops_visited", "PokéStops Visited"),
        ),
        help_text=pgettext_lazy("badge_pokestops_visited", "Visit {0} PokéStops."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 100), (_("Silver"), 1000), (_("Gold"), 2000)],
        badge_id=8,
        translation_ref="badge_pokestops_visited",
    )
    big_magikarp = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_big_magikarp_title", "Fisher"),
        help_text=pgettext_lazy("badge_big_magikarp", "Catch {0} big Magikarp."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 50), (_("Gold"), 300)],
        badge_id=11,
        translation_ref="badge_big_magikarp",
    )
    battle_attack_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_battle_attack_won_title", "Battle Girl"),
        help_text=pgettext_lazy("badge_battle_attack_won", "Win {0} Gym battles."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=13,
        translation_ref="badge_battle_attack_won",
    )
    battle_training_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_battle_training_won_title", "Ace Trainer"),
        help_text=pgettext_lazy("badge_battle_training_won", "Train {0} times."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=14,
        translation_ref="badge_battle_training_won",
    )
    small_rattata = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_small_rattata_title", "Youngster"),
        help_text=pgettext_lazy("badge_small_rattata", "Catch {0} tiny Rattata."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 50), (_("Gold"), 300)],
        badge_id=36,
        translation_ref="badge_small_rattata",
    )
    pikachu = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_pikachu_title", "Pikachu Fan"),
        help_text=pgettext_lazy("badge_pikachu", "Catch {0} Pikachu."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 3), (_("Silver"), 50), (_("Gold"), 300)],
        badge_id=37,
        translation_ref="badge_pikachu",
    )
    unown = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_unown_title", "Unown"),
        help_text=pgettext_lazy("badge_unown", "Catch {0} Unown."),
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
        verbose_name=pgettext_lazy("badge_raid_battle_won_title", "Champion"),
        help_text=pgettext_lazy("badge_raid_battle_won", "Win {0} Raids."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=40,
        translation_ref="badge_raid_battle_won",
    )
    legendary_battle_won = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_legendary_battle_won_title", "Battle Legend"),
        help_text=pgettext_lazy("badge_legendary_battle_won", "Win {0} Legendary Raids."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=41,
        translation_ref="badge_legendary_battle_won",
    )
    berries_fed = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_berries_fed_title", "Berry Master"),
        help_text=pgettext_lazy("badge_berries_fed", "Feed {0} Berries at Gyms."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=42,
        translation_ref="badge_berries_fed",
    )
    hours_defended = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_hours_defended_title", "Gym Leader"),
        help_text=pgettext_lazy("badge_hours_defended", "Defend Gyms for {0} hours."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=43,
        translation_ref="badge_hours_defended",
    )
    challenge_quests = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_challenge_quests_title", "Pokémon Ranger"),
        help_text=pgettext_lazy("badge_challenge_quests", "Complete {0} Field Research tasks."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=46,
        translation_ref="badge_challenge_quests",
    )
    max_level_friends = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_max_level_friends_title", "Idol"),
        help_text=npgettext_lazy(
            "badge_max_level_friends",
            "Become Best Friends with {0} Trainer.",
            "Become Best Friends with {0} Trainers.",
            3,
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
        verbose_name=pgettext_lazy("badge_trading_title", "Gentleman"),
        help_text=pgettext_lazy("badge_trading", "Trade {0} Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 100), (_("Gold"), 1000)],
        badge_id=49,
        translation_ref="badge_trading",
    )
    trading_distance = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_trading_distance_title", "Pilot"),
        help_text=pgettext_lazy(
            "badge_trading_distance", "Earn {0} km across the distance of all Pokémon trades."
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
        verbose_name=pgettext_lazy("badge_great_league_title", "Great League Veteran"),
        help_text=npgettext_lazy(
            "badge_great_league",
            "Win a Trainer Battle in the Great League.",
            "Win {0} Trainer Battles in the Great League.",
            200,
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
        verbose_name=pgettext_lazy("badge_ultra_league_title", "Ultra League Veteran"),
        help_text=npgettext_lazy(
            "badge_ultra_league",
            "Win a Trainer Battle in the Ultra League.",
            "Win {0} Trainer Battles in the Ultra League.",
            200,
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
        verbose_name=pgettext_lazy("badge_master_league_title", "Master League Veteran"),
        help_text=npgettext_lazy(
            "badge_master_league",
            "Win a Trainer Battle in the Master League.",
            "Win {0} Trainer Battles in the Master League.",
            200,
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
        verbose_name=pgettext_lazy("badge_photobomb_title", "Cameraman"),
        help_text=npgettext_lazy(
            "badge_photobomb",
            "Have {0} surprise encounter in GO Snapshot.",
            "Have {0} surprise encounters in GO Snapshot.",
            200,
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 50), (_("Gold"), 200)],
        badge_id=55,
        translation_ref="badge_photobomb",
    )
    pokemon_purified = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_pokemon_purified_title", "Purifier"),
        help_text=pgettext_lazy("badge_pokemon_purified", "Purify {0} Shadow Pokémon."),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 5), (_("Silver"), 50), (_("Gold"), 500)],
        badge_id=57,
        translation_ref="badge_pokemon_purified",
    )
    rocket_grunts_defeated = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_rocket_grunts_defeated_title", "Hero"),
        help_text=pgettext_lazy(
            "badge_rocket_grunts_defeated", "Defeat {0} Team GO Rocket Grunts."
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
        verbose_name=pgettext_lazy("badge_rocket_giovanni_defeated_title", "Ulta Hero"),
        help_text=npgettext_lazy(
            "badge_rocket_giovanni_defeated",
            "Defeat the Team GO Rocket Boss.",
            "Defeat the Team GO Rocket Boss {0} times. ",
            20,
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
        verbose_name=pgettext_lazy("badge_buddy_best_title", "Best Buddy"),
        help_text=npgettext_lazy(
            "badge_buddy_best", "Have 1 Best Buddy.", "Have {0} Best Buddies.", 100
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 1), (_("Silver"), 10), (_("Gold"), 100)],
        badge_id=60,
        translation_ref="badge_buddy_best",
    )
    wayfarer = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_wayfarer_title", "Wayfarer"),
        help_text=npgettext_lazy(
            "badge_wayfarer",
            "Earn a Wayfarer Agreement",
            "Earn {0} Wayfarer Agreements",
            1000,
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 50), (_("Silver"), 500), (_("Gold"), 1000)],
        badge_id=68,
        translation_ref="badge_wayfarer",
    )
    total_mega_evos = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_total_mega_evos_title", "Successor"),
        help_text=npgettext_lazy(
            "badge_total_mega_evos",
            "Mega Evolve a Pokémon {0} time.",
            "Mega Evolve a Pokémon {0} times.",
            500,
        ),
        reversable=False,
        sortable=True,
        levels=[(_("Bronze"), 10), (_("Silver"), 50), (_("Gold"), 500)],
        badge_id=69,
        translation_ref="badge_total_mega_evos",
    )
    unique_mega_evos = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_unique_mega_evos_title", "Mega Evolution Guru"),
        help_text=npgettext_lazy(
            "badge_unique_mega_evos",
            "Mega Evolve {0} Pokémon.",
            "Mega Evolve {0} different species of Pokémon.",
            36,
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
        verbose_name=pgettext_lazy("badge_type_normal_title", "Schoolkid"),
        help_text=pgettext_lazy("badge_type_normal", "Catch {0} Normal-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=18,
        translation_ref="badge_type_normal",
    )
    type_fighting = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_fighting_title", "Black Belt"),
        help_text=pgettext_lazy("badge_type_fighting", "Catch {0} Fighting-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=19,
        translation_ref="badge_type_fighting",
    )
    type_flying = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_flying_title", "Bird Keeper"),
        help_text=pgettext_lazy("badge_type_flying", "Catch {0} Flying-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=20,
        translation_ref="badge_type_flying",
    )
    type_poison = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_poison_title", "Punk Girl"),
        help_text=pgettext_lazy("badge_type_poison", "Catch {0} Poison-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=21,
        translation_ref="badge_type_poison",
    )
    type_ground = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_ground_title", "Ruin Maniac"),
        help_text=pgettext_lazy("badge_type_ground", "Catch {0} Ground-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=22,
        translation_ref="badge_type_ground",
    )
    type_rock = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_rock_title", "Hiker"),
        help_text=pgettext_lazy("badge_type_rock", "Catch {0} Rock-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=23,
        translation_ref="badge_type_rock",
    )
    type_bug = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_bug_title", "Bug Catcher"),
        help_text=pgettext_lazy("badge_type_bug", "Catch {0} Bug-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=24,
        translation_ref="badge_type_bug",
    )
    type_ghost = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_ghost_title", "Hex Maniac"),
        help_text=pgettext_lazy("badge_type_ghost", "Catch {0} Ghost-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=25,
        translation_ref="badge_type_ghost",
    )
    type_steel = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_steel_title", "Rail Staff"),
        help_text=pgettext_lazy("badge_type_steel", "Catch {0} Steel-type Pokémon."),
        reversable=False,
        sortable=True,
        badge_id=26,
        translation_ref="badge_type_steel",
    )
    type_fire = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_fire_title", "Kindler"),
        help_text=pgettext_lazy("badge_type_fire", "Catch {0} Fire-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=27,
        translation_ref="badge_type_fire",
    )
    type_water = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_water_title", "Swimmer"),
        help_text=pgettext_lazy("badge_type_water", "Catch {0} Water-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=28,
        translation_ref="badge_type_water",
    )
    type_grass = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_grass_title", "Gardener"),
        help_text=pgettext_lazy("badge_type_grass", "Catch {0} Grass-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=29,
        translation_ref="badge_type_grass",
    )
    type_electric = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_electric_title", "Rocker"),
        help_text=pgettext_lazy("badge_type_electric", "Catch {0} Electric-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=30,
        translation_ref="badge_type_electric",
    )
    type_psychic = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_psychic_title", "Psychic"),
        help_text=pgettext_lazy("badge_type_psychic", "Catch {0} Pychic-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=31,
        translation_ref="badge_type_psychic",
    )
    type_ice = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_ice_title", "Skier"),
        help_text=pgettext_lazy("badge_type_ice", "Catch {0} Ice-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=32,
        translation_ref="badge_type_ice",
    )
    type_dragon = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_dragon_title", "Dragon Tamer"),
        help_text=pgettext_lazy("badge_type_dragon", "Catch {0} Dragon-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=33,
        translation_ref="badge_type_dragon",
    )
    type_dark = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_dark_title", "Delinquent"),
        help_text=pgettext_lazy("badge_type_dark", "Catch {0} Dark-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=34,
        translation_ref="badge_type_dark",
    )
    type_fairy = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("badge_type_fairy_title", "Fairy Tale Girl"),
        help_text=pgettext_lazy("badge_type_fairy", "Catch {0} Fairy-type Pokémon"),
        reversable=False,
        sortable=True,
        badge_id=35,
        translation_ref="badge_type_fairy",
    )

    gymbadges_total = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("profile_category_gymbadges", "Gym Badges"),
        reversable=True,
        sortable=False,
        translation_ref="profile_category_gymbadges",
    )
    gymbadges_gold = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Gold Gym Badges"),
        reversable=True,
        sortable=False,
    )
    stardust = PogoPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("pokemon_info_stardust_label", "Stardust"),
        reversable=True,
        sortable=False,
        translation_ref="pokemon_info_stardust_label",
    )

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.__repr__()})"

    def __repr__(self) -> str:
        return f"trainer: {self.trainer} update_time: {self.update_time}"

    def modified_fields(self) -> Iterator[str]:
        fields = [
            field.name
            for field in Update._meta.fields
            if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
        ]

        for x in fields:
            if getattr(self, x):
                yield x

    def clean(self) -> None:
        super().clean()
        errors = defaultdict(list)
        fields = [
            field
            for field in Update._meta.fields
            if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
        ]

        if not any([(getattr(self, field.name) is not None) for field in fields]):
            raise ValidationError(
                _("You must fill in at least one field"),
                code="nodata",
            )

        for field in fields:
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
            if last_update is not None and field.reversable is False:
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
        fields = [
            field
            for field in Update._meta.fields
            if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
        ]

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
                "DailyLimit": Decimal("60"),
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

        for field in fields:
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
            len("update.")
            + len(
                max(
                    [
                        field.name
                        for field in Update._meta.fields
                        if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
                    ],
                    key=len,
                )
            ),
            len("trainer.profile"),
        ),
        choices=[
            ("trainer.profile", Trainer._meta.verbose_name.title()),
        ]
        + [
            (
                f"update.{field.name}",
                f"{Update._meta.verbose_name.title()}.{field.verbose_name}",
            )
            for field in Update._meta.fields
            if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
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
        max_length=len(
            max(
                [
                    field.name
                    for field in Update._meta.fields
                    if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
                ],
                key=len,
            )
        ),
        choices=[
            (field.name, field.verbose_name)
            for field in Update._meta.fields
            if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
            and field.reversable is False
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

    def __target_str_(self) -> str:
        return f"{self.target:0,}"

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
