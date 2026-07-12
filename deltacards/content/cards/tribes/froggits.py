from deltacards.dsl.api import *


FROGGIT = HAS_TRIBE(Tribe.FROGGIT)


@card(24)
class FinalFroggit(Monster):
    magic = (
        (BOARD | HAND | DECK) & FROGGIT & (TEMPLATE_ID != SELF.template_id)
    ).buff(attack=+1, hp=+1)


@card(494)
class JumpingFrog(Monster):
    targets = ENEMY_MONSTERS

    magic = TARGET.hit(SELF.attack)


@card(803)
class SidewalkFroggit(Monster):
    magic = SELF.schedule_delay_effect()

    delay = LOOP_COPY.buff(
        attack=SELF.buffs.attack,
        hp=SELF.buffs.max_hp
    )


@card(817)
class GigaFroggit(Monster):
    magic = Switch(
        left=(ALLY_MONSTERS & FROGGIT & ~SELF).add_keyword(TAUNT),
        right=(ALLY_MONSTERS & FROGGIT & ~SELF).add_keyword(ARMOR)
    )


@card(889)
class Ribbick(Monster):
    targets = ALLY_MONSTERS

    magic = (
        TARGET.hit(2)
        >> TARGET.buff(attack=+2)
        >> TARGET.add_keyword(HASTE)
    )
