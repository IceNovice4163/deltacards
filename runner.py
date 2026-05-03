from dataclasses import dataclass

from action_results import ActionResult
from actions import Action, Attack as AttackAction, Play, PlayerEndTurnAction, PlayerStartTurnAction
from artifacts import ARTIFACTS
from cards import CardZone
from containers import Deck
from enums import PlayerId
from game import Game
from schemas.requests import (
    Attack, ChoiceResponse, EndTurn, EngineInput, MulliganPrompt, MulliganResponse,
    PendingChoiceRequest, PendingMulliganRequest, PendingPlayerActionRequest, PendingRequest,
    PlayMonster, PlaySpell, PlayerAction, PlayerActionResponse,
)
from souls import SOULS


def compile_player_action(action: PlayerAction, game: Game, player_id: PlayerId) -> tuple[bool, str, Action | None]:
    """Validate a PlayerAction and compile it into an engine Action."""
    if game.turn_player.id != player_id:
        return False, 'not_turn_player', None

    player = game.player(player_id)

    match action:
        case PlayMonster(card_id=card_id, board_slot=board_slot):
            ok, reason = game.can_play_from_hand(player=player, card_id=card_id, pos=board_slot)
            if not ok:
                return False, reason, None

            card = game.entity(card_id)
            return True, 'ok', Play(player=player, card=card, pos=board_slot, allow_cancel=True)

        case PlaySpell(card_id=card_id):
            ok, reason = game.can_play_from_hand(player=player, card_id=card_id)
            if not ok:
                return False, reason, None

            card = game.entity(card_id)
            return True, 'ok', Play(player=player, card=card, allow_cancel=True)

        case Attack(attacker_id=attacker_id, defender_id=defender_id):
            ok, reason = game.can_attack(attacker_id, defender_id, initiated_by_player=player)
            if not ok:
                return False, reason, None

            attacker = game.entity(attacker_id)
            defender = game.entity(defender_id)
            return True, 'ok', AttackAction(attacker=attacker, defender=defender)

        case EndTurn():
            return True, 'ok', PlayerEndTurnAction(player=player)

        case _:
            return False, 'unknown_action', None


@dataclass(slots=True)
class EngineUpdate:
    results: list[ActionResult]
    pending: tuple[PendingRequest, ...]
    game_over: bool


class GameRunner:
    MAX_STEPS = 1_000

    def __init__(self, game: Game, no_initial_shuffle: bool = False):
        self.game = game
        self.no_initial_shuffle = no_initial_shuffle  # used for testing

    # --------------------
    # Setup phase
    # --------------------

    def _step_setup(self) -> EngineUpdate:
        if not self.game.mulligan_offered:
            # Choose starting player
            p1 = self.game.player(PlayerId.P1)
            p2 = self.game.player(PlayerId.P2)

            first_turn_player = self.game.rng.choice([PlayerId.P1, PlayerId.P2])

            p1.is_first_turn = (first_turn_player is PlayerId.P1)
            p2.is_first_turn = (first_turn_player is PlayerId.P2)
            self.game.turn_player = self.game.player(first_turn_player)

            # Setup decks
            for player_id in (PlayerId.P1, PlayerId.P2):
                player = self.game.player(player_id)

                player.soul = SOULS[player.starting_soul_id](id=self.game.alloc_entity_id(), controller_id=player_id)
                self.game.register_entity(player.soul, entity_id=player.soul.id)

                player.artifacts = [
                    ARTIFACTS[artifact_id](id=self.game.alloc_entity_id(), controller_id=player_id)
                    for artifact_id in player.starting_artifact_ids
                ]
                for artifact in player.artifacts:
                    self.game.register_entity(artifact, entity_id=artifact.id)

                player.deck = Deck([
                    self.game.create_card(template_id, controller_id=player_id, zone=CardZone.DECK)
                    for template_id in player.starting_deck_card_ids
                ])

                if not self.no_initial_shuffle:
                    self.game.rng.shuffle(player.deck.cards)

            # Offer cards to mulligan
            offered_cards = {}
            for player_id in (PlayerId.P1, PlayerId.P2):
                player = self.game.player(player_id)
                offered_cards[player_id] = [player.deck.cards[index].id for index in range(3)]

            self.game.mulligan_offered = offered_cards
            self.game.mulligan_replacements = {PlayerId.P1: set(), PlayerId.P2: set()}
            self.game.mulligan_submitted.clear()

        # Check whether players submitted cards to mulligan.
        # For each player that did not, create a mulligan request.
        for player_id in (PlayerId.P1, PlayerId.P2):
            if player_id in self.game.mulligan_submitted:
                continue

            # Don't create a duplicate request if one already exists for this player.
            if any(
                isinstance(req, PendingMulliganRequest) and req.player_id is player_id
                for req in self.game.pending_requests.values()
            ):
                continue

            request_id = self.game.alloc_request_id()
            prompt = MulliganPrompt(
                request_id=request_id,
                player_id=player_id,
                offered_card_ids=tuple(self.game.mulligan_offered[player_id]),
            )
            req = PendingMulliganRequest(request_id=request_id, player_id=player_id, prompt=prompt)
            self.game.pending_requests[request_id] = req

        if self.game.pending_requests:
            # Block until no pending mulligans left
            return EngineUpdate(results=[], pending=self._pending_sorted(), game_over=self.game.game_over)

        assert self.game.mulligan_submitted == {PlayerId.P1, PlayerId.P2}, self.game.mulligan_submitted

        # Finalize mulligan
        for player_id in (PlayerId.P1, PlayerId.P2):
            player = self.game.player(player_id)
            offered_ids = self.game.mulligan_offered[player_id]
            replace_ids = self.game.mulligan_replacements[player_id]

            kept_ids = [card_id for card_id in offered_ids if card_id not in replace_ids]
            replaced_ids = [card_id for card_id in offered_ids if card_id in replace_ids]

            for card_id in kept_ids:
                card = player.deck.get(card_id)
                self.game.move_card(card, player_id, CardZone.HAND)

                if not self.no_initial_shuffle:
                    self.game.rng.shuffle(player.deck.cards)

            for _ in range(len(replaced_ids)):
                self.game.move_card(player.deck.cards[0], player_id, CardZone.HAND)

        # Finalize setup state
        self.game.mulligan_offered = {}
        self.game.mulligan_submitted.clear()
        self.game.setup_complete = True

        # Start first turn
        self.game.enqueue_actions(
            PlayerStartTurnAction(player=self.game.turn_player),
            source=self.game.turn_player,
        )

        return EngineUpdate(results=[], pending=(), game_over=self.game.game_over)

    # --------------------
    # Engine step API
    # --------------------

    def _resolve_one(self) -> list[ActionResult]:
        pending = self.game.resolution_stack.pop()
        try:
            results = self.game._resolve_one(pending)
        except Exception as e:
            raise RuntimeError(
                f"Exception during effect resolution:\n"
                f"Effect: {pending.action!r}\n"
                f"Source: {pending.source!r}\n"
                f"kwargs: {pending.kwargs!r}\n"
                f"env: {pending.env!r}"
            ) from e

        self.game.check_invariants()  # TODO move?

        return results

    def _pending_sorted(self) -> tuple[PendingRequest, ...]:
        return tuple(sorted(self.game.pending_requests.values(), key=lambda r: r.request_id))

    def step(self) -> EngineUpdate:
        """
        Advance the engine by a single "step" if possible.
        Returns an EngineUpdate which includes any ActionResults emitted.
        """
        if self.game.game_over:
            return EngineUpdate(results=[], pending=(), game_over=True)

        # Check if already blocked and waiting for player input
        if self.game.pending_requests:
            return EngineUpdate(results=[], pending=self._pending_sorted(), game_over=False)

        # Setup phase
        if not self.game.setup_complete:
            return self._step_setup()

        # Queue is not empty: resolve one pending action
        if self.game.resolution_stack:
            results = self._resolve_one()
            return EngineUpdate(results=results, pending=self._pending_sorted(), game_over=self.game.game_over)

        # Open game state: request turn player's action
        assert len(self.game.stack) == 0, self.game.stack
        req = PendingPlayerActionRequest(
            request_id=self.game.alloc_request_id(),
            player_id=self.game.turn_player.id,
        )
        self.game.pending_requests[req.request_id] = req
        return EngineUpdate(results=[], pending=self._pending_sorted(), game_over=False)

    def resolve_until_blocked(self, step_limit: int = MAX_STEPS) -> EngineUpdate:
        """
        Resolve until blocked (pending requests exist) or game ends.
        Returns a single batch containing all results that were emitted.
        """
        results = []
        steps = 0

        while not self.game.game_over and steps < step_limit:
            upd = self.step()
            steps += 1

            if upd.results:
                results.extend(upd.results)

            if upd.pending or upd.game_over:
                return EngineUpdate(results=results, pending=upd.pending, game_over=upd.game_over)

        if steps >= step_limit:
            raise RuntimeError("Step limit reached (possible infinite loop).")

        return EngineUpdate(results=results, pending=(), game_over=True)

    # --------------------
    # Player input API
    # --------------------

    def provide_input(self, response: EngineInput) -> tuple[bool, str]:
        """Provide a response to a pending request."""
        try:
            pending = self.game.pending_requests[response.request_id]
        except KeyError:
            if not self.game.pending_requests:
                return False, 'no_pending_requests'
            return False, 'invalid_request_id'

        if isinstance(pending, PendingPlayerActionRequest):
            if not isinstance(response, PlayerActionResponse):
                return False, 'wrong_response_type'
            if self.game.resolution_stack:
                return False, 'game_queue_not_empty'

            ok, reason, action = compile_player_action(response.action, self.game, response.player_id)
            if not ok:
                return False, reason

            assert action is not None
            del self.game.pending_requests[pending.request_id]
            self.game.enqueue_actions(action, source=self.game.player(response.player_id))

            return True, 'ok'

        if isinstance(pending, PendingChoiceRequest):
            if not isinstance(response, ChoiceResponse):
                return False, 'wrong_response_type'

            ok, reason = pending.validate(response)
            if not ok:
                return False, reason

            del self.game.pending_requests[pending.request_id]
            actions = pending.on_choose(response)
            if actions:
                self.game.enqueue_actions(actions, source=self.game.player(response.player_id))

            return True, 'ok'

        if isinstance(pending, PendingMulliganRequest):
            if not isinstance(response, MulliganResponse):
                return False, 'wrong_response_type'

            ok, reason = pending.validate(response)
            if not ok:
                return False, reason

            self.game.mulligan_replacements[response.player_id] = set(response.replace_card_ids)
            self.game.mulligan_submitted.add(response.player_id)
            del self.game.pending_requests[pending.request_id]

            return True, 'ok'

        return False, 'invalid_request_type'
