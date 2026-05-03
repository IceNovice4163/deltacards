import math
from typing import Any, TYPE_CHECKING

from action_results import *
from actions_base import Action, ActionCall, ActionContext, ActionOutcome, Arg
from cards import Card, CardZone, CaughtCardData, Monster, Spell
from entity import Entity
from enums import Ability, CardKeyword, CardStatusId, DamageKind
from player import Player
from schemas.requests import ChoiceResponse, ChooseEntityPrompt, PendingChoiceRequest
from targeting import *

if TYPE_CHECKING:
    from artifacts import Artifact


__all__ = (
    'Action', 'ActionContext',
    'SetVar', 'Choose', 'Reveal',
    'Hit', 'Heal', 'Kill', 'Buff',
    'Draw', 'DrawNext', 'Overdraw',
    'AddKeyword', 'RemoveKeyword',
    'SetStatus', 'RemoveStatus',
    'Silence', 'Paralyze',
    'SetPlayerHP',
    'SetStats', 'SwapStats', 'HalveStats',
    'Move',
    'Summon', 'Play', 'Cast', 'RemoveCardFromStack', 'TriggerAbility',
    'Catch', 'ReleaseCaughtCard',
    'Erase',
    'Attack', 'CombatDamage', 'AttackAftermath', 'RefreshAttacks',
    'EarnGold', 'SpendGold', 'SetGold',
    'AddArtifact', 'UpdateArtifactCounter',
    'ScheduleEffect', 'ScheduleDelayEffect',
    'AdvanceTurn', 'ResolveScheduledEffectsAction',
    'PlayerStartTurnAction', 'PlayerEndTurnAction',
)


class SetVar(Action):
    var: Arg[Var] = Arg(raw=True)  # raw=True prevents turning `var` into a value
    value: Arg[Any] = Arg()

    def execute(self, var: Var, value: Any, *, ctx: ActionContext, **kwargs):
        ctx.vars[var.name] = value
        return ActionOutcome(success=True)


class Choose(Action):
    player: Arg['Player'] = Arg()
    options: Arg['list[Entity]'] = Arg()

    def execute(self, player: 'Player', options: 'list[Entity]', *, ctx: ActionContext, **kwargs):
        if len(options) == 0:
            return ActionOutcome(success=False)

        def _on_choose(response: ChoiceResponse):
            chosen = [entity for entity in options if entity.id in response.selected_option_ids]
            not_chosen = [entity for entity in options if entity not in chosen]

            ctx.vars['_choice_selected'] = chosen
            ctx.vars['_choice_not_selected'] = not_chosen

        pending_request = PendingChoiceRequest(
            request_id=ctx.game.alloc_request_id(),
            player_id=player.id,
            prompt=ChooseEntityPrompt(
                options=options,
            ),
            on_choose=_on_choose,
        )

        return ActionOutcome(
            success=True,
            pending_request=pending_request,
        )


class Reveal(Action):
    card: Arg['Card'] = Arg(many=True)

    def execute(self, card: 'Card', *, ctx: ActionContext, **kwargs):  # TODO
        return ActionOutcome(success=True)


class Hit(Action):
    target: Arg['Monster | Player'] = Arg(many=True)
    damage: Arg[int] = Arg()
    kind: Arg[DamageKind | None] = Arg(default=None)

    def execute(self, target: 'Monster | Player', damage: int, kind: DamageKind | None, *, ctx: ActionContext, **kwargs):
        res = ctx.game.apply_damage(
            target=target,
            damage=damage,
            source=ctx.source,
            kind=kind,
        )

        return ActionOutcome(
            success=(res.prevented_by != 'invalid_target'),
            results=res.results,
            action_calls=res.extra_actions,
        )


class Heal(Action):
    target: Arg['Monster | Player'] = Arg(many=True)
    amount: Arg[int] = Arg()

    def execute(self, target: 'Monster | Player', amount: int, *, ctx: ActionContext, **kwargs):
        hp_recovered = target.heal(amount)

        return ActionOutcome(
            success=True,
            results=(
                EntityHealedResult(
                    source_id=ctx.source.id,
                    target_id=target.id,
                    target=target.to_snapshot(),
                    amount=hp_recovered,
                ),
            ),
            affected=[target],
        )


class Kill(Action):
    target: Arg['Monster | Player'] = Arg(many=True)
    killer: Arg['Entity'] = Arg(default=SELF)

    def execute(self, target: 'Monster | Player', killer: 'Entity', *, ctx: ActionContext, **kwargs):
        action_calls = []
        results = []

        if isinstance(target, Monster):
            if target.has_keyword(CardKeyword.KR):
                if isinstance(killer, Monster) and killer.hp > 0:
                    buff_target = killer
                else:
                    buff_target = RANDOM(ENEMY_MONSTERS)

                action_calls.append(
                    ActionCall(Buff(target=buff_target, attack=1, hp=1), source=target)
                )

            if target.has_keyword(CardKeyword.WANTED):
                action_calls.append(
                    ActionCall(EarnGold(player=ctx.game.player(target.controller_id).opponent, amount=1), source=target)
                )

            effect = target.get_ability(Ability.DUST)
            if effect is not None:
                action_calls.append(
                    ActionCall(effect, source=target, env={'killer': killer})
                )

            ctx.game.move_card(target, target.controller_id, CardZone.DUSTPILE)

            results.append(
                MonsterKilledResult(
                    source_id=ctx.source.id,
                    monster_id=target.id,
                    monster=target.to_snapshot(),
                    killer_id=killer.id,
                    killer=killer.to_snapshot(),
                )
            )

        elif isinstance(target, Player):
            ctx.game.game_over = True
            ctx.game.dead_players.add(target.id)

            results.append(
                PlayerKilledResult(
                    source_id=ctx.source.id,
                    player_id=target.id,
                    player=target.to_snapshot(),
                    killer_id=killer.id,
                    killer=killer.to_snapshot(),
                )
            )

        else:
            raise TypeError(f"Target is of invalid type {type(target)}")

        return ActionOutcome(
            success=True,
            results=results,
            affected=[target],
            action_calls=action_calls,
        )


class Buff(Action):
    target: Arg['Card | Player'] = Arg(many=True)
    cost: Arg[int] = Arg(default=0)
    attack: Arg[int] = Arg(default=0)
    hp: Arg[int] = Arg(default=0)

    def execute(self, target: 'Card | Player', cost: int, attack: int, hp: int, *, ctx: ActionContext, **kwargs):
        action_calls = []

        if isinstance(target, Monster):
            target.buff(cost, attack, hp)
            if hp <= 0 and target.zone == CardZone.BOARD:
                action_calls.append(ActionCall(Kill(target=target, killer=ctx.source), source=ctx.source))

        elif isinstance(target, Spell):
            target.buff(cost)

        elif isinstance(target, Player):
            assert cost == 0 and attack == 0
            target.buff(hp=hp)

        return ActionOutcome(
            success=True,
            affected=[target],
            action_calls=action_calls,
        )


class Draw(Action):
    player: Arg['Player'] = Arg()
    card: Arg['Card'] = Arg(many=True)
    reason: Arg[str] = Arg(default='effect')

    def execute(self, player: 'Player', card: 'Card', reason: str, *, ctx: ActionContext, **kwargs):
        if card.zone is not CardZone.DECK or card.controller_id != player.id:
            return ActionOutcome(success=False)

        if len(player.hand) >= 7:
            return ActionOutcome(
                success=True,
                action_calls=[ActionCall(Overdraw(player=player, card=card), source=ctx.source)],
            )

        ctx.game.move_card(card, controller_id=player.id, zone=CardZone.HAND)

        return ActionOutcome(
            success=True,
            affected=[card],
        )


class DrawNext(Action):
    player: Arg['Player'] = Arg(many=True)
    reason: Arg[str] = Arg(default='effect')

    def execute(self, player: 'Player', reason: str, *, ctx: ActionContext, **kwargs):
        if len(player.deck) > 0:
            card = player.deck.cards[0]

            return ActionOutcome(
                success=True,
                action_calls=[ActionCall(Draw(player=player, card=card, reason=reason), source=ctx.source)],
            )

        else:
            player.fatigue_counter += 1

            return ActionOutcome(
                success=False,
                action_calls=[ActionCall(Hit(target=player, damage=player.fatigue_counter, kind=DamageKind.FATIGUE), source=player)],
            )


class Overdraw(Action):
    player: Arg['Player'] = Arg()
    card: Arg['Card'] = Arg(many=True)

    def execute(self, player: 'Player', card: 'Card', *, ctx: ActionContext, **kwargs):
        ctx.game.move_card(card, controller_id=player.id, zone=CardZone.ERASED)
        return ActionOutcome(
            success=True,
            affected=[card],
        )


class AddKeyword(Action):
    target: Arg['Card'] = Arg(many=True)
    keyword: Arg[CardKeyword] = Arg()

    def execute(self, target: Card, keyword: CardKeyword, *, ctx: ActionContext, **kwargs):
        target.add_keyword(keyword)
        return ActionOutcome(success=True, affected=[target])


class RemoveKeyword(Action):
    target: Arg['Card'] = Arg(many=True)
    keyword: Arg[CardKeyword] = Arg()

    def execute(self, target: Card, keyword: CardKeyword, *, ctx: ActionContext, **kwargs):
        target.remove_keyword(keyword)
        return ActionOutcome(success=True, affected=[target])


class SetStatus(Action):
    target: Arg['Card'] = Arg(many=True)
    status_id: Arg[CardStatusId] = Arg()
    value: Arg[int] = Arg(default=1)

    def execute(self, target: Card, status_id: CardStatusId, value: int, *, ctx: ActionContext, **kwargs):
        target.set_status(status_id, value)
        return ActionOutcome(success=True, affected=[target])


class RemoveStatus(Action):
    target: Arg['Card'] = Arg(many=True)
    status_id: Arg[CardStatusId] = Arg()

    def execute(self, target: Card, status_id: CardStatusId, *, ctx: ActionContext, **kwargs):
        target.remove_status(status_id)
        return ActionOutcome(success=True, affected=[target])


class Silence(Action):
    target: Arg['Monster'] = Arg(many=True)

    def execute(self, target: Monster, *, ctx: ActionContext, **kwargs):
        success = target.silence()
        return ActionOutcome(
            success=success,
            affected=[target] if success else [],
        )


class Paralyze(Action):
    target: Arg['Monster'] = Arg(many=True)

    def execute(self, target: Monster, *, ctx: ActionContext, **kwargs):
        paralyzed_turns = target.get_status(CardStatusId.PARALYZED)
        if paralyzed_turns > 0:
            return ActionOutcome(success=False)

        target.set_status(CardStatusId.PARALYZED, 2)
        return ActionOutcome(success=True, affected=[target])


class SetPlayerHP(Action):
    player: Arg['Player'] = Arg()
    hp: Arg[int] = Arg()

    def execute(self, player: 'Player', hp: int, *, ctx: ActionContext, **kwargs):
        player.set_max_hp(hp)
        return ActionOutcome(success=True, affected=[player])


# TODO check for correctness with modifiers
class SetStats(Action):
    target: Arg['Card'] = Arg(many=True)
    cost: Arg[int | None] = Arg(default=None)
    attack: Arg[int | None] = Arg(default=None)
    hp: Arg[int | None] = Arg(default=None)

    def execute(self, target: 'Card', cost: int | None, attack: int | None, hp: int | None, *, ctx: ActionContext, **kwargs):
        action_calls = []

        if attack is not None:
            assert isinstance(target, Monster)
            target.buff(attack - target.attack)

        if hp is not None:
            assert isinstance(target, Monster)
            target.buff(hp - target.hp)

            if hp <= 0 and target.zone == CardZone.BOARD:
                action_calls.append(ActionCall(Kill(target=target, killer=ctx.source), source=ctx.source))

        if cost is not None:
            target.buff(cost - target.cost)

        return ActionOutcome(
            success=True,
            affected=[target],
            action_calls=action_calls,
        )


class SwapStats(Action):
    target: Arg['Monster'] = Arg(many=True)

    def execute(self, target: Monster, *, ctx: ActionContext, **kwargs):
        action_calls = []
        target.buff(attack=target.hp - target.attack, hp=target.attack - target.hp)

        if target.hp <= 0 and target.zone == CardZone.BOARD:
            action_calls.append(ActionCall(Kill(target=target, killer=ctx.source), source=ctx.source))

        return ActionOutcome(
            success=True,
            affected=[target],
            action_calls=action_calls,
        )


class HalveStats(Action):
    target: Arg['Monster'] = Arg(many=True)
    round_up: Arg['bool'] = Arg()

    def execute(self, target: Monster, round_up: bool, *, ctx: ActionContext, **kwargs):
        action_calls = []

        round_func = math.floor if round_up else math.ceil  # negative stat buffs are inverted
        target.buff(attack=-round_func(target.attack / 2), hp=-round_func(target.hp / 2))

        if target.hp <= 0 and target.zone == CardZone.BOARD:
            action_calls.append(ActionCall(Kill(target=target, killer=ctx.source), source=ctx.source))

        return ActionOutcome(
            success=True,
            affected=[target],
            action_calls=action_calls,
        )


class Move(Action):
    target: Arg['Card'] = Arg(many=True)
    zone: Arg[CardZone] = Arg()
    controller: Arg['Player | None'] = Arg(default=None)
    pos: Arg['int | str | None'] = Arg(default=None)  # board/deck index, or one of: 'top', 'bottom', 'shuffle'

    def execute(self, target: 'Card', zone: CardZone, controller: 'Player | None', pos: 'int | str | None', *, ctx: ActionContext, **kwargs):
        if controller is None:
            controller = ctx.game.players[target.controller_id]

        if zone == CardZone.HAND:
            if target.zone == CardZone.DECK and target.controller_id == controller.id:
                return ActionOutcome(
                    success=True,
                    action_calls=[ActionCall(Draw(player=controller, card=target), source=ctx.source)],
                )

            if len(controller.hand) >= 7:
                if target.zone == CardZone.BOARD:
                    return ActionOutcome(
                        success=True,
                        action_calls=[ActionCall(Kill(target=target, killer=ctx.source), source=ctx.source)],
                    )
                elif target.zone == CardZone.DECK:
                    return ActionOutcome(
                        success=True,
                        action_calls=[ActionCall(Overdraw(player=controller, card=target), source=ctx.source)],
                    )
                else:
                    return ActionOutcome(success=False)

        ctx.game.move_card(card=target, controller_id=controller.id, zone=zone, pos=pos)
        return ActionOutcome(success=True, affected=[target])


class Summon(Action):
    card: Arg['Monster'] = Arg(many=True)
    controller: Arg['Player'] = Arg()
    pos: Arg[int | None] = Arg(default=None)
    attack: Arg[int | None] = Arg(default=None)
    hp: Arg[int | None] = Arg(default=None)

    def execute(self, card: 'Monster', controller: 'Player', pos: int | None, attack: int | None, hp: int | None, *, ctx: ActionContext, **kwargs):
        if len(controller.board) == controller.board.MAX_CARDS:
            return ActionOutcome(success=False)

        if pos is None:
            try:
                pos = controller.board.get_empty_slot_index()
            except StopIteration:
                return ActionOutcome(success=False)

        else:
            if not (0 <= pos < controller.board.MAX_CARDS):
                return ActionOutcome(success=False)
            if controller.board[pos] is not None:
                return ActionOutcome(success=False)

        if (attack is not None) or (hp is not None):
            card.set_base_stats(attack=attack, hp=hp)

        ctx.game.move_card(card, controller.id, CardZone.BOARD, pos=pos)

        return ActionOutcome(
            success=True,
            results=(
                MonsterSummonedResult(
                    source_id=ctx.source.id,
                    monster_id=card.id,
                    monster=card.to_snapshot(),
                ),
            ),
            affected=[card],
        )


class Play(Action):
    player: Arg['Player'] = Arg()
    card: Arg['Card'] = Arg()
    pos: Arg[int | None] = Arg(default=None)
    target: Arg[Entity | None] = Arg(default=None)

    # for manual play UX (allow canceling target selection)
    allow_cancel: Arg[bool] = Arg(default=False)

    def execute(self, player: 'Player', card: 'Card', pos: int | None, target: Entity | None, allow_cancel: bool, *, ctx: ActionContext, **kwargs):
        if card.controller_id != player.id or card.zone is not CardZone.HAND:
            return ActionOutcome(success=False)

        if player.gold < card.cost:
            return ActionOutcome(success=False)

        if isinstance(card, Monster):
            # TODO unsure if this part needs to be duplicated here and in Summon()
            if pos is None:
                try:
                    pos = player.board.get_empty_slot_index()
                except StopIteration:
                    return ActionOutcome(success=False)

            else:
                if not (0 <= pos < player.board.MAX_CARDS):
                    return ActionOutcome(success=False)
                if player.board[pos] is not None:
                    return ActionOutcome(success=False)

        skip_magic = False

        if card.targets is not None:
            options = ctx.game.play_target_options(card=card, player=player, pos=pos)

            if target is None:
                if len(options) == 0:
                    if isinstance(card, Spell):
                        # Spell is not playable without targets
                        return ActionOutcome(success=False)

                    # Monster is playable without targets, but its Magic gets skipped
                    skip_magic = True

                else:
                    prompt = ChooseEntityPrompt(
                        options=options,
                    )
                    id_to_obj = {int(o.id): o for o in options}

                    def _on_choose(response: ChoiceResponse):
                        if not response.selected_option_ids:
                            # Cancel => do nothing
                            return []

                        chosen_id = response.selected_option_ids[0]
                        chosen = id_to_obj[chosen_id]

                        # Continue by re-enqueuing Play() with a chosen target
                        return [Play(player=player, card=card, pos=pos, target=chosen)]

                    return ActionOutcome(
                        success=True,
                        pending_request=PendingChoiceRequest(
                            request_id=ctx.game.alloc_request_id(),
                            player_id=player.id,
                            prompt=prompt,
                            on_choose=_on_choose,
                            allow_cancel=allow_cancel,
                        )
                    )

            else:
                # If target is provided, validate it is legal
                if target not in options:
                    return ActionOutcome(success=False)

        spend_gold_calls = [
            ActionCall(SpendGold(player=player, amount=card.cost), source=card),
        ]

        magic_calls = []
        if not skip_magic:
            effect = card.get_ability(Ability.MAGIC)
            if effect is not None:
                magic_calls.append(ActionCall(effect, source=card, env={'target': target}))

        if isinstance(card, Monster):
            # TODO unsure if needed, currently it's here to allow LOOP to correctly trigger when there are 7 cards in hand
            ctx.game.move_card(card, player.id, CardZone.INVALID)

            loop_calls = []
            loop_counters = card.get_status(CardStatusId.LOOP)
            if loop_counters >= 1:
                copy = ctx.game.create_card_copy(card, creator_id=card.id, creator_base_identity=card.base_identity)
                copy.set_status(CardStatusId.LOOP, loop_counters - 1)
                loop_calls.append(ActionCall(Move(target=copy, zone=CardZone.HAND), source=card))

            return ActionOutcome(
                success=True,
                affected=[card],
                action_calls=[
                    *spend_gold_calls,
                    ActionCall(Summon(card=card, controller=player, pos=pos), source=player),
                    *loop_calls,
                    *magic_calls,
                ],
            )

        if isinstance(card, Spell):
            return ActionOutcome(
                success=True,
                affected=[card],
                action_calls=[
                    *spend_gold_calls,
                    ActionCall(Cast(card=card, controller=player, effect_target=target), source=player),
                    ActionCall(RemoveCardFromStack(card=card), source=card),
                ],
            )


class Cast(Action):
    card: Arg['Spell'] = Arg(many=True)
    controller: Arg['Player'] = Arg()
    effect_target: Arg['Entity | None'] = Arg()

    def execute(self, card: Spell, controller: 'Player', effect_target: 'Entity | None', *, ctx: ActionContext, **kwargs):
        ctx.game.move_card(card, controller.id, CardZone.STACK)

        magic_calls = []
        effect = card.get_ability(Ability.MAGIC)
        if effect is not None:
            magic_calls.append(ActionCall(effect, source=card, env={'target': effect_target}))

        return ActionOutcome(
            success=True,
            affected=[card],
            action_calls=[*magic_calls],
        )


class RemoveCardFromStack(Action):
    card: Arg['Card'] = Arg()

    def execute(self, card: 'Card', *, ctx: ActionContext, **kwargs):
        assert card.zone == CardZone.STACK, f"Card is not on stack: {card.zone}"
        ctx.game.move_card(card, card.controller_id, CardZone.DUSTPILE)
        return ActionOutcome(success=True, affected=[card])


class TriggerAbility(Action):
    target: Arg['Card'] = Arg(many=True)
    ability: Arg[Ability] = Arg()

    def execute(self, target: Card, ability: Ability, *, ctx: ActionContext, **kwargs):
        if isinstance(target, Monster) and target.has_keyword(CardKeyword.SILENCED):
            return ActionOutcome(success=False)

        effect = target.get_ability(ability)
        if effect is None:
            return ActionOutcome(success=True)

        return ActionOutcome(
            success=True,
            action_calls=[ActionCall(effect, source=target)],
        )


class Catch(Action):
    catcher: Arg['Monster'] = Arg()
    card_to_catch: Arg['Card'] = Arg()

    def execute(self, catcher: 'Monster', card_to_catch: 'Card', *, ctx: ActionContext, **kwargs):
        ctx.game.move_card(card_to_catch, card_to_catch.controller_id, CardZone.INVALID)
        catcher.caught_card = CaughtCardData(
            template_id=card_to_catch.template.id,
            controller_id=card_to_catch.controller_id,
        )

        return ActionOutcome(success=True, affected=[catcher, card_to_catch])


class ReleaseCaughtCard(Action):
    catcher: Arg['Monster'] = Arg()
    var: Arg[Var] = Arg(raw=True)  # raw=True prevents turning `var` into a value

    def execute(self, catcher: 'Monster', var: Var, *, ctx: ActionContext, **kwargs):
        if catcher.caught_card is None:
            return ActionOutcome(success=False)

        ctx.vars[var.name] = ctx.game.create_card(
            template_id=catcher.caught_card.template_id,
            controller_id=catcher.caught_card.controller_id,
            creator_id=catcher.id,
            creator_base_identity=catcher.base_identity,
        )
        catcher.caught_card = None
        return ActionOutcome(success=True)


class Erase(Action):
    target: Arg['Card'] = Arg(many=True)

    def execute(self, target: 'Card', *, ctx: ActionContext, **kwargs):
        ctx.game.move_card(target, target.controller_id, CardZone.ERASED)
        return ActionOutcome(success=True, affected=[target])


class Attack(Action):
    attacker: Arg['Monster'] = Arg()
    defender: Arg['Monster | Player'] = Arg(many=True)

    def execute(self, attacker: 'Monster', defender: 'Monster | Player', *, ctx: ActionContext, **kwargs):
        if attacker.zone is not CardZone.BOARD:
            return ActionOutcome(success=False)
        if isinstance(defender, Monster) and defender.zone is not CardZone.BOARD:
            return ActionOutcome(success=False)

        attacker.has_attacked = True
        ctx.env['combat_result'] = {}  # shared between CombatDamage and AttackAftermath

        return ActionOutcome(
            success=True,
            affected=[attacker, defender],
            action_calls=[
                ActionCall(CombatDamage(attacker=attacker, defender=defender), source=attacker, env=ctx.env),
                ActionCall(AttackAftermath(attacker=attacker, defender=defender), source=attacker, env=ctx.env),
            ],
        )


class CombatDamage(Action):
    attacker: Arg['Monster'] = Arg()
    defender: Arg['Monster | Player'] = Arg()

    def execute(self, attacker: 'Monster', defender: 'Monster | Player', *, ctx: ActionContext, **kwargs):
        if attacker.zone is not CardZone.BOARD:
            return ActionOutcome(success=False)
        if isinstance(defender, Monster) and defender.zone is not CardZone.BOARD:
            return ActionOutcome(success=False)

        if isinstance(defender, Player):
            res = ctx.game.apply_damage(
                target=defender,
                damage=attacker.attack,
                source=attacker,
                kind=DamageKind.COMBAT,
                combat_attacker=attacker,
                combat_defender=defender,
            )
            ctx.env['combat_result'].update({
                'damage_to_attacker': 0,
                'damage_to_defender': res.damage,
                'attacker_dead': False,
                'defender_dead': res.killed,
            })
            return ActionOutcome(
                success=True,
                results=res.results,
                affected=[attacker, defender],
                action_calls=res.extra_actions,
            )

        # Snapshot to avoid dynamic stat recalculations
        attacker_attack = attacker.attack
        defender_attack = defender.attack

        attacker_res = ctx.game.apply_damage(
            target=defender,
            damage=attacker_attack,
            source=attacker,
            kind=DamageKind.COMBAT,
            combat_attacker=attacker,
            combat_defender=defender,
        )
        defender_res = ctx.game.apply_damage(
            target=attacker,
            damage=defender_attack,
            source=defender,
            kind=DamageKind.COMBAT,
            combat_attacker=attacker,
            combat_defender=defender,
        )

        ctx.env['combat_result'].update({
            'damage_to_attacker': defender_res.damage,
            'damage_to_defender': attacker_res.damage,
            'attacker_dead': defender_res.killed,
            'defender_dead': attacker_res.killed,
        })
        return ActionOutcome(
            success=True,
            results=[*attacker_res.results, *defender_res.results],
            affected=[attacker, defender],
            # If both monsters die from simultaneous combat damage, the attacker's
            # Kill/Dust chain must resolve before the defender's.
            action_calls=[*attacker_res.extra_actions, *defender_res.extra_actions],
        )


class AttackAftermath(Action):
    attacker: Arg['Monster'] = Arg()
    defender: Arg['Monster | Player'] = Arg()

    def execute(self, attacker: 'Monster', defender: 'Monster | Player', *, ctx: ActionContext, **kwargs):
        if 'combat_result' not in ctx.env:
            raise RuntimeError(f"'combat_result' not in env: {ctx.env}")

        if attacker.zone == CardZone.BOARD:
            attacker.remove_keyword(CardKeyword.CHARGE)
            attacker.remove_keyword(CardKeyword.HASTE)

        return ActionOutcome(
            success=True,
            results=(
                AttackAftermathResult(
                    source_id=ctx.source.id,
                    attacker_id=attacker.id,
                    attacker=attacker.to_snapshot(),
                    defender_id=defender.id,
                    defender=defender.to_snapshot(),
                    damage_to_attacker=ctx.env['combat_result']['damage_to_attacker'],
                    damage_to_defender=ctx.env['combat_result']['damage_to_defender'],
                    attacker_dead=ctx.env['combat_result']['attacker_dead'],
                    defender_dead=ctx.env['combat_result']['defender_dead'],
                ),
            ),
            affected=[attacker, defender],
        )


class RefreshAttacks(Action):
    target: Arg['Monster'] = Arg(many=True)

    def execute(self, target: 'Monster', *, ctx: ActionContext, **kwargs):
        target.has_attacked = False

        return ActionOutcome(
            success=True,
            affected=[target],
        )


class EarnGold(Action):
    player: Arg['Player'] = Arg(many=True)
    amount: Arg[int] = Arg()

    def execute(self, player: 'Player', amount: int, *, ctx: ActionContext, **kwargs):
        if self.amount <= 0:
            return ActionOutcome(success=False)

        player.gold += amount
        return ActionOutcome(success=True, affected=[player])


class SpendGold(Action):
    player: Arg['Player'] = Arg(many=True)
    amount: Arg[int] = Arg()
    spent_on_spell: Arg[bool] = Arg(default=False)
    allow_partial: Arg[bool] = Arg(default=False)  # TODO

    def execute(self, player: 'Player', amount: int, spent_on_spell: bool, allow_partial: bool, *, ctx: ActionContext, **kwargs):
        assert self.amount >= 0

        if player.gold < amount:
            return ActionOutcome(success=False)

        player.gold -= amount

        return ActionOutcome(
            success=True,
            results=[
                SpentGoldResult(
                    source_id=ctx.source.id,
                    player_id=player.id,
                    amount=amount,
                    spent_on_spell=spent_on_spell,
                ),
            ],
            affected=[player],
        )


class SetGold(Action):
    player: Arg['Player'] = Arg(many=True)
    amount: Arg[int] = Arg()

    def execute(self, player: 'Player', amount: int, *, ctx: ActionContext, **kwargs):
        player.gold = amount
        return ActionOutcome(success=True, affected=[player])


class AddArtifact(Action):
    player: Arg['Player'] = Arg(many=True)
    artifact: Arg['Artifact'] = Arg()

    def execute(self, player: 'Player', artifact: 'Artifact', *, ctx: ActionContext, **kwargs):
        player.artifacts.append(artifact)
        return ActionOutcome(success=True, affected=[artifact])


class UpdateArtifactCounter(Action):
    artifact: Arg['Artifact'] = Arg()
    delta: Arg[int] = Arg()

    def execute(self, player: 'Player', artifact: 'Artifact', delta: int, *, ctx: ActionContext, **kwargs):
        artifact.counter = max(artifact.counter + delta, 0)
        return ActionOutcome(success=True, affected=[artifact])


class ScheduleEffect(Action):
    target: Arg['Entity'] = Arg(many=True)
    name: Arg[str] = Arg()

    def execute(self, target: 'Entity', name: str, *, ctx: ActionContext, **kwargs):
        ctx.game.schedule_effect(target.id, name, ctx)
        return ActionOutcome(success=True, affected=[target])


def ScheduleDelayEffect(target: 'Entity') -> ScheduleEffect:
    return ScheduleEffect(target=target, name='delay')


class AdvanceTurn(Action):
    player: Arg['Player'] = Arg()

    def execute(self, player: 'Player', *, ctx: ActionContext, **kwargs):
        if list(ctx.game.players.values())[-1] == player:
            ctx.game.turn += 1

        ctx.game.turn_player = next(p for p in ctx.game.players.values() if p is not player)

        return ActionOutcome(success=True)


class ResolveScheduledEffectsAction(Action):
    player: Arg['Player'] = Arg()

    def execute(self, player: 'Player', *, ctx: ActionContext, **kwargs):
        action_calls = []
        for effect in ctx.game.scheduled_effects:
            entity = ctx.game.entity(effect.entity_id)
            action_calls.append(
                ActionCall(
                    getattr(entity, effect.name),
                    source=entity,
                    env=effect.env,
                    vars=effect.vars,
                )
            )

        ctx.game.scheduled_effects = []

        return ActionOutcome(
            success=True,
            action_calls=action_calls,
        )


class PlayerStartTurnAction(Action):
    player: Arg['Player'] = Arg()

    def execute(self, player: 'Player', *, ctx: ActionContext, **kwargs):
        from timing_windows import run_player_start_turn_window

        return ActionOutcome(
            success=True,
            affected=[player],
            action_calls=[
                ActionCall(
                    run_player_start_turn_window,
                    source=player,
                    kwargs={'player': player},
                )
            ],
        )


class PlayerEndTurnAction(Action):
    player: Arg['Player'] = Arg()

    def execute(self, player: 'Player', *, ctx: ActionContext, **kwargs):
        from timing_windows import run_player_end_turn_window

        return ActionOutcome(
            success=True,
            affected=[player],
            action_calls=[
                ActionCall(
                    run_player_end_turn_window,
                    source=player,
                    kwargs={'player': player},
                )
            ],
        )
