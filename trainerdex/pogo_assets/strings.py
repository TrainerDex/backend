"""
This file only exists to make sure certain strings stay in the translation files as they become in
and out of use within the codebase.
"""
from django.utils.translation import pgettext as _, npgettext as __

remote_metadata = ("2020-09-03T22:21:05.018639", "a7cbdfdeb5ba0f10697cce720de093807c4a9a4c")
apk_metadata = ("2020-09-01T22:45:11.849571", "339c3fbf671838056e38cd7b43276db48e33b64c")

_("badge_battle_attack_won", "Win {0} Gym battles.")
_("badge_battle_attack_won_title", "Battle Girl")

_("badge_battle_defend_won", "Win {0} defense battles!")
_("badge_battle_defend_won_title", "Defense Battles Won")

_("badge_battle_training_won", "Train {0} times.")
_("badge_battle_training_won_title", "Ace Trainer")

_("badge_berries_fed", "Feed {0} Berries at Gyms.")
_("badge_berries_fed_title", "Berry Master")

_("badge_big_magikarp", "Catch {0} big Magikarp.")
_("badge_big_magikarp_title", "Fisher")

__("badge_buddy_best", "Have 1 Best Buddy.", "Have {0} Best Buddies.", 1)
_("badge_buddy_best_title", "Best Buddy")

_("badge_capture_total", "Catch {0} Pokémon.")
_("badge_capture_total_title", "Collector")

_("badge_challenge_quests", "Complete {0} Field Research tasks.")
_("badge_challenge_quests_title", "Pokémon Ranger")

_("badge_defeated_fort", "Win {0} battles.")
_("badge_defeated_fort_title", "Battle")

_("badge_deployed_total", "Assign {0} Pokémon to Gyms!")
_("badge_deployed_total_title", "Pokémon at Gyms")

_("badge_encountered_total", "Encounter {0} Pokémon.")
_("badge_encountered_total_title", "Encounters")

_("badge_evolved_total", "Evolve {0} Pokémon.")
_("badge_evolved_total_title", "Scientist")

__(
    "badge_great_league",
    "Win a Trainer Battle in the Great League.",
    "Win {0} Trainer Battles in the Great League.",
    1,
)
_("badge_great_league_title", "Great League Veteran")

_("badge_hatched_total", "Hatch {0} Eggs.")
_("badge_hatched_total_title", "Breeder")

_("badge_hours_defended", "Defend Gyms for {0} hours.")
_("badge_hours_defended_title", "Gym Leader")

_("badge_legendary_battle_won", "Win {0} Legendary raids.")
_("badge_legendary_battle_won_title", "Battle Legend")

__(
    "badge_master_league",
    "Win a Trainer Battle in the Master League.",
    "Win {0} Trainer Battles in the Master League.",
    1,
)
_("badge_master_league_title", "Master League Veteran")

__(
    "badge_max_level_friends",
    "Become Best Friends with {0} Trainer.",
    "Become Best Friends with {0} Trainers.",
    1,
)
_("badge_max_level_friends_title", "Idol")

__(
    "badge_photobomb",
    "Have {0} surprise encounter in GO Snapshot.",
    "Have {0} surprise encounters in GO Snapshot.",
    1,
)
_("badge_photobomb_title", "Cameraman")

_("badge_pikachu", "Catch {0} Pikachu.")
_("badge_pikachu_title", "Pikachu Fan")

_("badge_pokedex_entries", "Register {0} Kanto region Pokémon in the Pokédex.")
_("badge_pokedex_entries_title", "Kanto")

_(
    "badge_pokedex_entries_gen2",
    "Register {0} Pokémon first discovered in the Johto region to the Pokédex.",
)
_("badge_pokedex_entries_title", "Johto")

_(
    "badge_pokedex_entries_gen3",
    "Register {0} Pokémon first discovered in the Hoenn region to the Pokédex.",
)
_("badge_pokedex_entries_gen3_title", "Hoenn")

_(
    "badge_pokedex_entries_gen4",
    "Register {0} Pokémon first discovered in the Sinnoh region to the Pokédex.",
)
_("badge_pokedex_entries_gen4_title", "Sinnoh")

_(
    "badge_pokedex_entries_gen5",
    "Register {0} Pokémon first discovered in the Unova region to the Pokédex.",
)
_("badge_pokedex_entries_gen5_title", "Unova")

_(
    "badge_pokedex_entries_gen6",
    "Register {0} Pokémon first discovered in the Kalos region to the Pokédex.",
)
_("badge_pokedex_entries_gen6_title", "Kalos")

_(
    "badge_pokedex_entries_gen7",
    "Register {0} Pokémon first discovered in the Alola region to the Pokédex.",
)
_("badge_pokedex_entries_gen7_title", "Alola")

_(
    "badge_pokedex_entries_gen8",
    "Register {0} Pokémon first discovered in the Galar region to the Pokédex.",
)
_("badge_pokedex_entries_gen8_title", "Galar")

_("badge_pokedex_entries_unknown_title", "Unknown")

_("badge_pokemon_purified", "Purify {0} Shadow Pokémon.")
_("badge_pokemon_purified_title", "Purifier")

_("badge_pokestops_visited", "Visit {0} PokéStops.")
_("badge_pokestops_visited_title", "Backpacker")

_("badge_prestige_dropped", "Reduce {0} total Gym Prestige!")
_("badge_prestige_dropped_title", "Reduced Prestige")

_("badge_prestige_raised", "Raise {0} total Gym Prestige!")
_("badge_prestige_raised_title", "Prestige Raised")

_("badge_raid_battle_won", "Win {0} raids.")
_("badge_raid_battle_won_title", "Champion")

__(
    "badge_rocket_giovanni_defeated",
    "Defeat the Team GO Rocket Boss.",
    "Defeat the Team GO Rocket Boss {0} times. ",
    1,
)
_("badge_rocket_giovanni_defeated_title", "Ultra Hero")

_("badge_rocket_grunts_defeated", "Defeat {0} Team GO Rocket members.")
_("badge_rocket_grunts_defeated_title", "Hero")

_("badge_small_rattata", "Catch {0} tiny Rattata.")
_("badge_small_rattata_title", "Youngster")

_("badge_trading", "Trade {0} Pokémon.")
_("badge_trading_title", "Gentleman")

_("badge_trading_distance", "Earn {0} km across the distance of all Pokémon trades.")
_("badge_trading_distance_title", "Pilot")

_(
    "badge_travel_km", "Walk {0:0,g} km."
)  # Original string uses {0:0.#} but I've had to convert for Python
_("badge_travel_km_title", "Jogger")

_("badge_type_bug", "Catch {0} Bug-type Pokémon.")
_("badge_type_bug_title", "Bug Catcher")

_("badge_type_dark", "Catch {0} Dark-type Pokémon.")
_("badge_type_dark_title", "Delinquent")

_("badge_type_dragon", "Catch {0} Dragon-type Pokémon.")
_("badge_type_dragon_title", "Dragon Tamer")

_("badge_type_electric", "Catch {0} Electric-type Pokémon.")
_("badge_type_electric_title", "Rocker")

_("badge_type_fairy", "Catch {0} Fairy-type Pokémon.")
_("badge_type_fairy_title", "Fairy Tale Girl")

_("badge_type_fighting", "Catch {0} Fighting-type Pokémon.")
_("badge_type_fighting_title", "Black Belt")

_("badge_type_fire", "Catch {0} Fire-type Pokémon.")
_("badge_type_fire_title", "Kindler")

_("badge_type_flying", "Catch {0} Flying-type Pokémon.")
_("badge_type_flying_title", "Bird Keeper")

_("badge_type_ghost", "Catch {0} Ghost-type Pokémon.")
_("badge_type_ghost_title", "Hex Maniac")

_("badge_type_grass", "Catch {0} Grass-type Pokémon.")
_("badge_type_grass_title", "Gardener")

_("badge_type_ground", "Catch {0} Ground-type Pokémon.")
_("badge_type_ground_title", "Ruin Maniac")

_("badge_type_ice", "Catch {0} Ice-type Pokémon.")
_("badge_type_ice_title", "Skier")

_("badge_type_normal", "Catch {0} Normal-type Pokémon.")
_("badge_type_normal_title", "Schoolkid")

_("badge_type_poison", "Catch {0} Poison-type Pokémon.")
_("badge_type_poison_title", "Punk Girl")

_("badge_type_psychic", "Catch {0} Psychic-type Pokémon.")
_("badge_type_psychic_title", "Psychic")

_("badge_type_rock", "Catch {0} Rock-type Pokémon.")
_("badge_type_rock_title", "Hiker")

_("badge_type_steel", "Catch {0} Steel-type Pokémon.")
_("badge_type_steel_title", "Rail Staff")

_("badge_type_water", "Catch {0} Water-type Pokémon.")
_("badge_type_water_title", "Water")

__(
    "badge_ultra_league",
    "Win a Trainer Battle in the Ultra League.",
    "Win {0} Trainer Battles in the Ultra League.",
    1,
)
_("badge_ultra_league_title", "Ultra League Veteran")

_("badge_unique_pokestops", "Visit {0} unique PokéStops.")
_("badge_unique_pokestops_title", "Unique PokéStops")

_("badge_unown", "Catch {0} Unown.")
_("badge_unown_title", "Unown")

__(
    "badge_wayfarer", "Earn a Wayfarer Agreement", "Earn {0} Wayfarer Agreements", 1,
)
_("badge_wayfarer_title", "Wayfarer")

__(
    "badge_total_mega_evos",
    "Mega Evolve a Pokémon {0} time.",
    "Mega Evolve a Pokémon {0} times.",
    1,
)
_("badge_total_mega_evos_title", "Successor")

__(
    "badge_unique_mega_evos",
    "Mega Evolve {0} Pokémon.",
    "Mega Evolve {0} different species of Pokémon.",
    1,
)
_("badge_unique_mega_evos_title", "Mega Evolution Guru")

__("buddy_level_0", "Buddy", "Buddies", 1)
__("buddy_level_1", "Good Buddy", "Good Buddies", 1)
__("buddy_level_2", "Great Buddy", "Great Buddies", 1)
__("buddy_level_3", "Ultra Buddy", "Ultra Buddies", 1)
__("buddy_level_4", "Best Buddy", "Best Buddies", 1)

_("codename_already_yours", "That's already your name!")
_("codename_reassign_success", "You're now known as {0}.")

_("date_format", "MMM dd, yyyy")

_("encounter_score_total_exp", "{0} XP")
_("feedback_added_xp", "+{0} XP")

__("friend", "friend", "friends", 1)
_("friend_code_title", "Trainer Code")
_("friend_full_name", "{0} ({1})")
_("friends_list_level_format", "Lv {0}")

__("friendship_level_0", "Friend", "Friends", 1)
__("friendship_level_1", "Good Friend", "Good Friends", 1)
__("friendship_level_2", "Great Friend", "Great Friends", 1)
__("friendship_level_3", "Ultra Friend", "Ultra Friends", 1)
__("friendship_level_4", "Best Friend", "Best Friends", 1)

_("galarian_pokedex_header", "Galarian Form")

_("general_accept", "Accept")
_("general_allow", "Allow")
_("general_button_select", "Select")
_("general_cancel", "Cancel")
_("general_close", "Close")
_("general_continue", "Continue")
_("general_cp", "CP")
_("general_dismiss", "Dismiss")
_("general_do_not_allow", "Don’t Allow")
_("general_error", "Error")
_("general_go", "GO")
_("general_kg", "kg")
_("general_m", "m")
_("general_more", "More")
_("general_no", "No")
_("general_ok", "OK")
_("general_pokemon", "Pokémon")
_("general_sign_out", "Sign Out")
_("general_sign_out_confirm", "Are you sure you want to sign out?")
_("general_stamina", "HP")
_("general_xp", "XP")
_("general_yes", "Yes")


_("help_center_friends_link", "https://pokemongo.nianticlabs.com/support/friends")
_("help_center_link", "https://pokemongo.nianticlabs.com/support/contact/en")

_("onboard_name_fail", "An error has occurred. Try another name.")
_("onboard_name_invalid_characters_error", "Only letters and numbers are allowed.")
_("onboard_name_not_available", "That name isn't available.")
_("onboard_name_not_valid", "That name is invalid.")
_("onboard_name_owned", "This name is already in use by another Trainer.")

_("pokemon_info_cp", "CP")
_("pokemon_info_stardust_label", "Stardust")
_("pokemon_info_type", "Type")

_("pokemon_type_bug", "Bug")
_("pokemon_type_dark", "Dark")
_("pokemon_type_dragon", "Dragon")
_("pokemon_type_electric", "Electric")
_("pokemon_type_fairy", "Fairy")
_("pokemon_type_fighting", "Fighting")
_("pokemon_type_fire", "Fire")
_("pokemon_type_flying", "Flying")
_("pokemon_type_ghost", "Ghost")
_("pokemon_type_grass", "Grass")
_("pokemon_type_ground", "Ground")
_("pokemon_type_ice", "Ice")
_("pokemon_type_normal", "Normal")
_("pokemon_type_poison", "Poison")
_("pokemon_type_psychic", "Psychic")
_("pokemon_type_rock", "Rock")
_("pokemon_type_steel", "Steel")
_("pokemon_type_water", "Water")

_("privacy_policy_url", "https://www.nianticlabs.com/privacy/pokemongo/en")

_("profile_button_activity_log", "Journal")
_("profile_button_customize", "Style")
_("profile_category_gymbadges", "Gym Badges")
_("profile_category_medals", "Medals")
_("profile_category_stats", "Stats")
_("profile_category_total_fitness", "TOTAL PROGRESS")
_("profile_category_weekly_fitness", "WEEKLY PROGRESS")
_("profile_gymbadges_help", "Learn more")
_("profile_gymbadges_recently_visited", "Recently Visited")
_("profile_no_gymbadges", "You don't have any Gym Badges.")
_("profile_player_level", "Level")
_("profile_pokestops_visited", "PokéStops Visited:")
_("profile_start_date", "Start Date:")
_("profile_total_xp", "Total XP:")

_("screen_friends_title", "friends")
_("screen_title_badge_collection", "Gym Badges")
_("screen_title_friend_requests", "Friend Requests")
_("screen_title_news", "News")
_("screen_title_notification", "Notifications")
_("screen_title_pokedex", "POKÉDEX")
_("screen_title_settings", "SETTINGS")

_("team_name_team0", "No Team")
_("team_name_team1", "Team Mystic")
_("team_name_team2", "Team Valor")
_("team_name_team3", "Team Instinct")

_("terms_of_service_url", "https://www.nianticlabs.com/terms/pokemongo/en/")
_("three_strike_policy_url", "https://pokemongo.nianticlabs.com/support/three-strike-policy")
