import argparse
import asyncio
import re
import signal
from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from deltacards.content.loader import load
from deltacards.model.enums import PlayerId

from .config import ServerConfig
from .errors import FatalProtocolError, PlayerUnavailableError
from .games import GameRegistry
from .serializers import json_text
from .session import WebSocketSession, fatal_error_event


class WebSocketApplication:
    def __init__(
        self,
        config: ServerConfig | None = None,
    ):
        self.config = config or ServerConfig()
        self.registry = GameRegistry(self.config)

    @staticmethod
    def _parse_endpoint(
        connection: ServerConnection,
    ) -> tuple[int, PlayerId]:
        parsed = urlsplit(connection.request.path)
        path_match = re.fullmatch(r'^/game/([1-9][0-9]*)$', parsed.path)
        if path_match is None:
            raise FatalProtocolError(
                f"Invalid game endpoint {parsed.path!r}"
            )

        query = parse_qs(parsed.query, keep_blank_values=True)

        player_values = query['player_id']
        if player_values[0] not in ('1', '2'):
            raise FatalProtocolError("player_id must be 1 or 2")

        game_id = int(path_match.group(1))
        player_id = PlayerId(int(player_values[0]))

        return game_id, player_id

    async def handler(
        self,
        connection: ServerConnection,
    ) -> None:
        try:
            game_id, player_id = self._parse_endpoint(connection)
            hosted = await self.registry.get_or_create(
                game_id=game_id,
                player_id=player_id,
            )

        except PlayerUnavailableError:
            await self._fail_connection(
                connection,
                'game-error-player-unavailable',
            )
            return

        except FatalProtocolError as exc:
            await self._fail_connection(
                connection,
                exc.translation_key,
                *exc.translation_args,
            )
            return

        except Exception:
            await self._fail_connection(
                connection,
                'game-error-internal',
            )
            raise

        session = WebSocketSession(
            websocket=connection,
            hosted=hosted,
            player_id=player_id,
        )
        await session.run()

    @staticmethod
    async def _fail_connection(
        connection: ServerConnection,
        translation_key: str,
        *translation_args: object,
    ) -> None:
        try:
            await connection.send(
                json_text(
                    fatal_error_event(
                        translation_key,
                        *translation_args,
                    ),
                )
            )
        except ConnectionClosed:
            return

        try:
            await connection.close(
                code=1008,
                reason="Connection rejected",
            )
        except ConnectionClosed:
            pass


async def run_server(
    config: ServerConfig | None = None,
) -> None:
    config = config or ServerConfig()
    load()

    application = WebSocketApplication(config)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for signal_name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signal_name, stop_event.set)
        except (NotImplementedError, RuntimeError):
            pass

    print(f"Starting WebSocket server on ws://{config.host}:{config.port}")

    async with serve(
        application.handler,
        config.host,
        config.port,
        max_size=config.max_message_size,
    ):
        await stop_event.wait()


def parse_args() -> argparse.Namespace:
    defaults = ServerConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host',
        default=defaults.host,
    )
    parser.add_argument(
        '--port',
        type=int,
        default=defaults.port,
    )
    parser.add_argument('--human-deck')
    parser.add_argument('--bot-deck')
    parser.add_argument(
        '--seed-base',
        type=int,
        default=defaults.game_seed_base,
        help=(
            'Base seed used to derive deterministic per-game seeds. '
            'The game ID is added to this value.'
        ),
    )
    parser.add_argument('--no-animations', action='store_true')
    parser.add_argument('--no-wait-times', action='store_true')
    return parser.parse_args()


def config_from_args(
    args: argparse.Namespace,
) -> ServerConfig:
    config = ServerConfig()
    presentation = replace(
        config.presentation,
        emit_animation_events=not args.no_animations,
        wait_times_enabled=not args.no_wait_times,
    )

    return replace(
        config,
        host=args.host or config.host,
        port=args.port if args.port is not None else config.port,
        presentation=presentation,
        human_deck_name=(
            args.human_deck
            if args.human_deck is not None
            else config.human_deck_name
        ),
        bot_deck_name=(
            args.bot_deck
            if args.bot_deck is not None
            else config.bot_deck_name
        ),
    )


def main() -> None:
    try:
        asyncio.run(run_server(config_from_args(parse_args())))
    except KeyboardInterrupt:
        pass
