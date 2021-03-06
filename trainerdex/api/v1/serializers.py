﻿from typing import Dict, List, Union

from allauth.socialaccount.models import SocialAccount
from rest_framework import serializers

from trainerdex.models import Trainer, Update

v1_field_names = {
    "update": {
        "uuid": "uuid",
        "trainer": "trainer",
        "update_time": "update_time",
        "submission_date": "submission_date",
        "data_source": "data_source",
        "total_xp": "total_xp",
        "pokedex_total_caught": "pokedex_caught",
        "pokedex_total_seen": "pokedex_seen",
        "pokedex_gen1": "badge_pokedex_entries",
        "pokedex_gen2": "badge_pokedex_entries_gen2",
        "pokedex_gen3": "badge_pokedex_entries_gen3",
        "pokedex_gen4": "badge_pokedex_entries_gen4",
        "pokedex_gen5": "badge_pokedex_entries_gen5",
        "pokedex_gen6": "badge_pokedex_entries_gen6",
        "pokedex_gen7": "badge_pokedex_entries_gen7",
        "pokedex_gen8": "badge_pokedex_entries_gen8",
        "travel_km": "badge_travel_km",
        "capture_total": "badge_capture_total",
        "evolved_total": "badge_evolved_total",
        "hatched_total": "badge_hatched_total",
        "pokestops_visited": "badge_pokestops_visited",
        "big_magikarp": "badge_big_magikarp",
        "battle_attack_won": "badge_battle_attack_won",
        "battle_training_won": "badge_battle_training_won",
        "small_rattata": "badge_small_rattata",
        "pikachu": "badge_pikachu",
        "unown": "badge_unown",
        "raid_battle_won": "badge_raid_battle_won",
        "legendary_battle_won": "badge_legendary_battle_won",
        "berries_fed": "badge_berries_fed",
        "hours_defended": "badge_hours_defended",
        "challenge_quests": "badge_challenge_quests",
        "max_level_friends": "badge_max_level_friends",
        "trading": "badge_trading",
        "trading_distance": "badge_trading_distance",
        "great_league": "badge_great_league",
        "ultra_league": "badge_ultra_league",
        "master_league": "badge_master_league",
        "photobomb": "badge_photobomb",
        "pokemon_purified": "badge_pokemon_purified",
        "rocket_grunts_defeated": "badge_rocket_grunts_defeated",
        "rocket_giovanni_defeated": "badge_rocket_giovanni_defeated",
        "buddy_best": "badge_buddy_best",
        "wayfarer": "badge_wayfarer",
        "total_mega_evos": "badge_total_mega_evos",
        "unique_mega_evos": "badge_unique_mega_evos",
        "type_normal": "badge_type_normal",
        "type_fighting": "badge_type_fighting",
        "type_flying": "badge_type_flying",
        "type_poison": "badge_type_poison",
        "type_ground": "badge_type_ground",
        "type_rock": "badge_type_rock",
        "type_bug": "badge_type_bug",
        "type_ghost": "badge_type_ghost",
        "type_steel": "badge_type_steel",
        "type_fire": "badge_type_fire",
        "type_water": "badge_type_water",
        "type_grass": "badge_type_grass",
        "type_electric": "badge_type_electric",
        "type_psychic": "badge_type_psychic",
        "type_ice": "badge_type_ice",
        "type_dragon": "badge_type_dragon",
        "type_dark": "badge_type_dark",
        "type_fairy": "badge_type_fairy",
        "gymbadges_total": "gymbadges_total",
        "gymbadges_gold": "gymbadges_gold",
        "stardust": "pokemon_info_stardust",
    },
    "trainer": {
        "id": "owner",
        "start_date": "start_date",
        "faction": "faction",
        "country": "leaderboard_country",
        "is_verified": "verified",
        "last_modified": "last_modified",
    },
}


class BriefUpdateSerializer(serializers.ModelSerializer):
    xp = serializers.SerializerMethodField()
    trainer = serializers.SerializerMethodField()
    modified_extra_fields = serializers.SerializerMethodField()

    def get_xp(self, obj: Update) -> int:
        """This field is deprecated and will be removed in API v2"""
        return getattr(obj, "total_xp")

    def get_trainer(self, obj: Update) -> int:
        return getattr(obj, "trainer").tid

    def get_modified_extra_fields(self, obj: Update) -> List[str]:
        return [v1_field_names["update"][x] for x in obj.modified_extra_fields()]

    class Meta:
        model = Update
        fields = (
            "uuid",
            "trainer",
            "update_time",
            "xp",
            "total_xp",
            "modified_extra_fields",
        )


class DetailedUpdateSerializer(serializers.ModelSerializer):
    trainer = serializers.SerializerMethodField()
    pokedex_caught = serializers.SerializerMethodField()
    pokedex_seen = serializers.SerializerMethodField()
    badge_pokedex_entries = serializers.SerializerMethodField()
    badge_pokedex_entries_gen2 = serializers.SerializerMethodField()
    badge_pokedex_entries_gen3 = serializers.SerializerMethodField()
    badge_pokedex_entries_gen4 = serializers.SerializerMethodField()
    badge_pokedex_entries_gen5 = serializers.SerializerMethodField()
    badge_pokedex_entries_gen6 = serializers.SerializerMethodField()
    badge_pokedex_entries_gen7 = serializers.SerializerMethodField()
    badge_pokedex_entries_gen8 = serializers.SerializerMethodField()
    badge_travel_km = serializers.SerializerMethodField()
    badge_capture_total = serializers.SerializerMethodField()
    badge_evolved_total = serializers.SerializerMethodField()
    badge_hatched_total = serializers.SerializerMethodField()
    badge_pokestops_visited = serializers.SerializerMethodField()
    badge_big_magikarp = serializers.SerializerMethodField()
    badge_battle_attack_won = serializers.SerializerMethodField()
    badge_battle_training_won = serializers.SerializerMethodField()
    badge_small_rattata = serializers.SerializerMethodField()
    badge_pikachu = serializers.SerializerMethodField()
    badge_unown = serializers.SerializerMethodField()
    badge_raid_battle_won = serializers.SerializerMethodField()
    badge_legendary_battle_won = serializers.SerializerMethodField()
    badge_berries_fed = serializers.SerializerMethodField()
    badge_hours_defended = serializers.SerializerMethodField()
    badge_challenge_quests = serializers.SerializerMethodField()
    badge_max_level_friends = serializers.SerializerMethodField()
    badge_trading = serializers.SerializerMethodField()
    badge_trading_distance = serializers.SerializerMethodField()
    badge_great_league = serializers.SerializerMethodField()
    badge_ultra_league = serializers.SerializerMethodField()
    badge_master_league = serializers.SerializerMethodField()
    badge_photobomb = serializers.SerializerMethodField()
    badge_pokemon_purified = serializers.SerializerMethodField()
    badge_rocket_grunts_defeated = serializers.SerializerMethodField()
    badge_buddy_best = serializers.SerializerMethodField()
    badge_wayfarer = serializers.SerializerMethodField()
    badge_type_normal = serializers.SerializerMethodField()
    badge_type_fighting = serializers.SerializerMethodField()
    badge_type_flying = serializers.SerializerMethodField()
    badge_type_poison = serializers.SerializerMethodField()
    badge_type_ground = serializers.SerializerMethodField()
    badge_type_rock = serializers.SerializerMethodField()
    badge_type_bug = serializers.SerializerMethodField()
    badge_type_ghost = serializers.SerializerMethodField()
    badge_type_steel = serializers.SerializerMethodField()
    badge_type_fire = serializers.SerializerMethodField()
    badge_type_water = serializers.SerializerMethodField()
    badge_type_grass = serializers.SerializerMethodField()
    badge_type_electric = serializers.SerializerMethodField()
    badge_type_psychic = serializers.SerializerMethodField()
    badge_type_ice = serializers.SerializerMethodField()
    badge_type_dragon = serializers.SerializerMethodField()
    badge_type_dark = serializers.SerializerMethodField()
    badge_type_fairy = serializers.SerializerMethodField()
    gymbadges_total = serializers.SerializerMethodField()
    gymbadges_gold = serializers.SerializerMethodField()
    pokemon_info_stardust = serializers.SerializerMethodField()

    def get_trainer(self, obj: Update) -> int:
        return getattr(obj, "trainer").tid

    def get_xp(self, obj: Update) -> int:
        """This field is deprecated and will be removed in API v2"""
        return getattr(obj, "total_xp")

    def get_pokedex_caught(self, obj: Update) -> int:
        return getattr(obj, "pokedex_total_caught")

    def get_pokedex_seen(self, obj: Update) -> int:
        return getattr(obj, "pokedex_total_seen")

    def get_badge_pokedex_entries(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen1")

    def get_badge_pokedex_entries_gen2(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen2")

    def get_badge_pokedex_entries_gen3(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen3")

    def get_badge_pokedex_entries_gen4(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen4")

    def get_badge_pokedex_entries_gen5(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen5")

    def get_badge_pokedex_entries_gen6(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen6")

    def get_badge_pokedex_entries_gen7(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen7")

    def get_badge_pokedex_entries_gen8(self, obj: Update) -> int:
        return getattr(obj, "pokedex_gen8")

    def get_badge_travel_km(self, obj: Update) -> str:
        return str(getattr(obj, "travel_km"))

    def get_badge_capture_total(self, obj: Update) -> int:
        return getattr(obj, "capture_total")

    def get_badge_evolved_total(self, obj: Update) -> int:
        return getattr(obj, "evolved_total")

    def get_badge_hatched_total(self, obj: Update) -> int:
        return getattr(obj, "hatched_total")

    def get_badge_pokestops_visited(self, obj: Update) -> int:
        return getattr(obj, "pokestops_visited")

    def get_badge_big_magikarp(self, obj: Update) -> int:
        return getattr(obj, "big_magikarp")

    def get_badge_battle_attack_won(self, obj: Update) -> int:
        return getattr(obj, "battle_attack_won")

    def get_badge_battle_training_won(self, obj: Update) -> int:
        return getattr(obj, "battle_training_won")

    def get_badge_small_rattata(self, obj: Update) -> int:
        return getattr(obj, "small_rattata")

    def get_badge_pikachu(self, obj: Update) -> int:
        return getattr(obj, "pikachu")

    def get_badge_unown(self, obj: Update) -> int:
        return getattr(obj, "unown")

    def get_badge_raid_battle_won(self, obj: Update) -> int:
        return getattr(obj, "raid_battle_won")

    def get_badge_legendary_battle_won(self, obj: Update) -> int:
        return getattr(obj, "legendary_battle_won")

    def get_badge_berries_fed(self, obj: Update) -> int:
        return getattr(obj, "berries_fed")

    def get_badge_hours_defended(self, obj: Update) -> int:
        return getattr(obj, "hours_defended")

    def get_badge_challenge_quests(self, obj: Update) -> int:
        return getattr(obj, "challenge_quests")

    def get_badge_max_level_friends(self, obj: Update) -> int:
        return getattr(obj, "max_level_friends")

    def get_badge_trading(self, obj: Update) -> int:
        return getattr(obj, "trading")

    def get_badge_trading_distance(self, obj: Update) -> int:
        return getattr(obj, "trading_distance")

    def get_badge_great_league(self, obj: Update) -> int:
        return getattr(obj, "great_league")

    def get_badge_ultra_league(self, obj: Update) -> int:
        return getattr(obj, "ultra_league")

    def get_badge_master_league(self, obj: Update) -> int:
        return getattr(obj, "master_league")

    def get_badge_photobomb(self, obj: Update) -> int:
        return getattr(obj, "photobomb")

    def get_badge_pokemon_purified(self, obj: Update) -> int:
        return getattr(obj, "pokemon_purified")

    def get_badge_rocket_grunts_defeated(self, obj: Update) -> int:
        return getattr(obj, "rocket_grunts_defeated")

    def get_badge_buddy_best(self, obj: Update) -> int:
        return getattr(obj, "buddy_best")

    def get_badge_wayfarer(self, obj: Update) -> int:
        return getattr(obj, "wayfarer")

    def get_badge_type_normal(self, obj: Update) -> int:
        return getattr(obj, "type_normal")

    def get_badge_type_fighting(self, obj: Update) -> int:
        return getattr(obj, "type_fighting")

    def get_badge_type_flying(self, obj: Update) -> int:
        return getattr(obj, "type_flying")

    def get_badge_type_poison(self, obj: Update) -> int:
        return getattr(obj, "type_poison")

    def get_badge_type_ground(self, obj: Update) -> int:
        return getattr(obj, "type_ground")

    def get_badge_type_rock(self, obj: Update) -> int:
        return getattr(obj, "type_rock")

    def get_badge_type_bug(self, obj: Update) -> int:
        return getattr(obj, "type_bug")

    def get_badge_type_ghost(self, obj: Update) -> int:
        return getattr(obj, "type_ghost")

    def get_badge_type_steel(self, obj: Update) -> int:
        return getattr(obj, "type_steel")

    def get_badge_type_fire(self, obj: Update) -> int:
        return getattr(obj, "type_fire")

    def get_badge_type_water(self, obj: Update) -> int:
        return getattr(obj, "type_water")

    def get_badge_type_grass(self, obj: Update) -> int:
        return getattr(obj, "type_grass")

    def get_badge_type_electric(self, obj: Update) -> int:
        return getattr(obj, "type_electric")

    def get_badge_type_psychic(self, obj: Update) -> int:
        return getattr(obj, "type_psychic")

    def get_badge_type_ice(self, obj: Update) -> int:
        return getattr(obj, "type_ice")

    def get_badge_type_dragon(self, obj: Update) -> int:
        return getattr(obj, "type_dragon")

    def get_badge_type_dark(self, obj: Update) -> int:
        return getattr(obj, "type_dark")

    def get_badge_type_fairy(self, obj: Update) -> int:
        return getattr(obj, "type_fairy")

    def get_gymbadges_total(self, obj: Update) -> int:
        return getattr(obj, "gymbadges_total")

    def get_gymbadges_gold(self, obj: Update) -> int:
        return getattr(obj, "gymbadges_gold")

    def get_pokemon_info_stardust(self, obj: Update) -> int:
        return getattr(obj, "stardust")

    class Meta:
        model = Update
        fields = tuple(v1_field_names["update"].values())


class TrainerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    trainer_code = serializers.SerializerMethodField()
    friend_code = serializers.SerializerMethodField()
    has_cheated = serializers.SerializerMethodField()
    last_cheated = serializers.SerializerMethodField()
    currently_cheats = serializers.SerializerMethodField()
    daily_goal = serializers.SerializerMethodField()
    total_goal = serializers.SerializerMethodField()
    leaderboard_country = serializers.SerializerMethodField()
    leaderboard_region = serializers.SerializerMethodField()
    update_set = serializers.SerializerMethodField()
    prefered = serializers.SerializerMethodField()

    def get_user(self, obj: Trainer) -> int:
        return getattr(obj, "pk")

    def get_owner(self, obj: Trainer) -> int:
        return getattr(obj, "pk")

    def get_username(self, obj: Trainer) -> str:
        return getattr(obj, "codename")

    def get_friend_code(self, obj: Trainer) -> str:
        if obj.has_perm("trainerdex.share_friend_code_to_api"):
            if hasattr(obj, "friend_code"):
                return obj.friend_code.code
        return None

    def get_trainer_code(self, obj: Trainer) -> str:
        return self.get_friend_code(obj)

    def get_has_cheated(self, obj: Trainer) -> bool:
        return getattr(obj, "is_banned")

    def get_last_cheated(self, obj: Trainer) -> None:
        return None

    def get_currently_cheats(self, obj: Trainer) -> bool:
        return getattr(obj, "is_banned")

    def get_daily_goal(self, obj: Trainer) -> None:
        return None

    def get_total_goal(self, obj: Trainer) -> None:
        return None

    def get_leaderboard_country(self, obj: Trainer) -> str:
        return getattr(obj, "country").code

    def get_leaderboard_region(self, obj: Trainer) -> None:
        return None

    def get_update_set(self, obj: Trainer) -> Dict[str, Union[str, int]]:
        return BriefUpdateSerializer(obj.updates, read_only=True, many=True).data

    def get_prefered(self, obj: Trainer) -> bool:
        """This field is deprecated and will be removed in API v2"""
        return True

    class Meta:
        model = Trainer
        fields = (
            "id",
            "last_modified",
            "owner",
            "user",
            "username",
            "start_date",
            "faction",
            "trainer_code",
            "friend_code",
            "has_cheated",
            "last_cheated",
            "currently_cheats",
            "daily_goal",
            "total_goal",
            "leaderboard_country",
            "leaderboard_region",
            "update_set",
            "prefered",
        )


class UserSerializer(serializers.ModelSerializer):
    profiles = serializers.SerializerMethodField()
    trainer = serializers.SerializerMethodField()

    def get_trainer(self, obj: Trainer) -> int:
        """This field is deprecated and will be removed in API v2"""
        return obj.tid

    def get_profiles(self, obj: Trainer) -> List[int]:
        """This field is deprecated and will be removed in API v2"""
        trainer = self.get_trainer(obj)
        if trainer:
            return [trainer]
        else:
            return []

    class Meta:
        model = Trainer
        fields = ("id", "username", "first_name", "last_name", "profiles", "trainer")


class SocialAllAuthSerializer(serializers.ModelSerializer):

    trainer = serializers.SerializerMethodField()

    def get_trainer(self, obj: SocialAccount) -> int:
        return obj.user.trainer.pk

    class Meta:
        model = SocialAccount
        fields = (
            "user",
            "provider",
            "uid",
            "extra_data",
            "trainer",
        )
