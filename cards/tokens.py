from actions import *
from cards import Monster, Spell, card
from enums import CardZone
from targeting import *


@card(351)
class GasterBlaster(Spell):
    targets = YOU | ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Hit(target=TARGET, damage=8)


@card(360)
class LostToriel(Monster):
    dust = Buff(target=RANDOM(ENEMY_MONSTERS), attack=-3)


@card(361)
class LostAsgore(Monster):
    dust = Hit(target=RANDOM(ENEMY_MONSTERS & DAMAGED), damage=4)


@card(362)
class LostSans(Monster):
    dust = Move(target=CARD_BY_NAME("GasterBlaster") >> GENERATE(), zone=CardZone.HAND)


@card(363)
class LostPapyrus(Monster):
    dust = Heal(target=RANDOM(ALLY_MONSTERS & DAMAGED), amount=3) >> Heal(target=CONTROLLER, amount=3)


@card(364)
class LostUndyne(Monster):
    dust = Hit(target=MIN(ENEMY_MONSTERS, TARGET.hp), damage=2)


@card(365)
class LostAlphys(Monster):
    dust = Buff(target=MAX(HAND, TARGET.cost), cost=-2)


@card(552)
class ChangeOfWinds(Spell):
    magic = Choose(player=YOU, options=DECK[:2]).to(
        Draw(player=YOU, card=CHOICE_SELECTED)
        >> Move(target=CHOICE_NOT_SELECTED, zone=CardZone.DECK, pos='bottom')
        >> Buff(target=CHOICE_SELECTED | CHOICE_NOT_SELECTED, cost=-1)
    )


@card(576)
class Shield(Spell):
    targets = ALLY_MONSTERS
    magic = Buff(target=TARGET, attack=1, hp=1) >> DrawNext(player=CONTROLLER)


LOST_SOULS = (LostAlphys, LostPapyrus, LostUndyne, LostToriel, LostAsgore, LostSans)
