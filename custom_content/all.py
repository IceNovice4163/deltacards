from deltacards.dsl.api import *


@card(
    1_000_001,
    name="Rainy Kid",
    description=(
        "{{KW:MAGIC}}: Give the lowest {{COST}} non-{{RARITY:TOKEN}} spell in your hand +1 {{KW:LOOP}}. "
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=1,
    attack=2,
    hp=1,
    image=CustomImage("images/Rainy_Kid.png"),
    localizations={
        'en': LocalizedText(
            name="Rainy Kid{{PLURAL:$1||s}}",
        ),
    },
)
class RainyKid(Monster):
    spell: Var[Card] = Var(Card)

    magic = (
        SetVar(
            var=spell,
            value=(HAND & IS_SPELL & NON_TOKEN) >> MIN(COST),
        )
        >> spell.set_status(LOOP, value=spell.status(LOOP) + 1)
    )


@card(
    1_000_002,
    name="Wireframe Queen",
    description=(
        "{{KW:TURN_END}}: If your hand is full, give the highest {{COST}} card in your hand -4 {{COST}}. "
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=5,
    attack=4,
    hp=6,
    image=CustomImage("images/Queen_Wireframe.png"),
    localizations={
        'en': LocalizedText(
            name="Wireframe Queen{{PLURAL:$1||s}}",
        ),
    },
)
class WireframeQueen(Monster):
    turn_end = Check(
        COUNT(HAND) == 7
    ).to(
        (HAND >> MAX(COST)).buff(cost=-4)
    )


@card(
    1_000_003,
    name="Chef Ralsei",
    description=(
        "{{KW:SHOCK}}: Give the target +2 {{HP}}. If there's no target alive, gain +2 {{HP}} instead. {{KW:MAGIC}}: Add a {{CARD:132|1}} to your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=4,
    hp=3,
    image=CustomImage("images/Chef_Ralsei.png"),
    localizations={
        'en': LocalizedText(
            name="Chef Ralsei{{PLURAL:$1||s}}",
        ),
    },
)
class ChefRalsei(Monster):
    magic = (
        GENERATE_CARD("Pie").to_hand()
    )

    shock = Check(
        EXISTS(TARGET)
    ).to(
        Check(
            ~TARGET.dead
        ).to(
            TARGET.buff(hp=+2),
            else_=SELF.buff(hp=+2)
        ),
        else_=SELF.buff(hp=+2)
    )


@card(
    1_000_004,
    name="Platswap Statue",
    description=(
        "After you spend {{GOLD}} on spells, regain this {{KW:SUPPORT}}. {{KW:SUPPORT}}: Earn 1 {{GOLD}} and lose this {{KW:SUPPORT}}."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=3,
    hp=4,
    image=CustomImage("images/Platswap_Statue.png"),
    localizations={
        'en': LocalizedText(
            name="Platswap Statue{{PLURAL:$1||s}}",
        ),
    },
)
class PlatswapStatue(Monster):
    @on_event(SpellCastResult)
    def on_spell_cast(self, res: SpellCastResult, game, **kwargs):
        if res.player_id != self.controller_id:
            return None

        if res.card.cost < 1:
            return None

        return SELF.toggle_ability(SUPPORT, True)

    support = (
        YOU.earn_gold(1)
        >> SELF.toggle_ability(SUPPORT, False)
    )


@card(
    1_000_005,
    name="Ralseicoaster",
    description=(
        "{{KW:HASTE}}. After an ally monster attacks, heal 1 {{HP}} to all allies."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=3,
    hp=3,
    keywords=HASTE,
    image=CustomImage("images/Ralseicoaster.png"),
    localizations={
        'en': LocalizedText(
            name="Ralseicoaster{{PLURAL:$1||s}}",
        ),
    },
)
class Ralseicoaster(Monster):
    @on_event(AttackResolvedResult)
    def on_attack_resolved(self, res: AttackResolvedResult, game, **kwargs):
        if res.attacker.controller_id != self.controller_id:
            return None
        
        if res.attacker_id == self.id and res.attacker_dead:
            return None

        return ALLIES.heal(1)


@card(
    1_000_006,
    name="Quiz Vortex",
    description=(
        "{{KW:MAGIC}}: Enchant an ally slot with {{ENCHANT:QUIZ_SHOW|1}}."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=3,
    hp=3,
    image=CustomImage("images/Quiz_Vortex.png"),
    localizations={
        'en': LocalizedText(
            name="Quiz Vortex{{PLURAL:$1||es}}",
        ),
    },
)
class QuizVortex(Monster):
    targets = ALLY_SLOTS

    magic = TARGET.enchant(
        ENCHANTMENT_BY_NAME('quiz-show')
    )


@enchantment(
    'quiz-show',
    name="Quiz Show",
    description="Starts with 3 counters. After you play a monster here and have 0 {{GOLD}}, give it {{STATS:+1|+1}} and lose a counter. At 0 counters, draw 2 cards and this effect expires.",
    image=ExistingImage("O"),
    overlay=ExistingImage("O"),
    initial_counter=3,
    localizations={
        'en': LocalizedText(
            name="Quiz Show{{PLURAL:$1||s}}",
        ),
    },
)
class QuizShow(Enchantment):
    initial_counter = 3

    @on_event(MonsterSummonedResult)
    def on_monster_summoned(self, res: MonsterSummonedResult, game, **kwargs):
        if not res.is_played:
            return None

        if res.monster.slot_id != self.slot_id:
            return None

        if game.players[self.controller_id].gold != 0:
            return None

        return (
            RESOLVE_ENTITY(res.monster_id).buff(attack=+1, hp=+1)
            >> SELF.update_enchantment_counter(-1)
            >> Check(SELF.counter == 0).to(
                (YOU.draw_next() * 2)
                >> SELF.expire_enchantment()
            )
        )


@card(
    1_000_007,
    name="Nurse Susie",
    description=(
        "{{KW:MAGIC}}: Deal 1 {{DMG}} to all other ally monsters twice. "
        "{{KW:BULLSEYE}}: If it's a non-{{RARITY:DETERMINATION}} ally, summon a copy of it with {{STATS:+1|+1}}."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=3,
    hp=7,
    image=CustomImage("images/Nurse_Susie.png"),
    localizations={
        'en': LocalizedText(
            name="Nurse Susie{{PLURAL:$1||s}}",
        ),
    },
)
class NurseSusie(Monster):
    copied_card: Var[Card] = Var(Card)

    magic = (ALLY_MONSTERS & ~SELF).hit(1) * 2

    bullseye = Check(
        TARGET & NON_DT
    ).to(
        Check(
            TARGET.controller_id == YOU.id
        ).to(
            SetVar(
                var=copied_card,
                value=(TARGET >> COPY()),
            ) >> copied_card.summon()
            >> copied_card.buff(attack=+1, hp=+1)
        )
    )


@card(
    1_000_008,
    name="Mouse Train",
    description=(
        "{{KW:MAGIC}}: Summon 2 random 1-{{COST}} monsters from your hand."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=3,
    hp=4,
    image=CustomImage("images/Mouse_Train.png"),
    localizations={
        'en': LocalizedText(
            name="Mouse Train{{PLURAL:$1||s}}",
        ),
    },
)
class MouseTrain(Monster):
    magic = (
        (HAND & IS_MONSTER & (COST == 1)) >> RANDOM(2)
    ).summon()


@card(
    1_000_009,
    name="Ferroll",
    description=(
        "{{KW:MAGIC}}: Deal 1 {{DMG}} to all other ally monsters. "
        "Earn 1 {{GOLD}} for each one that survived."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=5,
    attack=5,
    hp=5,
    image=CustomImage("images/Ferroll.png"),
    localizations={
        'en': LocalizedText(
            name="Ferroll{{PLURAL:$1||s}}",
        ),
    },
)
class Ferroll(Monster):
    damaged_cards: Var[TargetSelector] = Var(TargetSelector)
    monster: Var[Card] = Var(Monster)

    magic = (
        SetVar(
            var=damaged_cards,
            value=(ALLY_MONSTERS & ~SELF),
        ) >> damaged_cards.hit(1)
        >> ForEach(
            damaged_cards,
            var = monster,
            effect = Check(
                ~monster.dead
            ).to(
                YOU.earn_gold(1)
            )
        )
    )


@card(
    1_000_010,
    name="Pixel Bluebird",
    description=(
        "{{KW:NEED}}: You played a {{RARITY:TOKEN}} card with a base {{COST}} of 3+ {{GOLD}} this turn. "
        "{{KW:MAGIC}}: Add a {{CARD:1000011|1}} to your hand."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=3,
    hp=3,
    image=CustomImage("images/Pixel_Bluebird.png"),
    localizations={
        'en': LocalizedText(
            name="Pixel Bluebird{{PLURAL:$1||s}}",
        ),
    },
)
class PixelBluebird(Monster):
    need = EXISTS(
        CARDS_PLAYED(player=YOU, scope=THIS_TURN)
        & (BASE_COST >= 3)
        & TOKEN
    )

    magic = GENERATE_CARD("Pixel Crystal").to_hand()


@card(
    1_000_011,
    name="Pixel Crystal",
    description=(
        "{{KW:TAUNT}}. {{KW:MAGIC}}: {{KW:PARALYZE}} a monster. "
        "{{KW:DUST}}: Deal 2 {{DMG}} to all enemy monsters."
    ),
    rarity=CardRarity.TOKEN,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=3,
    hp=3,
    keywords=TAUNT,
    image=CustomImage("images/Pixel_Crystal.png"),
    localizations={
        'en': LocalizedText(
            name="Pixel Crystal{{PLURAL:$1||s}}",
        ),
    },
)
class PixelCrystal(Monster):
    targets = ALL_MONSTERS

    magic = TARGET.paralyze()
    dust = ENEMY_MONSTERS.hit(2)


@card(
    1_000_012,
    name="Spaceship Frog",
    description=(
        "{{KW:MAGIC}} and {{KW:SUPPORT}}: Deal 1 {{DMG}} to the monster in front of this. "
        "{{KW:BULLSEYE}}: Add a {{CARD:196|1}} to your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.UTY,
    cost=2,
    attack=1,
    hp=3,
    tribes=[Tribe.FROGGIT],
    image=CustomImage("images/Spaceship_Frog.png"),
    localizations={
        'en': LocalizedText(
            name="Spaceship Frog{{PLURAL:$1||s}}",
        ),
    },
)
class SpaceshipFrog(Monster):
    _effect = FRONT(SELF).hit(1)

    magic = _effect
    support = _effect
    bullseye = (
        GENERATE_CARD("Tiny Froggit").to_hand()
    )


@card(
    1_000_013,
    name="Honeydew Keeper",
    description=(
        "{{KW:MAGIC}}: Give a monster and its adjacent monsters in your hand +2 {{HP}}."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.UTY,
    cost=3,
    attack=2,
    hp=3,
    image=CustomImage("images/Honeydew_Keeper.png"),
    localizations={
        'en': LocalizedText(
            name="Honeydew Keeper{{PLURAL:$1||s}}",
        ),
    },
)
class HoneydewKeeper(Monster):
    targets = HAND & IS_MONSTER

    magic = (
        TARGET.buff(hp=+2)
        >> Check(LEFT_IN_HAND(TARGET) & IS_MONSTER).to(
            LEFT_IN_HAND(TARGET).buff(hp=+2)
        )
        >> Check(RIGHT_IN_HAND(TARGET) & IS_MONSTER).to(
            RIGHT_IN_HAND(TARGET).buff(hp=+2)
        )
    )


@card(
    1_000_014,
    name="Maus Box",
    description=(
        "{{KW:MAGIC}}: Summon 3 {{CARD:617|3}} with {{KW:HASTE}}. "
        "Add any not summoned to your hand with +2 {{ATK}}."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=9,
    attack=6,
    hp=6,
    image=CustomImage("images/Maus_Box.png"),
    localizations={
        'en': LocalizedText(
            name="Maus Box{{PLURAL:$1||es}}",
        ),
    },
)
class MausBox(Monster):
    generated_card: Var[Card] = Var(Card)

    _effect = (
        SetVar(var=generated_card, value=GENERATE_CARD("Maus"))
        >> generated_card.add_keyword(HASTE)
    )
    
    magic = (
        For(
            3,
            _effect
            >> Check(COUNT(ALLY_MONSTERS) < 4).to(
                (generated_card.summon()),
                else_=(
                    generated_card.buff(attack=+2)
                    >> generated_card.to_hand()
                )
            )
        )
    )


@card(
    1_000_015,
    name="Farmer Shi",
    description=(
        "{{KW:NEED}}: 2+ unique ally 0-{{COST}} monsters. "
        "{{KW:MAGIC}}: Add a copy of each ally 0-{{COST}} monster to your hand with {{STATS:+1|+1}}."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=2,
    attack=2,
    hp=3,
    image=CustomImage("images/Farmer_Shi.png"),
    localizations={
        'en': LocalizedText(
            name="Farmer Shi",
        ),
    },
)
class FarmerShi(Monster):
    monster: Var[Card] = Var(Monster)
    generated_card: Var[Card] = Var(Card)

    need = COUNT_DISTINCT(
        (ALLY_MONSTERS | SELF) & (COST == 0),
        TEMPLATE_ID
    ) >= 2

    magic = (
        ForEach(
            ALLY_MONSTERS,
            var = monster,
            effect = Check(
                monster.cost == 0
            ).to(
                SetVar(var=generated_card, value=monster >> COPY())
                >> generated_card.buff(attack=+1, hp=+1)
                >> generated_card.to_hand()
            )
        )
    )


@card(
    1_000_016,
    name="Virus",
    description=(
        "After you take {{DMG}} during your turn, add a {{CARD:516|1}} to your hand. "
        "{{KW:MAGIC}}: Deal 2 {{DMG}} to you."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=1,
    attack=1,
    hp=2,
    image=CustomImage("images/Virus.png"),
    localizations={
        'en': LocalizedText(
            name="Virus{{PLURAL:$1||es}}",
        ),
    },
)
class Virus(Monster):
    magic = YOU.hit(2)

    @on_event(EntityDamagedResult)
    def on_entity_damaged(self, res: EntityDamagedResult, game, **kwargs):
        if game.turn_player.id != self.controller_id:
            return None

        if res.target_id != self.controller_id:
            return None

        return GENERATE_CARD("Breaking Love").to_hand()


@card(
    1_000_017,
    name="Puzzle Piece",
    description=(
        "{{KW:MAGIC}}: Give an ally monster {{STATS:+1|+1}}."
    ),
    rarity=CardRarity.BASE,
    expansion=Expansion.DELTARUNE,
    cost=1,
    attack=1,
    hp=1,
    image=CustomImage("images/Jigsaw_Piece.png"),
    localizations={
        'en': LocalizedText(
            name="Puzzle Piece{{PLURAL:$1||s}}",
        ),
    },
)
class PuzzlePiece(Monster):
    targets = ALLY_MONSTERS

    magic = TARGET.buff(attack=+1, hp=+1)


@card(
    1_000_018,
    name="Twirl Flower",
    description=(
        "{{KW:MAGIC}}: Draw 2 cards and give them -1 {{COST}}. "
        "{{KW:DUST}}: {{KW:ERASE}} the rightmost card in your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=4,
    hp=3,
    tribes=[Tribe.PLANT],
    image=CustomImage("images/Twirl_Flower.png"),
    localizations={
        'en': LocalizedText(
            name="Twirl Flower{{PLURAL:$1||s}}",
        ),
    },
)
class TwirlFlower(Monster):
    drawn_card: Var[Card] = Var(Card)

    magic = (
        For(
            2,
            (
                SetVar(var=drawn_card, value=DECK.first())
                >> YOU.draw(drawn_card).to(
                    drawn_card.buff(cost=-1)
                )
            )
        )
    )

    dust = HAND.last().erase()


@card(
    1_000_019,
    name="Ed",
    description=(
        "{{KW:ARMOR}}. {{KW:MAGIC}}: Make an enemy monster {{KW:WANTED}}. "
        "Attack all enemy {{KW:WANTED}} monsters (from lowest to highest {{ATK}})."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.UTY,
    cost=10,
    attack=5,
    hp=8,
    keywords=ARMOR,
    image=CustomImage("images/Ed.png"),
    localizations={
        'en': LocalizedText(
            name="Ed{{PLURAL:$1||s}}",
        ),
    },
)
class Ed(Monster):
    targets = ENEMY_MONSTERS
    attack_targets: Var[TargetSelector] = Var(TargetSelector)
    next_target: Var[Card] = Var(Monster)

    magic = (
        TARGET.add_keyword(WANTED)
        >> SetVar(
            var=attack_targets,
            value=(
                (ENEMY_MONSTERS & HAS_KEYWORD(WANTED))
                >> MIN(ATTACK)
            )
        )
        >> For(
            3,
            (
                SetVar(
                    var=next_target,
                    value=(
                        (ENEMY_MONSTERS & HAS_KEYWORD(WANTED) & ~attack_targets)
                        >> MIN(ATTACK)
                    )
                )
                >> SetVar(
                    var=attack_targets,
                    value=(attack_targets | next_target)
                )
            )
        )
        >> SELF.force_attack(attack_targets)
    )


@card(
    1_000_020,
    name="Red",
    description=(
        "{{KW:MAGIC}}: {{KW:ERASE}} a card and any to its left in your hand. "
        "Add that many {{CARD:1000021|2}} to your hand."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.UTY,
    cost=5,
    attack=6,
    hp=4,
    tribes=[Tribe.ROYAL_GUARD],
    image=CustomImage("images/Red.png"),
    localizations={
        'en': LocalizedText(
            name="Red{{PLURAL:$1||s}}",
        ),
    },
)
class Red(Monster):
    targets = HAND
    erase_targets: Var[TargetSelector] = Var(TargetSelector)
    next_target: Var[Card] = Var(Card)

    magic = (
        SetVar(
            var=erase_targets,
            value=TARGET
        )
        >> SetVar(
            var=next_target,
            value=TARGET
        )
        >> For(
            6,
            (
                Check(LEFT_IN_HAND(next_target)).to(
                    SetVar(
                        var=next_target,
                        value=LEFT_IN_HAND(next_target)
                    )
                    >> SetVar(
                        var=erase_targets,
                        value=(erase_targets | next_target)
                    )
                )
            )
        )
        >> ForEach(
            erase_targets,
            var = next_target,
            effect = (
                next_target.erase()
                >> GENERATE_CARD("Sawblade").to_hand()
            )
        )
    )


@card(
    1_000_021,
    name="Sawblade",
    description=(
        "{{KW:MAGIC}}: {{KW:SWITCH}}: "
        "{{SWITCH_LEFT:1|Deal 2 {{DMG}}}} or {{SWITCH_RIGHT:1|Gain +2 {{HP}} and draw a card}}."
    ),
    rarity=CardRarity.TOKEN,
    expansion=Expansion.UTY,
    cost=2,
    attack=2,
    hp=2,
    image=CustomImage("images/Sawblade.png"),
    localizations={
        'en': LocalizedText(
            name="Sawblade{{PLURAL:$1||s}}",
        ),
    },
)
class Sawblade(Monster):
    targets = ALLIES | ENEMIES

    magic = Switch(
        left=TARGET.hit(2),
        right=(
            SELF.buff(hp=+2)
            >> YOU.draw_next()
        )
    )


@card(
    1_000_022,
    name="Verse Sans",
    description=(
        "{{KW:DODGE}} (1). "
        "{{KW:MAGIC}}: Enchant all other unenchanted slots with {{ENCHANT:TREADMILL|2}}."
    ),
    rarity=CardRarity.LEGENDARY,
    expansion=Expansion.BASE,
    cost=3,
    attack=1,
    hp=1,
    statuses={
        DODGE: 1,
    },
    image=CustomImage("images/Casual_Sans.png"),
    localizations={
        'en': LocalizedText(
            name="Verse Sans{{PLURAL:$1||es}}",
        ),
    },
)
class VerseSans(Monster):
    magic = (
        (ENEMY_SLOTS | ALLY_SLOTS)
        & UNENCHANTED_SLOT
        & ~SLOT_OF(SELF)
    ).enchant(
        ENCHANTMENT_BY_NAME('treadmill')
    )


@enchantment(
    'treadmill',
    name="Treadmill",
    description="After you play a monster here (except {{CARD:1000022|1}}), move it 1 slot to the left and this effect expires. If it can't move to the left, send it to the top of your deck instead and set its {{COST}} to 3 (max. -6 {{COST}}).",
    image=ExistingImage("A"),
    overlay=ExistingImage("A"),
    localizations={
        'en': LocalizedText(
            name="Treadmill{{PLURAL:$1||s}}",
        ),
    },
)
class Treadmill(Enchantment):
    _effect = (
        THIS_SLOT_MONSTER.to_deck(pos='top')
        >> Check(DECK.first() & (COST <= 9)).to(
            DECK.first().set_stats(cost=3),
            else_=DECK.first().buff(cost=-6)
        )
        >> SELF.expire_enchantment()
    )

    @on_event(MonsterSummonedResult)
    def on_monster_summoned(self, res: MonsterSummonedResult, game, **kwargs):
        if not res.is_played:
            return None

        if res.monster.slot_id != self.slot_id:
            return None

        if res.monster.template.name == "Verse Sans":
            return None

        return (
            Check(
                LEFT_OF(THIS_SLOT_MONSTER) & ADJACENT(THIS_SLOT_MONSTER)
            ).to(
                self._effect,
                else_=(
                    THIS_SLOT_MONSTER.summon(pos=(SLOT_OF(SELF).pos - 1))
                    >> SELF.expire_enchantment()
                    >> Check(THIS_SLOT_MONSTER).to(
                        self._effect
                    )
                )
            )
        )


@card(
    1_000_023,
    name="Gramophone",
    description=(
        "{{KW:SHOCK}}: Lose this {{KW:SHOCK}}. "
        "Deal 1 {{DMG}} to all enemy monsters. "
        "{{KW:BULLSEYE}}: Regain this {{KW:SHOCK}}."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=2,
    attack=1,
    hp=3,
    image=CustomImage("images/The_Jitterbuggerer.png"),
    localizations={
        'en': LocalizedText(
            name="Gramophone{{PLURAL:$1||s}}",
        ),
    },
)
class Gramophone(Monster):
    shock = (
        SELF.toggle_ability(SHOCK, False)
        >> ENEMY_MONSTERS.hit(1)
    )

    bullseye = (
        SELF.toggle_ability(SHOCK, True)
    )


@card(
    1_000_024,
    name="Server Kris",
    description=(
        "{{KW:MAGIC}}: Heal 2 {{HP}} to all damaged monsters. "
        "Earn 1 {{GOLD}} for each enemy healed."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=5,
    hp=7,
    image=CustomImage("images/Server_Kris.png"),
    localizations={
        'en': LocalizedText(
            name="Server Kris{{PLURAL:$1||es}}",
        ),
    },
)
class ServerKris(Monster):
    magic = (
        YOU.earn_gold(COUNT(ENEMY_MONSTERS & DAMAGED))
        >> (ALL_MONSTERS & DAMAGED).heal(2)
    )


@card(
    1_000_025,
    name="Signery",
    description=(
        "{{KW:NEED}}: You spent {{GOLD}} on 2+ unique spells this turn. "
        "{{KW:MAGIC}}: Give a spell in your hand -3 {{COST}}."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=3,
    hp=3,
    image=CustomImage("images/Signery.png"),
    localizations={
        'en': LocalizedText(
            name="Signer{{PLURAL:$1|y|ies}}",
        ),
    },
)
class Signery(Monster):
    targets = HAND & IS_SPELL

    need = COUNT_DISTINCT(
        (
            CARDS_PLAYED(player=YOU, scope=THIS_TURN)
            & (COST >= 1)
            & IS_SPELL
        ),
        TEMPLATE_ID
    ) >= 2

    magic = TARGET.buff(cost=-3)
    
@card(
    1_000_026,
    name="Kooby",
    description=(
        "{{KW:DUST}}: The current turn player spends 2 {{GOLD}} to summon 2 {{CARD:375|2}} with +1 {{ATK}}."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=5,
    hp=4,
    tribes=[Tribe.PLANT],
    image=CustomImage("images/Kooby.png"),
    localizations={
        'en': LocalizedText(
            name="Koob{{PLURAL:$1|y|ies}}",
        ),
    },
)
class Kooby(Monster):
    generated_card: Var[Card] = Var(Card)

    dust = TURN_PLAYER.spend_gold(2).to(
        SetVar(var=generated_card, value=GENERATE_CARD("Green Clover", controller=TURN_PLAYER))
        >> generated_card.buff(attack=+1)
        >> generated_card.summon(controller=TURN_PLAYER)
        >> SetVar(var=generated_card, value=GENERATE_CARD("Green Clover", controller=TURN_PLAYER))
        >> generated_card.buff(attack=+1)
        >> generated_card.summon(controller=TURN_PLAYER)
    )


@card(
    1_000_027,
    name="Takoyaki Stand",
    description=(
        "{{KW:HASTE}}. "
        "{{KW:MAGIC}}: Kill an ally {{RARITY:TOKEN}} monster to gain {{STATS:+1|+2}} and any stat buffs it had."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=3,
    hp=5,
    keywords=HASTE,
    image=CustomImage("images/Takoyaki_Stand.png"),
    localizations={
        'en': LocalizedText(
            name="Takoyaki Stand{{PLURAL:$1||s}}",
        ),
    },
)
class TakoyakiStand(Monster):
    targets = ALLY_MONSTERS & TOKEN
    stored_card: Var[Card] = Var(Card)

    magic = (
        SetVar(
            var=stored_card,
            value=(TARGET >> EXACT_COPY())
        )
        >> TARGET.kill().to(
            SELF.buff(attack=+1, hp=+2)
            >> SELF.buff(
                attack=stored_card.buffs.attack,
                hp=stored_card.buffs.max_hp,
                cost=stored_card.buffs.cost
            )
        )
    )

@card(
    1_000_028,
    name="Spikery",
    description=(
        "{{KW:NEED}}: 3+ monsters took {{DMG}} this turn. "
        "{{KW:MAGIC}}: Gain {{KW:TAUNT}} and +1 {{KW:DODGE}}."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=3,
    hp=4,
    image=CustomImage("images/Spikery.png"),
    localizations={
        'en': LocalizedText(
            name="Spiker{{PLURAL:$1|y|ies}}",
        ),
    },
)
class Spikery(Monster):
    need = (
        COUNT_DISTINCT(
            DAMAGE_DONE(scope=THIS_TURN) & IS_MONSTER,
            TARGET_ID
        ) >= 3
    )

    magic = (
        SELF.set_status(
            DODGE,
            value=SELF.status(DODGE) + 1
        )
        >> SELF.add_keyword(TAUNT)
    )


@card(
    1_000_029,
    name="Dogmobile",
    description=(
        "{{KW:DELAY}} and {{KW:TURN_END}}: Attack the lowest {{HP}} enemy monster."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=2,
    hp=7,
    tribes=[Tribe.DOG],
    image=CustomImage("images/Dogmobile.png"),
    localizations={
        'en': LocalizedText(
            name="Dogmobile{{PLURAL:$1||s}}",
        ),
    },
)
class Dogmobile(Monster):
    _effect = SELF.force_attack(ENEMY_MONSTERS >> MIN(HP))

    magic = SELF.schedule_delay_effect()
    delay = _effect
    turn_end = _effect


@card(
    1_000_030,
    name="Scissors",
    description=(
        "{{KW:MAGIC}}: Deal 1 {{DMG}} to a monster. "
        "If it's already damaged, gain {{ATK}} equal to its {{HP}} instead."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=2,
    attack=1,
    hp=3,
    image=ExistingImage("Sheary"),
    localizations={
        'en': LocalizedText(
            name="Scissors",
        ),
    },
)
class Scissors(Monster):
    targets = ALL_MONSTERS

    magic = Check(TARGET & DAMAGED).to(
        SELF.buff(attack=TARGET.hp),
        else_=TARGET.hit(1)
    )


@card(
    1_000_031,
    name="Kawkaw",
    description=(
        "ueueleuleuleue"
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=0,
    attack=0,
    hp=3,
    image=CustomImage("images/Kawkaw.png"),
    localizations={
        'en': LocalizedText(
            name="Kawkaw{{PLURAL:$1||s}}",
        ),
    },
)
class Kawkaw(Monster):
    magic = ()


@card(
    1_000_032,
    name="Lancer Marker",
    description=(
        "{{KW:MAGIC}}: Enchant all empty and unenchanted ally slots with {{ENCHANT:XMARK|2}}. Add a {{CARD:371|1}} to your hand."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=2,
    hp=3,
    image=CustomImage("images/Lancer_Marker.png"),
    localizations={
        'en': LocalizedText(
            name="Lancer Marker{{PLURAL:$1||s}}",
        ),
    },
)
class LancerMarker(Monster):
    magic = (
        GENERATE_CARD("Spade").to_hand()
        >> (
            ALLY_SLOTS
            & EMPTY_SLOT
            & UNENCHANTED_SLOT
        ).enchant(
            ENCHANTMENT_BY_NAME('xmark')
        )
    )


@enchantment(
    'xmark',
    name="XMark",
    description="After a monster is summoned here, give a {{CARD:371|1}} in your hand -1 {{COST}} and this effect expires. {{KW:TURN_END}}: This effect expires.",
    image=ExistingImage("X"),
    overlay=ExistingImage("X"),
    localizations={
        'en': LocalizedText(
            name="X-Mark{{PLURAL:$1||s}}",
        ),
    },
)
class XMark(Enchantment):
    turn_end = SELF.expire_enchantment()

    @on_event(MonsterSummonedResult)
    def on_monster_summoned(self, res: MonsterSummonedResult, game, **kwargs):
        if res.monster.slot_id != self.slot_id:
            return None

        return (
            (HAND & (TEMPLATE_NAME == "Spade")).first().buff(cost=-1)
            >> SELF.expire_enchantment()
        )


@card(
    1_000_033,
    name="MTT Chainsaw",
    description=(
        "{{KW:MAGIC}}: Choose a monster. "
        "{{KW:DELAY}}: {{KW:PROGRAM}} (3): Kill it. "
        "{{KW:SUPPORT}}: Reduce the {{KW:PROGRAM}} by 1."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.BASE,
    cost=7,
    attack=3,
    hp=7,
    statuses={
        PROGRAM: 3,
    },
    image=CustomImage("images/Chainsaw.png"),
    localizations={
        'en': LocalizedText(
            name="MTT Chainsaw{{PLURAL:$1||s}}",
        ),
    },
)
class MTTChainsaw(Monster):
    targets = ALL_MONSTERS
    chosen_monster: Var[TargetSelector] = Var(TargetSelector)

    magic = (
        SetVar(var=chosen_monster, value=TARGET)
        >> SELF.schedule_delay_effect()
    )

    delay = Check(
        ~chosen_monster.dead
    ).to(
        Program(SELF.status(PROGRAM)).to(
            chosen_monster.kill()
        )
    )

    support = (
        Check(SELF.status(PROGRAM) >= 1).to(
            SELF.set_status(
                PROGRAM,
                value=SELF.status(PROGRAM) - 1
            )
        )
    )


@card(
    1_000_034,
    name="Dancing Cat",
    description=(
        "{{KW:HASTE}}. In your hand, this has -1 {{COST}} "
        "for each {{CARD:1000034|1}} you played this game."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=3,
    hp=5,
    keywords=HASTE,
    image=CustomImage("images/Dancing_Cat.png"),
    localizations={
        'en': LocalizedText(
            name="Dancing Cat{{PLURAL:$1||s}}",
        ),
    },
)
class DancingCat(Monster):
    def iter_modifiers(self, game):
        if self.zone is not CardZone.HAND:
            return

        played_cat_count = 0

        for res in game.log_by_type[CardPlayedResult]:
            if res.player_id != self.controller_id:
                continue

            if res.card.template.name != "Dancing Cat":
                continue

            played_cat_count += 1

        if played_cat_count <= 0:
            return

        yield IntModifier(
            kind=ModKind.COST,
            layer=CostLayer.ADD,
            source=self,
            description="In your hand, this has -1 COST for each Dancing Cat you played this game",
            applies=lambda q: q.card is self,
            apply=lambda cost, q: cost - played_cat_count,
        )


@card(
    1_000_035,
    name="Poppup",
    description=(
        "{{KW:TAUNT}}. After you take {{DMG}} and have 15 or less {{HP}}, summon this from your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=2,
    attack=2,
    hp=2,
    keywords=TAUNT,
    works_in_hand=True,
    image=CustomImage("images/Poppup.png"),
    localizations={
        'en': LocalizedText(
            name="Poppup{{PLURAL:$1||s}}",
        ),
    },
)
class Poppup(Monster):
    @on_event(EntityDamagedResult)
    def on_entity_damaged(self, res: EntityDamagedResult, game, **kwargs):
        if res.target_id != self.controller_id:
            return None

        if game.player(self.controller_id).hp > 15:
            return None

        if self.zone != CardZone.HAND:
            return None

        return SELF.summon()


@card(
    1_000_036,
    name="Candle Lighter",
    description=(
        "After this gains {{ATK}}, deal 1 {{DMG}} to the opponent."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=1,
    attack=1,
    hp=3,
    image=CustomImage("images/Candle_Lighter.png"),
    localizations={
        'en': LocalizedText(
            name="Candle Lighter{{PLURAL:$1||s}}",
        ),
    },
)
class CandleLighter(Monster):
    @on_event(EntityBuffedResult)
    def on_entity_buffed(self, res: EntityBuffedResult, game, **kwargs):
        if res.target_id != self.id:
            return None

        if res.attack_amount <= 0:
            return None

        return OPPONENT.hit(1)


@card(
    1_000_037,
    name="Heart Pillows",
    description=(
        "{{KW:HASTE}}. {{KW:CANDY}}. "
        "After you play a monster, steal 1 {{HP}} from it if this is in your hand."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=5,
    hp=3,
    keywords=HASTE | CANDY,
    works_in_hand=True,
    image=CustomImage("images/Heart_Pillows.png"),
    localizations={
        'en': LocalizedText(
            name="Heart Pillows",
        ),
    },
)
class HeartPillows(Monster):
    @on_event(CardPlayedResult)
    def on_card_played(self, res: CardPlayedResult, game, **kwargs):
        card_ = game.entity(res.card_id)
        if not isinstance(card_, Monster):
            return None

        if card_.controller_id != self.controller_id:
            return None

        if self.zone != CardZone.HAND:
            return None

        return (
            card_.actions.buff(hp=-1)
            >> SELF.buff(hp=+1)
        )


@card(
    1_000_038,
    name="Maustower",
    description=(
        "In your hand, this has -1 {{COST}} for each {{RARITY:TOKEN}} card in your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=7,
    attack=6,
    hp=5,
    image=CustomImage("images/Maicetower.png"),
    localizations={
        'en': LocalizedText(
            name="Maustower{{PLURAL:$1||s}}",
        ),
    },
)
class Maustower(Monster):
    def iter_modifiers(self, game):
        if self.zone is not CardZone.HAND:
            return

        hand_tokens = sum(
            1
            for monster in game.player(self.controller_id).hand.cards
            if (monster.rarity is CardRarity.TOKEN)
        )

        yield IntModifier(
            kind=ModKind.COST,
            layer=CostLayer.ADD,
            source=self,
            description="In your hand, this has -1 COST for each TOKEN card in your hand",
            applies=lambda q: q.card is self,
            apply=lambda cost, q: cost - hand_tokens,
        )


@card(
    1_000_039,
    name="Super Nubert",
    description=(
        "{{KW:HASTE}}. {{KW:TAUNT}}. "
        "This card's stat buffs are doubled."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=10,
    attack=4,
    hp=6,
    keywords=HASTE | TAUNT,
    image=CustomImage("images/Super_Nubert.png"),
    localizations={
        'en': LocalizedText(
            name="Super Nubert{{PLURAL:$1||s}}",
        ),
    },
)
class SuperNubert(Monster):
    def iter_modifiers(self, game):
        if (self.zone is not CardZone.HAND) and (self.zone is not CardZone.BOARD):
            return

        yield IntModifier(
            kind=ModKind.COST,
            layer=CostLayer.ADD,
            source=self,
            description="This card's cost buffs are doubled",
            applies=lambda q: q.card is self,
            apply=lambda cost, q: cost + min(self.buffs.cost, 0),
        )

        yield IntModifier(
            kind=ModKind.ATTACK,
            layer=StatLayer.ADD,
            source=self,
            description="This card's ATK buffs are doubled",
            applies=lambda q: q.monster is self,
            apply=lambda attack, q: attack + max(self.buffs.attack, 0),
        )

        yield IntModifier(
            kind=ModKind.MAX_HP,
            layer=StatLayer.ADD,
            source=self,
            description="This card's HP buffs are doubled",
            applies=lambda q: q.monster is self,
            apply=lambda max_hp, q: max_hp + max(self.buffs.max_hp, 0),
        )


@card(
    1_000_040,
    name="Snowmonster",
    description=(
        "{{KW:SHOCK}}: Gain +1 {{ATK}}. "
        "{{KW:DUST}}: Summon a copy of this with {{STATS:-2|-3}} base stats."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.BASE,
    cost=3,
    attack=2,
    hp=5,
    image=CustomImage("images/Antlers_Snowman.png"),
    localizations={
        'en': LocalizedText(
            name="Snowmonster{{PLURAL:$1||s}}",
        ),
    },
)
class Snowmonster(Monster):
    shock = (
        SELF.buff(attack=+1)
    )

    dust = (
        Check(SELF.base.hp > 3).to(
            GENERATE_CARD("Snowmonster").summon(
                attack=(SELF.base.attack - 2),
                hp=(SELF.base.hp - 3)
            )
        )
    )


@card(
    1_000_041,
    name="Tem Painting",
    description=(
        "{{KW:MAGIC}}: Gain {{STATS:+1|+1}} for each {{TRIBE:TEMMIE}} "
        "you played last turn and attack all enemy monsters. "
        "{{KW:DUST}}: Summon 2 {{CARD:50|2}}."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.BASE,
    cost=8,
    attack=4,
    hp=5,
    tribes=[Tribe.TEMMIE],
    image=CustomImage("images/History_Temmie.png"),
    localizations={
        'en': LocalizedText(
            name="Tem Painting{{PLURAL:$1||s}}",
        ),
    },
)
class TemPainting(Monster):
    last_turn_tems: Var[int] = Var(int)

    magic = (
        SetVar(
            var=last_turn_tems,
            value=COUNT(
                CARDS_PLAYED(player=YOU, scope=LAST_TURN_OF(YOU))
                & HAS_TRIBE(Tribe.TEMMIE)
            )
        )
        >> SELF.buff(attack=last_turn_tems, hp=last_turn_tems)
        >> SELF.force_attack(ENEMY_MONSTERS)
    )

    dust = GENERATE_CARD("Temmie").summon() * 2


@card(
    1_000_042,
    name="Waterfall Flower",
    description=(
        "After you cast a spell, draw a monster of the same {{COST}}."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.BASE,
    cost=2,
    attack=1,
    hp=2,
    tribes=[Tribe.PLANT],
    image=CustomImage("images/Waterfall_Flower.png"),
    localizations={
        'en': LocalizedText(
            name="Waterfall Flower{{PLURAL:$1||s}}",
        ),
    },
)
class WaterfallFlower(Monster):
    @on_event(SpellCastResult)
    def on_spell_cast(self, res: SpellCastResult, game, **kwargs):
        if res.player_id != self.controller_id:
            return None

        return YOU.draw((DECK & IS_MONSTER & (COST == res.card.cost)).first())


@card(
    1_000_043,
    name="Golden Statue",
    description=(
        "{{KW:MAGIC}}: Look at all other CUSTOM cards and add one to your hand."
    ),
    rarity=CardRarity.LEGENDARY,
    expansion=Expansion.BASE,
    cost=1,
    attack=1,
    hp=3,
    tribes=[Tribe.DOG],
    image=CustomImage("images/Dog_Statue.png"),
    localizations={
        'en': LocalizedText(
            name="Golden Statue{{PLURAL:$1||s}}",
        ),
    },
)
class GoldenStatue(Monster):
    magic = YOU.choose(
        (
            CARD_LIBRARY
            & (TEMPLATE_ID >= 1000000)
            & ~(RARITY == CardRarity.TOKEN)
            & ~(TEMPLATE_NAME == "Golden Statue")
        ) >> GENERATE_CARD()
    ).to(
        CHOICE_SELECTED.to_hand()
    )


@card(
    1_000_044,
    name="Justice Axe",
    description=(
        "{{KW:MAGIC}}: Choose a monster. "
        "Add a {{CARD:1000045|1}} to your hand "
        "with its {{ATK}} as base {{ATK}}."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=5,
    hp=6,
    image=CustomImage("images/JusticeAxe.png"),
    localizations={
        'en': LocalizedText(
            name="Justice Axe{{PLURAL:$1||s}}",
        ),
    },
)
class JusticeAxe(Monster):
    targets = ALL_MONSTERS
    generated_card: Var[Card] = Var(Card)

    magic = (
        SetVar(
            var=generated_card,
            value=GENERATE_CARD("Bouncing Shell")
        )
        >> generated_card.set_base_stats(attack=TARGET.attack)
        >> generated_card.to_hand()
    )


@card(
    1_000_045,
    name="Bouncing Shell",
    description=(
        "{{KW:HASTE}}. {{KW:BULLSEYE}}: Add a copy of this to your hand "
        "with {{STATS:-1|-1|-1}} base stats."
    ),
    rarity=CardRarity.TOKEN,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=3,
    hp=3,
    keywords=HASTE,
    image=CustomImage("images/Bouncing_Shell.png"),
    localizations={
        'en': LocalizedText(
            name="Bouncing Shell{{PLURAL:$1||s}}",
        ),
    },
)
class BouncingShell(Monster):
    generated_card: Var[Card] = Var(Card)

    bullseye = Check(SELF.base.hp > 1).to(
        SetVar(
            var=generated_card,
            value=GENERATE_CARD("Bouncing Shell")
        )
        >> generated_card.set_base_stats(
            cost=SELF.base.cost - 1,
            attack=SELF.base.attack - 1,
            hp=SELF.base.hp - 1
        )
        >> generated_card.to_hand()
    )


@card(
    1_000_046,
    name="Balloon Dog",
    description=(
        "{{KW:MAGIC}}: Choose a monster in your deck to {{KW:CATCH}}. "
        "{{KW:DUST}}: Draw a copy of it. "
        "If you can't, add an {{CARD:1000047|1}} to your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.BASE,
    cost=3,
    attack=3,
    hp=2,
    tribes=[Tribe.DOG],
    image=CustomImage("images/Balloon_Dog.png"),
    localizations={
        'en': LocalizedText(
            name="Balloon Dog{{PLURAL:$1||s}}",
        ),
    },
)
class BalloonDog(Monster):
    released_card: Var[Card] = Var(Card)

    magic = YOU.choose(
        DECK
        & IS_MONSTER
    ).to(
        SELF.catch(CHOICE_SELECTED)
    )

    dust = SELF.release_caught_card(var=released_card).to(
        Check(DECK & (TEMPLATE_ID == released_card.template_id)).to(
            YOU.draw((DECK & (TEMPLATE_ID == released_card.template_id)).first()),
            else_=GENERATE_CARD("Egg").to_hand()
        )
    )


@card(
    1_000_047,
    name="Egg",
    description=(
        "You called out someone's name, but it sounds unfamiliar to your ears. "
        "Who are you looking for?"
    ),
    rarity=CardRarity.TOKEN,
    expansion=Expansion.DELTARUNE,
    cost=0,
    attack=3,
    hp=3,
    image=CustomImage("images/EGG.png"),
    localizations={
        'en': LocalizedText(
            name="Egg{{PLURAL:$1||s}}",
        ),
    },
)
class Egg(Monster):
    magic = ()


@card(
    1_000_048,
    name="Windstruggler",
    description=(
        "{{KW:NEED}}: No non-{{KW:GENERATED}} "
        "{{KW:HASTE}} or {{KW:CHARGE}} monsters in your deck. "
        "{{KW:MAGIC}}: Set a monster's {{HP}} to 1."
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=3,
    hp=4,
    image=CustomImage("images/Wind_Struggler.png"),
    localizations={
        'en': LocalizedText(
            name="Windstruggler{{PLURAL:$1||s}}",
        ),
    },
)
class Windstruggler(Monster):
    targets = ALL_MONSTERS

    need = ~EXISTS(
        DECK
        & NON_GENERATED
        & IS_MONSTER
        & (HAS_KEYWORD(HASTE) | HAS_KEYWORD(CHARGE))
    )

    magic = TARGET.set_stats(hp=1)


@card(
    1_000_049,
    name="Cheese Bank",
    description=(
        "{{KW:MAGIC}}: Add a {{STATS:1|1}} copy of each ally monster "
        "with a base {{COST}} of 1 or less {{GOLD}} to your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=3,
    attack=2,
    hp=4,
    image=CustomImage("images/Cheese_Bank.png"),
    localizations={
        'en': LocalizedText(
            name="Cheese Bank{{PLURAL:$1||s}}",
        ),
    },
)
class CheeseBank(Monster):
    monster: Var[Card] = Var(Card)
    copied_monster: Var[Card] = Var(Card)

    magic = ForEach(
        ALLY_MONSTERS,
        var=monster,
        effect=Check(monster.base.cost <= 1).to(
            SetVar(
                var=copied_monster,
                value=monster >> COPY()
            )
            >> copied_monster.set_base_stats(attack=1, hp=1)
            >> copied_monster.to_hand()
        )
    )


@card(
    1_000_050,
    name="QC",
    description=(
        "{{KW:MAGIC}}: Draw up to 4 {{RARITY:BASE}} cards."
    ),
    rarity=CardRarity.EPIC,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=3,
    hp=6,
    image=CustomImage("images/QC.png"),
    localizations={
        'en': LocalizedText(
            name="QC{{PLURAL:$1||s}}",
        ),
    },
)
class QC(Monster):
    magic = DrawUpTo(4, group=(RARITY == CardRarity.BASE))


@card(
    1_000_051,
    name="Sousborg",
    description=(
        "{{KW:TAUNT}}. After this kills a monster, add a {{CARD:596|1}} to your deck. "
        "{{KW:BULLSEYE}}: Send all {{CARD:596|2}} in your deck to the top."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.UTY,
    cost=6,
    attack=4,
    hp=8,
    keywords=TAUNT,
    image=CustomImage("images/Sousborg.png"),
    localizations={
        'en': LocalizedText(
            name="Sousborg{{PLURAL:$1||s}}",
        ),
    },
)
class Sousborg(Monster):
    send_vegetable: Var[Card] = Var(Card)

    @on_event(MonsterKilledResult)
    def on_monster_killed(self, res: MonsterKilledResult, game, **kwargs):
        if res.killer_id != self.id:
            return None

        return GENERATE_CARD("Vegetables").to_deck()

    bullseye = (
        ForEach(
            DECK & (TEMPLATE_NAME == "Vegetables"),
            var=send_vegetable,
            effect=send_vegetable.to_deck(pos='top')
        )
    )


@card(
    1_000_052,
    name="Asgore Plush",
    description=(
        "Other damaged monsters take +2 {{DMG}}."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.UTY,
    cost=3,
    attack=3,
    hp=3,
    image=CustomImage("images/Asgore_Plush.png"),
    localizations={
        'en': LocalizedText(
            name="Asgore Plush{{PLURAL:$1||es}}",
        ),
    },
)
class AsgorePlush(Monster):
    def iter_modifiers(self, game):
        if self.zone is not CardZone.BOARD:
            return

        yield IntModifier(
            kind=ModKind.DAMAGE,
            layer=DamageLayer.ADD,
            source=self,
            description="Damaged monsters take +2 DMG",
            applies=lambda q: (
                (q.target is not self)
                and isinstance(q.target, Monster)
                and (q.target.hp_missing > 0)
            ),
            apply=lambda damage, q: damage + 2,
        )


@card(
    1_000_053,
    name="Pusher Flower",
    description=(
        "After you play a monster costing 2+ {{GOLD}}, "
        "deal 3 {{DMG}} to the monster in front of it."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=4,
    hp=5,
    tribes=[Tribe.PLANT],
    image=CustomImage("images/Pusher_Flower.png"),
    localizations={
        'en': LocalizedText(
            name="Pusher Flower{{PLURAL:$1||s}}",
        ),
    },
)
class PusherFlower(Monster):
    @on_event(CardPlayedResult)
    def on_card_played(self, res: CardPlayedResult, game, **kwargs):
        if res.player_id != self.controller_id:
            return None

        if res.card.cost < 2:
            return None

        card_ = game.entity(res.card_id)
        if not isinstance(card_, Monster):
            return None

        return FRONT(RESOLVE_ENTITY(res.card_id)).hit(3)


@card(
    1_000_054,
    name="Garden Fox",
    description=(
        "Kon kon~"
    ),
    rarity=CardRarity.COMMON,
    expansion=Expansion.DELTARUNE,
    cost=1,
    attack=1,
    hp=3,
    tribes=[Tribe.ALL],
    image=CustomImage("images/Garden_Fox.png"),
    localizations={
        'en': LocalizedText(
            name="Garden Fox{{PLURAL:$1||es}}",
        ),
    },
)
class GardenFox(Monster):
    magic = ()


@card(
    1_000_055,
    name="Trash Pile",
    description=(
        "After a non-{{KW:GENERATED}} non-{{RARITY:DETERMINATION}} "
        "ally monster dies, add a copy of it to your hand."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=5,
    attack=5,
    hp=5,
    image=CustomImage("images/Pile_of_Trash.png"),
    localizations={
        'en': LocalizedText(
            name="Trash Pile{{PLURAL:$1||s}}",
        ),
    },
)
class TrashPile(Monster):
    @on_event(MonsterKilledResult)
    def on_monster_killed(self, res: MonsterKilledResult, game, **kwargs):
        if res.monster.controller_id != self.controller_id:
            return None

        if res.monster.template.rarity == CardRarity.DETERMINATION:
            return None

        if res.monster.is_generated:
            return None

        return (RESOLVE_ENTITY(res.monster_id) >> COPY()).to_hand()


@card(
    1_000_056,
    name="Spellbook",
    description=(
        "{{KW:MAGIC}}: Cast a random 1-{{COST}} spell on each ally monster. "
        "{{KW:PROGRAM}} (2): 2-{{COST}} spells instead."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=4,
    attack=4,
    hp=5,
    statuses={
        PROGRAM: 2,
    },
    image=CustomImage("images/Magic_Book.png"),
    localizations={
        'en': LocalizedText(
            name="Spellbook{{PLURAL:$1||s}}",
        ),
    },
)
class Spellbook(Monster):
    monster: Var[Card] = Var(Card)
    chosen_spell: Var[Card] = Var(Card)
    spell_cost: Var[int] = Var(int)

    magic = (
        SetVar(var=spell_cost,value=1)
        >> Program(2).to(
            SetVar(var=spell_cost,value=2)
        )
        >> ForEach(
            ALLY_MONSTERS,
            var=monster,
            effect=(
                SetVar(
                    var=chosen_spell,
                    value=GENERATE_CARD(
                        (
                            CARD_LIBRARY
                            & IS_SPELL
                            & NON_TOKEN
                            & (COST == spell_cost)
                        ) >> RANDOM(1)
                    )
                )
                >> Cast(
                    card=chosen_spell,
                    controller=YOU,
                    effect_target=monster
                )
            )
        )
    )


@card(
    1_000_057,
    name="Greater Bandit",
    description=(
        "{{KW:NEED}}: Ally monsters have 6+ total stat buffs. "
        "{{KW:MAGIC}}: Add {{CARD:525|1}} to your hand "
        " and the top of your deck with +2 {{ATK}}."
    ),
    rarity=CardRarity.RARE,
    expansion=Expansion.DELTARUNE,
    cost=6,
    attack=5,
    hp=6,
    tribes=[Tribe.DOG],
    image=CustomImage("images/Greater_Bandit.png"),
    localizations={
        'en': LocalizedText(
            name="Greater Bandit{{PLURAL:$1||s}}",
        ),
    },
)
class GreaterBandit(Monster):
    _total_atk_buffs=SUM(ALLY_MONSTERS, ATTACK-BASE_ATTACK)
    _total_hp_buffs=SUM(ALLY_MONSTERS, HP-BASE_HP)
    _total_cost_buffs=SUM(ALLY_MONSTERS, BASE_COST-COST)
    generated_card: Var[Card] = Var(Card)

    need = (
        _total_atk_buffs
        + _total_hp_buffs
        + _total_cost_buffs
    ) >= 6

    magic = (
        SetVar(
            var=generated_card,
            value=GENERATE_CARD("Too Many Dogs")
        )
        >> generated_card.buff(attack=+2)
        >> generated_card.to_hand()
        >> SetVar(
            var=generated_card,
            value=GENERATE_CARD("Too Many Dogs")
        )
        >> generated_card.buff(attack=+2)
        >> generated_card.to_deck(pos='top')
    )
