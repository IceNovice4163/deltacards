from deltacards.dsl.api import *


@card(3)
class Whimsun(Monster):
    magic = Buff(target=SELF, attack=COUNT(ALLY_MONSTERS & ~SELF))


@card(5)
class Migosp(Monster):
    magic = Buff(target=ADJACENT(SELF), hp=+1)


@card(6)
class Vegetoid(Monster):
    turn_start = Heal(target=CONTROLLER, amount=5)


@card(10)
class Ice(Monster):
    dust = Paralyze(target=KILLER)


@card(11)
class Snowdrake(Monster):
    targets = ALLY_MONSTERS
    magic = Buff(target=TARGET, attack=+2)


@card(13)
class Woshua(Monster):
    magic = Buff(target=ENEMY_MONSTERS, attack=-1)


@card(16)
class Madjick(Monster):
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = SwapStats(target=TARGET)


@card(20)
class Vulkin(Monster):
    targets = YOU | OPPONENT | ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Hit(target=TARGET, damage=2)


@card(22)
class Shyren(Monster):
    targets = YOU | OPPONENT | ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Heal(target=TARGET, amount=4)


@card(44)
class Gyftrot(Monster):
    magic = DrawNext(player=CONTROLLER)


@card(144)
class ScarfMouse(Monster):
    targets = ENEMY_MONSTERS
    magic = Silence(target=TARGET)


@card(147)
class FukuFire(Monster):
    magic = Hit(target=FRONT, damage=3)


@card(176)
class UglyFish(Monster):
    targets = ENEMY_MONSTERS
    magic = Move(target=TARGET, zone=CardZone.HAND)


@card(225)
class FishingRod(Monster):
    turn_end = DrawNext(player=CONTROLLER)


@card(235)
class DadSlime(Monster):
    dust = Summon(card=CARD_BY_NAME("KidSlime") >> GENERATE(), controller=YOU) * 2


@card(72)
class Melt(Spell):
    targets = ALLY_MONSTERS
    magic = Hit(target=FRONT(TARGET), damage=TARGET.hp)


@card(76)
class Strength(Spell):
    magic = Buff(target=ALLY_MONSTERS >> RANDOM(n=2), attack=+1, hp=+1)


@card(83)
class Shopping(Spell):
    magic = Draw(player=YOU, card=(DECK & (COST <= 5)).first()) * 3


@card(86)
class Worsening(Spell):
    magic = HalveStats(target=ENEMY_MONSTERS & HAS_KEYWORD(KR), round_up=False)


@card(96)
class Punishment(Spell):
    targets = ENEMY_MONSTERS
    magic = Check(YOU & SPENT_GOLD_LAST_TURN).to(
        Hit(target=TARGET, damage=4),
        else_=Hit(target=TARGET, damage=3)
    )


@card(129)
class Knife(Spell):
    targets = ENEMY_MONSTERS
    magic = Kill(target=TARGET).to(Hit(target=CONTROLLER, damage=TARGET.cost))


@card(132)
class Pie(Spell):
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Heal(target=TARGET, amount=TARGET.max_hp)
