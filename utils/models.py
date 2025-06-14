# utils/models.py
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Reward:
    """Represents an in-game reward item."""

    name: str
    image: str


@dataclass
class Duration:
    """Represents the validity period of a code."""

    discovered: Optional[str] = None
    valid: Optional[str] = None
    expired: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Code:
    """Represents a single promotional code."""

    code: str
    server: str
    status: str
    rewards: List[Reward]
    duration: Duration
    link: Optional[str] = None
