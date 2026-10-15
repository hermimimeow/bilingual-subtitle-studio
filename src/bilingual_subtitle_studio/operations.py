"""Helpers for stopping long-running transcription and translation jobs."""

class OperationCancelled(RuntimeError):
    """Raised when a user requests cancellation of a long-running operation."""
