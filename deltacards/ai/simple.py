from deltacards.ai import GameAI
from deltacards.engine.runner import GameRunner
from deltacards.model.requests import (
    ChoiceResponse, ChooseEntityPrompt, EndTurn, EngineInput,
    MulliganResponse,
    PendingChoiceRequest,
    PendingMulliganRequest,
    PendingPlayerActionRequest,
    PendingRequest, PlayerActionResponse,
)


class SimpleAI(GameAI):
    def choose_mulligan_response(self, runner: GameRunner, request: PendingMulliganRequest) -> MulliganResponse:
        replace_ids: list[int] = []

        for card_id in request.prompt.offered_card_ids:
            if runner.game.card(card_id).cost > 5:
                replace_ids.append(card_id)

        return MulliganResponse(
            request_id=request.request_id,
            player_id=request.player_id,
            replace_card_ids=tuple(replace_ids),
        )

    def choose_player_action_response(
        self,
        runner: GameRunner,
        request: PendingPlayerActionRequest,
    ) -> PlayerActionResponse:
        # End turn only when no other actions are available
        actions = [
            a for a in runner.legal_player_actions(request.player_id)
            if not isinstance(a, EndTurn)
        ]
        if actions:
            action = runner.game.rng.choice(actions)
        else:
            action = EndTurn()

        return PlayerActionResponse(
            request_id=request.request_id,
            player_id=request.player_id,
            action=action,
        )

    def choose_choice_response(self, runner: GameRunner, request: PendingChoiceRequest) -> ChoiceResponse:
        prompt = request.prompt
        if not isinstance(prompt, ChooseEntityPrompt):
            raise TypeError(f"Unsupported `ChoicePrompt` type: {type(prompt).__name__}")

        selected_option = runner.game.rng.choice(prompt.options)
        return ChoiceResponse(
            request_id=request.request_id,
            player_id=request.player_id,
            selected_option_ids=(selected_option.id,),
        )

    def choose_response(self, runner: GameRunner, request: PendingRequest) -> EngineInput:
        if isinstance(request, PendingMulliganRequest):
            return self.choose_mulligan_response(runner, request)

        if isinstance(request, PendingPlayerActionRequest):
            return self.choose_player_action_response(runner, request)

        if isinstance(request, PendingChoiceRequest):
            return self.choose_choice_response(runner, request)

        raise TypeError(f"Unsupported `PendingRequest` type: {type(request).__name__}")
