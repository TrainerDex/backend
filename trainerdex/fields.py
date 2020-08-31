from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Iterable, Tuple, Optional


class PogoPositiveIntegerField(models.PositiveIntegerField):
    def __init__(
        self,
        reversable: bool = False,
        sortable: bool = False,
        levels: Iterable[Tuple[str, int]] = [
            (_("Bronze"), 10),
            (_("Silver"), 50),
            (_("Gold"), 200),
        ],
        badge_id: Optional[int] = None,
        translation_ref: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.reversable = reversable
        self.sortable = sortable
        self.levels = levels
        self.badge_id = badge_id
        self.translation_ref = translation_ref


class PogoDecimalField(models.DecimalField):
    def __init__(
        self,
        reversable: bool = False,
        sortable: bool = False,
        levels: Iterable[Tuple[str, Decimal]] = [
            (_("Bronze"), 10),
            (_("Silver"), 50),
            (_("Gold"), 200),
        ],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.reversable = reversable
        self.sortable = sortable
        self.levels = levels
