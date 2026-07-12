from abc import ABC, abstractmethod
from dataclasses import dataclass

from deltacards.engine.runner import EngineUpdate, GameRunner
from deltacards.model.enums import PlayerId
from deltacards.model.requests import EngineInput, PendingRequest


class GameAI(ABC):
    @abstractmethod
    def choose_response(self, runner: GameRunner, request: PendingRequest) -> EngineInput:
        pass


@dataclass(slots=True)
class AIGameController:
    runner: GameRunner
    agents: dict[PlayerId, GameAI]

    def resolve_until_blocked(
        self,
        *,
        max_ai_inputs: int = 1_000,
    ) -> EngineUpdate:
        all_results = []
        all_log_records = []

        for _ in range(max_ai_inputs):
            update = self.runner.resolve_until_blocked()
            if update.results is not None:
                all_results.extend(update.results)
            if update.log_records is not None:
                all_log_records.extend(update.log_records)

            if update.game_over:
                return EngineUpdate(
                    results=all_results,
                    pending=update.pending,
                    game_over=update.game_over,
                    log_records=all_log_records,
                )

            unhandled_requests = [
                request for request in update.pending
                if request.player_id not in self.agents
            ]

            if unhandled_requests:
                return EngineUpdate(
                    results=all_results,
                    pending=update.pending,
                    game_over=update.game_over,
                    log_records=all_log_records,
                )

            for request in update.pending:
                ai = self.agents[request.player_id]
                response = ai.choose_response(self.runner, request)

                ok, reason = self.runner.provide_input(response)
                if not ok:
                    raise RuntimeError(
                        "AI produced a response rejected by runner: "
                        f"{reason}; request={request!r}; response={response!r}"
                    )

        raise RuntimeError("AI input limit reached (possible infinite loop).")
