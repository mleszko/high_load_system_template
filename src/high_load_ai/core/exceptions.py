class ApplicationError(Exception):
    """Base application-level exception."""


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""


class RateLimitExceededError(ApplicationError):
    """Raised when request quota is exceeded."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


class NotFoundError(ApplicationError):
    """Raised when resource does not exist."""
