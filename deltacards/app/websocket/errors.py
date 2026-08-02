class WebSocketTransportError(Exception):
    """Base class for WebSocket transport failures."""


class FatalProtocolError(WebSocketTransportError):
    """
    Raised on malformed or impossible frontend command.

    The socket should receive getGameError and then be closed.
    """

    def __init__(
        self,
        message: str,
        *,
        translation_key: str = 'game-error-invalid-command',
        translation_args: tuple[object, ...] = (),
    ):
        super().__init__(message)
        self.translation_key = translation_key
        self.translation_args = translation_args


class UnsupportedFrontendRequestError(WebSocketTransportError):
    """
    Raised when the engine requests a choice the existing browser frontend
    cannot represent.
    """


class PlayerUnavailableError(WebSocketTransportError):
    """Raised when a requested player seat belongs to a bot."""
