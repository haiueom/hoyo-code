# utils/models.py
from dataclasses import dataclass


@dataclass
class Reward:
    """Represents an in-game reward item."""

    name: str
    image: str


@dataclass
class Duration:
    """Represents the validity period of a code."""

    discovered: str | None = None
    valid: str | None = None
    expired: str | None = None
    notes: str | None = None


@dataclass
class Code:
    """Represents a single promotional code."""

    code: str
    server: str
    status: str
    rewards: list[Reward]
    duration: Duration
    link: str | None = None
