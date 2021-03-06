from django.core import validators
from django.utils.translation import pgettext_lazy

PokemonGoUsernameValidator = validators.RegexValidator(
    r"^[A-Za-z0-9]{3,15}$",
    pgettext_lazy("codename__error", "Only letters and numbers are allowed."),
    "invalid",
)

FriendCodeValidator = validators.RegexValidator(
    r"(\d{4}[\s\-]?){3}",
    pgettext_lazy(
        "friend_code__error",
        "Trainer Code must be 12 digits long and contain only numbers and whitespace.",
    ),
    "invalid",
)

username_validator = [PokemonGoUsernameValidator]
