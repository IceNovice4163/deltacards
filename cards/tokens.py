from typing import TYPE_CHECKING

from actions import *
from conditions import *
from cards import TargetsEnum, Monster, Spell, card, create_card
from entity import on_event
from targeting import *

if TYPE_CHECKING:
    from ..player import Player
    from ..game import Game


@card(576)
class Shield(Spell):
    targets = TargetsEnum.ALLY_MONSTER,
    magic = Buff(target=TARGET, attack=1, hp=1), DrawNext(target=OWNER)
