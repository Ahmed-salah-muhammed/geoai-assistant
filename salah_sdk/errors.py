"""SalahError hierarchy.

Every SDK call raises a SalahError subclass on failure - callers can catch
the base class for an "anything went wrong" handler or the specific class
to react to one failure mode.
"""


class SalahError(Exception):
    """Base class for all Salah SDK errors."""


class MissingKey(SalahError):
    """Raised when the active provider has no API key configured."""

    def __init__(self, provider: str, key_name: str):
        self.provider = provider
        self.key_name = key_name
        super().__init__(
            f"No API key for provider '{provider}'. "
            f"Set {key_name} via SalahClient(...) or as an env var."
        )


class ProviderError(SalahError):
    """Wraps any exception raised by the underlying provider SDK."""

    def __init__(self, provider: str, original: Exception):
        self.provider = provider
        self.original = original
        super().__init__(f"{provider} call failed: {type(original).__name__}: {original}")


class UnknownModel(SalahError):
    """Raised when a caller passes a model ID the SDK does not know about."""


class VisionNotSupported(SalahError):
    """Raised when a vision call targets a text-only model."""
