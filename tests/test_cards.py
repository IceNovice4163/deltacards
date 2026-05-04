from action_results import AttackAftermathResult
from actions import *
from cards import Monster, Spell, card
from effects import Check, For, ForEach, StepResult
from entity import Entity, on_event
from enums import CardKeyword, CardStatusId, CardZone, DamageKind
from game import Game
from modifiers import DamageLayer, IntModifier, ModKind, StatLayer
from targeting import *
from .rig import TestRig


@card(236)
class HotDogVulkin(Monster):
    # Magic: Deal 3 DMG to an opponent.
    magic = Hit(target=OPPONENT, damage=3)


def test_card_hotdogvulkin():
    rig = TestRig.create(p1_deck=[236])

    rig.p1.play_monster(rig.p1.hand[0], slot=0)
    assert rig.p2.obj.hp == rig.p2.obj.max_hp - 3


@card(23)
class Migospel(Monster):
    # Magic: Give a monster +3 HP.
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Buff(target=TARGET, hp=+3)


def test_card_migospel():
    rig = TestRig.create(p1_deck=[1, 23])

    dummy = rig.p1.hand[0]
    migospel = rig.p1.hand[1]

    rig.p1.play_monster(dummy, slot=0)
    rig.p1.play_monster(migospel, slot=1, target=dummy)

    assert dummy.hp == dummy.base.hp + 3


@card(129)
class Knife(Spell):
    # Kill a monster. Deal its COST as DMG to you.
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Kill(target=TARGET) >> Hit(target=CONTROLLER, damage=TARGET.cost)


def test_card_knife():
    rig = TestRig.create(p1_deck=[1], p2_deck=[129])

    dummy = rig.p1.hand[0]
    rig.p1.play_monster(dummy, slot=0)
    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0], target=dummy)

    assert dummy.zone is CardZone.DUSTPILE
    assert len(rig.p1.obj.board) == 0
    assert rig.p2.hp == rig.p2.max_hp - dummy.cost


@card(17)
class KnightKnight(Monster):
    # After this attacks and survives, heal this by the amount of DMG dealt.
    @on_event(AttackAftermathResult)
    def on_attack_aftermath(self, res: AttackAftermathResult):
        if res.attacker_id != self.id:
            return None

        if res.attacker_dead:
            return None

        return Heal(target=self, amount=res.damage_to_defender)


def test_card_knightknight():
    rig = TestRig.create(p1_deck=[17], p2_deck=[1, 616])

    attacker = rig.p1.hand[0]
    rig.p1.play_monster(attacker, slot=0)
    rig.p1.end_turn()

    defender = rig.p2.hand[0]
    big_monster = rig.p2.hand[1]
    rig.p2.play_monster(defender, slot=0)
    rig.p2.play_monster(big_monster, slot=1)
    rig.p2.end_turn()

    rig.p1.attack(attacker, defender)
    assert attacker.zone is CardZone.BOARD
    assert attacker.hp == attacker.base.hp

    rig.p1.end_turn()
    rig.p2.end_turn()

    rig.p1.attack(attacker, big_monster)
    assert attacker.zone is CardZone.DUSTPILE


@card(6)
class Vegetoid(Monster):
    # Turn start: Heal 5 HP to you.
    turn_start = Heal(target=CONTROLLER, amount=5)


def test_card_vegetoid():
    rig = TestRig.create(p1_deck=[6])
    rig.p1.obj.hp = 10

    rig.p1.play_monster(rig.p1.hand[0], slot=0)

    rig.p1.end_turn()
    assert rig.p1.obj.hp == 10

    rig.p2.end_turn()
    assert rig.p1.obj.hp == 15


@card(10)
class Ice(Monster):
    # Dust: Paralyze the killer.
    dust = Paralyze(target=KILLER)


def test_card_ice():
    rig = TestRig.create(p1_deck=[10, 10], p2_deck=[616, 616])

    ice_1 = rig.p1.hand[0]
    ice_2 = rig.p1.hand[1]
    rig.p1.play_monster(ice_1, slot=0)
    rig.p1.play_monster(ice_2, slot=1)
    rig.p1.end_turn()

    big_monster_1 = rig.p2.hand[0]
    big_monster_2 = rig.p2.hand[1]
    rig.p2.play_monster(big_monster_1, slot=0)
    rig.p2.play_monster(big_monster_2, slot=1)
    rig.p2.end_turn()

    # Attacker's Dust trigger test
    rig.p1.attack(ice_1, big_monster_1)
    assert ice_1.zone is CardZone.DUSTPILE
    assert big_monster_1.get_status(CardStatusId.PARALYZED) == 2
    rig.p1.end_turn()

    # Defender's Dust trigger test
    rig.p2.attack(big_monster_2, ice_2)
    assert ice_2.zone is CardZone.DUSTPILE
    assert big_monster_2.get_status(CardStatusId.PARALYZED) == 2


@card(26)
class Parsnik(Monster):
    # Magic: Paralyze a monster. If it was already Paralyzed, deal 2 DMG to it.
    res: Var[StepResult] = Var(StepResult)

    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = (
        Paralyze(target=TARGET).store_result(res)
        >> Check(res.success == False).to(Hit(target=TARGET, damage=2))
    )


def test_card_parsnik():
    rig = TestRig.create(p1_deck=[1, 26, 26])

    dummy = rig.p1.hand[0]
    parsnik = rig.p1.hand[1]
    parsnik_2 = rig.p1.hand[2]

    rig.p1.play_monster(dummy, slot=0)
    rig.p1.play_monster(parsnik, slot=1, target=dummy)

    assert dummy.get_status(CardStatusId.PARALYZED) == 2
    assert dummy.hp == dummy.base.hp

    rig.p1.end_turn()
    rig.p2.end_turn()

    assert dummy.get_status(CardStatusId.PARALYZED) == 1

    rig.p1.play_monster(parsnik_2, slot=2, target=dummy)

    assert dummy.get_status(CardStatusId.PARALYZED) == 1
    assert dummy.hp == dummy.base.hp - 2


@card(83)
class Shopping(Spell):
    # Draw 3 cards costing 5 GOLD or less.
    magic = Draw(player=YOU, card=(DECK & (COST <= 5)).first()) * 3


def test_card_shopping():
    rig = TestRig.create(p1_deck=[83, 1, 1, 1, 616, 616])

    assert [c.template.id for c in rig.p1.hand] == [83, 1, 1, 1]
    rig.p1.play_spell(rig.p1.hand[0])
    assert [c.template.id for c in rig.p1.hand] == [1] * 6


@card(400)
class Cogwheel(Monster):
    # Turn end: Send the most expensive card in your hand to your deck and draw a card.
    turn_end = Move(target=HAND >> MAX(COST), zone=CardZone.DECK) >> DrawNext(player=YOU)


def test_card_cogwheel():
    rig = TestRig.create(p1_deck=[400, 1, 616, 1])

    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.id for c in rig.p1.hand] == [1, 616, 1]
    rig.p1.end_turn()
    assert len(rig.p1.hand) == 3
    assert [c.template.id for c in rig.p1.hand][:2] == [1, 1]


@card(552)
class ChangeOfWinds(Spell):
    # Look at the next 2 cards in your deck.
    # Choose one to draw.
    # Send the other to the bottom of your deck.
    # Give them -1 COST.
    magic = Choose(player=YOU, options=DECK[:2]).to(
        Draw(player=YOU, card=CHOICE_SELECTED)
        >> Move(target=CHOICE_NOT_SELECTED, zone=CardZone.DECK, pos='bottom')
        >> Buff(target=CHOICE_SELECTED | CHOICE_NOT_SELECTED, cost=-1)
    )


def test_card_changeofwinds():
    rig = TestRig.create(p1_deck=[552, 1, 1, 1, 616, 1])

    rig.p1.play_spell(rig.p1.hand[0])
    choices = rig.get_choices()
    assert [c.template.id for c in choices] == [616, 1]

    rig.p1.choose([choices[0]])
    assert choices[0].zone is CardZone.HAND
    assert choices[0].cost == choices[0].base.cost - 1
    assert choices[1].zone is CardZone.DECK
    assert choices[1].cost == choices[1].base.cost - 1


@card(246)
class Editor2(Monster):
    # Magic: Look at 5 random monsters and choose one. Add it to your hand.
    magic = Choose(player=YOU, options=DISCOVER(IS_MONSTER & NON_TOKEN, n=5)).to(
        Move(target=CHOICE_SELECTED, zone=CardZone.HAND)
    )


def test_card_editor2():
    rig = TestRig.create(p1_deck=[246, 246, 246])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

        choices = rig.get_choices()
        template_ids = [card.template.id for card in choices]
        assert len(set(template_ids)) == len(template_ids)

        rig.p1.choose([choices[0]])
        assert len(rig.p1.hand) == 4
        assert rig.p1.hand[-1].id == choices[0].id


@card(76)
class Strength(Spell):
    # Give 3 random ally monsters +1/+1
    magic = Buff(target=ALLY_MONSTERS >> RANDOM(3), attack=+1, hp=+1)


def test_card_strength():
    rig = TestRig.create(p1_deck=[76, 1, 1, 1])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[1])

    rig.p1.play_spell(rig.p1.hand[0])

    for m in rig.p1.board:
        if not m:
            continue

        assert m.attack == m.base.attack + 1
        assert m.hp == m.base.hp + 1


@card(73)
class ColdWinter(Spell):
    # Deal 11 DMG randomly split among all enemy monsters. Add a Change Of Winds to your hand for each one that died.
    res: Var[StepResult] = Var(StepResult)
    kill_count: Var[int] = Var(int, default=0)

    magic = For(
        11,
        effect=(
            Hit(target=ENEMY_MONSTERS >> RANDOM(1), damage=1).store_result(res)
            >> Check((res.success == True) & (res.killed == True)).to(
                SetVar(var=kill_count, value=kill_count + 1)
            )
        )
    ) >> For(
        kill_count,
        effect=Move(target=CARD_BY_NAME("ChangeOfWinds") >> GENERATE(), zone=CardZone.HAND)
    )


def test_card_coldwinter():
    rig = TestRig.create(p1_deck=[1, 1, 1], p2_deck=[73])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0])
    # Only one of monsters that were on the board must survive, and that monster must have exactly 1 HP left
    assert sum(1 for m in rig.p1.board if m) == 1
    assert next(m for m in rig.p1.board if m).hp == 1
    assert [c.template.id for c in rig.p2.hand] == [1, 1, 1, 552, 552]


@card(737)
class IceShock(Spell):
    # Deal 2 DMG to a monster. If it kills, Paralyze the adjacent ones.
    res: Var[StepResult] = Var(StepResult)

    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = Hit(target=TARGET, damage=2).store_result(res) >> Check((res.success == True) & (res.killed == True)).to(
        Paralyze(target=ADJACENT(res.target))
    )


def test_card_iceshock():
    rig = TestRig.create(p1_deck=[1, 1, 1], p2_deck=[737])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

    monster = rig.p1.board[1]
    monster.hp_missing = monster.hp - 1

    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0], target=monster)
    assert rig.p1.board[1] is None
    assert isinstance(rig.p1.board[0], Monster)
    assert isinstance(rig.p1.board[2], Monster)
    assert rig.p1.board[0].get_status(CardStatusId.PARALYZED) == 2
    assert rig.p1.board[2].get_status(CardStatusId.PARALYZED) == 2


@card(36)
class SnowdrakesMom(Monster):
    # Delay: Summon a Vegetoid. Give it +1/+1 and TRANSPARENCY if this has any ATK buffs.
    res: Var[StepResult] = Var(StepResult)

    magic = ScheduleDelayEffect(SELF)
    delay = Summon(card=CARD_BY_NAME("Vegetoid") >> GENERATE(), controller=YOU).store_result(res).to(
        Check(SELF.buffs.attack > 0).to(
            Buff(target=res.monster_id, attack=+1, hp=+1)
            >> AddKeyword(target=res.monster_id, keyword=CardKeyword.TRANSPARENCY)
        )
    )


def test_card_snowdrakesmom():
    rig = TestRig.create(p1_deck=[36, 36])

    monster_1 = rig.p1.hand[0]
    monster_2 = rig.p1.hand[1]

    rig.p1.play_monster(monster_1)
    rig.p1.play_monster(monster_2)
    monster_1.buff(attack=+1)
    monster_2.buff(hp=+1)
    assert len(rig.p1.obj.board) == 2

    rig.p1.end_turn()
    assert len(rig.p1.obj.board) == 4

    assert rig.p1.board[2].has_keyword(CardKeyword.TRANSPARENCY)
    assert rig.p1.board[2].buffs.attack == 1
    assert rig.p1.board[2].buffs.max_hp == 1

    assert not rig.p1.board[3].has_keyword(CardKeyword.TRANSPARENCY)
    assert rig.p1.board[3].buffs.attack == 0
    assert rig.p1.board[3].buffs.max_hp == 0


@card(71)
class FrozenEnergy(Spell):
    # Give a monster +2/+2 and HASTE. Delay: If its COST is the same as its base COST, Paralyze it.
    targets = ALLY_MONSTERS | ENEMY_MONSTERS
    magic = (
        Buff(target=TARGET, attack=+2, hp=+2)
        >> AddKeyword(target=TARGET, keyword=CardKeyword.HASTE)
    ).to(
        ScheduleDelayEffect(SELF)
    )
    delay = Check(TARGET.cost == TARGET.base.cost).to(Paralyze(target=TARGET))


def test_card_frozenenergy():
    rig = TestRig.create(p1_deck=[1, 1, 71, 71])

    dummy_1 = rig.p1.hand[0]
    dummy_2 = rig.p1.hand[1]

    rig.p1.play_monster(dummy_1)
    rig.p1.play_monster(dummy_2)
    rig.p1.play_spell(rig.p1.hand[0], target=dummy_1)
    rig.p1.play_spell(rig.p1.hand[0], target=dummy_2)
    dummy_2.buff(cost=+1)
    assert dummy_1.get_status(CardStatusId.PARALYZED) == 0
    assert dummy_2.get_status(CardStatusId.PARALYZED) == 0

    rig.p1.end_turn()
    assert dummy_1.get_status(CardStatusId.PARALYZED) == 2
    assert dummy_2.get_status(CardStatusId.PARALYZED) == 0


@card(62)
class Undyne(Monster):
    # Deal 1 DMG to the lowest HP enemy monster 10 times. Summon a Spear with base stats equal to DMG not dealt.
    damage_not_dealt: Var[int] = Var(int, default=0)

    magic = For(
        10,
        effect=Check(COUNT(ENEMY_MONSTERS) > 0).to(
            Hit(target=ENEMY_MONSTERS >> MIN(HP), damage=1),
            else_=SetVar(var=damage_not_dealt, value=damage_not_dealt + 1)
        )
    ) >> Check(damage_not_dealt > 0).to(
        Summon(card=CARD_BY_NAME("Spear") >> GENERATE(), controller=YOU, attack=damage_not_dealt, hp=damage_not_dealt)
    )


def test_card_undyne():
    rig = TestRig.create(p1_deck=[1, 1], p2_deck=[62])

    for _ in range(2):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_monster(rig.p2.hand[0])

    assert sum(1 for m in rig.p1.board if m) == 0
    assert [m.template.name for m in rig.p2.board if m] == ["Undyne", "Spear"]
    assert rig.p2.board[1].attack == rig.p2.board[1].base.attack == 2
    assert rig.p2.board[1].hp == rig.p2.board[1].base.hp == 2


def test_card_undyne_no_spear_summon():
    rig = TestRig.create(p1_deck=[1, 1, 1], p2_deck=[62])

    for _ in range(3):
        rig.p1.play_monster(rig.p1.hand[0])

    rig.p1.end_turn()

    rig.p2.play_monster(rig.p2.hand[0])

    assert sum(1 for m in rig.p1.board if m) == 1
    assert rig.p1.board[2].hp == 2
    assert [m.template.name for m in rig.p2.board if m] == ["Undyne"]


@card(427)
class KillerCook(Monster):
    # Magic: Add Flour, Eggs and Milk to your hand. Dust: Draw a TOKEN card.
    X: Var[TargetSelector] = Var(TargetSelector)

    magic = ForEach(
        [CARD_BY_NAME("Flour"), CARD_BY_NAME("Eggs"), CARD_BY_NAME("Milk")],
        var=X,
        effect=Move(target=X >> GENERATE(), zone=CardZone.HAND)
    )


def test_card_killercook():
    rig = TestRig.create(p1_deck=[427])

    rig.p1.play_monster(rig.p1.hand[0])
    assert [c.template.name for c in rig.p1.hand] == ["Dummy", "Dummy", "Dummy", "Flour", "Eggs", "Milk"]


@card(923)
class PixelKris(Monster):
    # Has +1 ATK for each missing HP.
    def iter_modifiers(self, game):
        if (self.zone is not CardZone.BOARD) or self.silenced:
            return

        yield IntModifier(
            kind=ModKind.ATTACK,
            layer=StatLayer.ADD,
            source=self,
            description="+1 ATK for each missing HP",
            applies=lambda q: q.monster is self,
            apply=lambda attack, q: attack + self.hp_missing,
        )


def test_card_pixelkris():
    rig = TestRig.create(p1_deck=[923], p2_deck=[923])

    attacker = rig.p1.hand[0]
    rig.p1.play_monster(attacker, slot=0)
    rig.p1.end_turn()

    defender = rig.p2.hand[0]
    rig.p2.play_monster(defender, slot=0)
    rig.p2.end_turn()

    # Base ATK of Pixel Kris is 2
    rig.p1.attack(attacker, defender)

    assert attacker.zone is CardZone.BOARD
    assert attacker.attack == attacker.base.attack + 2
    assert attacker.hp == attacker.base.hp - 2

    assert defender.zone is CardZone.BOARD
    assert defender.attack == defender.base.attack + 2
    assert defender.hp == defender.base.hp - 2


@card(632)
class Trashy(Monster):
    # This has +2 ATK on the enemy turn and takes no DMG while attacking.
    def iter_modifiers(self, game):
        if (self.zone is not CardZone.BOARD) or self.silenced:
            return

        yield IntModifier(
            kind=ModKind.ATTACK,
            layer=StatLayer.ADD,
            source=self,
            description="+2 ATK on the enemy turn",
            applies=lambda q: q.monster is self and game.turn_player.id != self.controller_id,
            apply=lambda attack, q: attack + 2,
        )

        yield IntModifier(
            kind=ModKind.DAMAGE,
            layer=DamageLayer.PREVENT,
            source=self,
            description="Takes no DMG while attacking",
            applies=lambda q: (
                q.target is self
                and q.kind is DamageKind.COMBAT
                and q.combat_attacker is self
            ),
            apply=lambda damage, q: 0,
        )


def test_card_trashy():
    rig = TestRig.create(p1_deck=[632], p2_deck=[632])

    attacker = rig.p1.hand[0]
    rig.p1.play_monster(attacker, slot=0)
    rig.p1.end_turn()

    defender = rig.p2.hand[0]
    rig.p2.play_monster(defender, slot=0)
    rig.p2.end_turn()

    # Base ATK of Trashy is 2
    rig.p1.attack(attacker, defender)

    assert attacker.zone is CardZone.BOARD
    assert attacker.attack == attacker.base.attack
    assert attacker.hp == attacker.base.hp

    assert defender.zone is CardZone.BOARD
    assert defender.attack == defender.base.attack + 2
    assert defender.hp == defender.base.hp - 2


@card(289)
class RedWagon(Monster):
    # Magic: Catch an ally monster. Dust: Release it to your hand with +3/+3.
    card_to_release: Var[Monster] = Var(Monster)

    targets = ALLY_MONSTERS
    magic = Catch(catcher=SELF, card_to_catch=TARGET)
    dust = ReleaseCaughtCard(catcher=SELF, var=card_to_release).to(
        Buff(target=card_to_release, attack=+3, hp=+3)
        >> Move(target=card_to_release, zone=CardZone.HAND, controller=card_to_release.controller)
    )


def test_card_redwagon():
    rig = TestRig.create(p1_deck=[1, 289, 129, 1])

    dummy = rig.p1.hand[0]
    catcher = rig.p1.hand[1]
    knife = rig.p1.hand[2]

    rig.p1.play_monster(dummy)
    rig.p1.play_monster(catcher, target=dummy)

    assert dummy.zone == CardZone.INVALID
    assert catcher.caught_card is not None
    assert catcher.caught_card.template_id == 1
    assert catcher.caught_card.controller_id == dummy.controller_id

    rig.p1.play_spell(knife, target=catcher)

    assert len(rig.p1.obj.board) == 0
    assert [c.template.id for c in rig.p1.hand] == [1, 1]
    assert rig.p1.hand[1].attack == rig.p1.hand[1].base.attack + 3
    assert rig.p1.hand[1].hp == rig.p1.hand[1].base.hp + 3


def test_soul_determination_death_prevention():
    rig = TestRig.create(soul_id='DETERMINATION', p1_deck=[1, 129, 1, 129])
    rig.p1.obj.hp = 1

    dummy = rig.p1.hand[0]
    knife = rig.p1.hand[1]
    dummy_2 = rig.p1.hand[2]
    knife_2 = rig.p1.hand[3]

    rig.p1.play_monster(dummy)
    rig.p1.play_spell(knife, target=dummy)

    assert rig.p1.obj.hp == 5

    # Check that death is prevented only once
    rig.p1.obj.hp = 1
    rig.p1.play_monster(dummy_2)
    rig.p1.play_spell(knife_2, target=dummy_2)

    assert rig.p1.obj.hp == 0
    assert rig.game.game_over == True
    assert rig.game.dead_players == {rig.p1.id}


@card(106)
class TheHeroine(Monster):
    # Magic: Instead of dying, Erase 2 cards in your hand to return with -1/-2 base stats.
    def on_would_die(self, entity: Entity, game: Game, **kwargs):
        hand = game.player(self.controller_id).hand
        if entity.id == self.id and self.base.hp > 2 and len(hand) >= 2:
            return [
                [Erase(target=hand.cards[i]) for i in range(2)]
                + [self.revive]
            ]

        return None

    def revive(self, ctx: 'ActionContext', **kwargs):
        base_attack = self.base.attack
        base_hp = self.base.hp
        pos = self.pos

        self._reset()

        self.pos = pos
        self.set_base_stats(attack=base_attack - 1, hp=base_hp - 2)


def test_theheroine_death_prevention_on_kill():
    rig = TestRig.create(p1_deck=[106, 129, 1, 1])

    monster = rig.p1.hand[0]
    knife = rig.p1.hand[1]

    base_attack = monster.base.attack
    base_hp = monster.base.hp

    rig.p1.play_monster(monster, slot=3)
    rig.p1.play_spell(knife, target=monster)

    assert monster.zone == CardZone.BOARD
    assert monster.pos == 3
    assert monster.base.attack == base_attack - 1
    assert monster.base.hp == base_hp - 2
    assert len(rig.p1.hand) == 0


def test_theheroine_death_prevention_on_combat_damage():
    rig = TestRig.create(p1_deck=[106, 1, 1, 1], p2_deck=[616])

    monster = rig.p1.hand[0]

    base_attack = monster.base.attack
    base_hp = monster.base.hp

    rig.p1.play_monster(monster, slot=3)
    rig.p1.end_turn()

    big_monster = rig.p2.hand[0]
    rig.p2.play_monster(big_monster)
    rig.p2.end_turn()

    rig.p1.attack(monster, big_monster)

    assert monster.zone == CardZone.BOARD
    assert monster.pos == 3
    assert monster.base.attack == base_attack - 1
    assert monster.base.hp == base_hp - 2
    assert len(rig.p1.hand) == 2


def test_theheroine_death_prevention_failure():
    rig = TestRig.create(p1_deck=[106, 129, 1, 1])

    monster = rig.p1.hand[0]
    knife = rig.p1.hand[1]
    dummy = rig.p1.hand[2]

    rig.p1.play_monster(monster, slot=3)
    rig.p1.play_monster(dummy)
    rig.p1.play_spell(knife, target=monster)

    assert monster.zone == CardZone.DUSTPILE
    assert len(rig.p1.hand) == 1


def test_preservation_overdraw_prevention():
    rig = TestRig.create(p1_artifacts=[11], p1_deck=[83, 83, 83, 1], p2_deck=[83, 83, 83, 1])

    rig.p1.play_spell(rig.p1.hand[0])
    assert len(rig.p1.hand) == 6
    assert len(rig.p1.deck) == 18

    rig.p1.play_spell(rig.p1.hand[0])
    assert len(rig.p1.hand) == 7
    assert len(rig.p1.deck) == 16

    rig.p1.play_spell(rig.p1.hand[0])
    assert len(rig.p1.hand) == 7
    assert len(rig.p1.deck) == 15

    rig.p1.end_turn()

    rig.p2.play_spell(rig.p2.hand[0])
    assert len(rig.p2.hand) == 6
    assert len(rig.p2.deck) == 18

    rig.p2.play_spell(rig.p2.hand[0])
    assert len(rig.p2.hand) == 7
    assert len(rig.p2.deck) == 15
