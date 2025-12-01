"""Question dataclass for Polymarket markets."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Question:
    """A resolved Polymarket market question for arena evaluation.

    Attributes:
        id: Unique market identifier
        condition_id: Polymarket condition ID
        question: The prediction question text
        slug: URL-friendly slug
        outcomes: List of outcome labels (e.g., ["Yes", "No"])
        outcome_prices: Resolution prices (e.g., ["1", "0"] means Yes won)
        resolved_outcome: Derived float (1.0 if Yes won, 0.0 if No won)
        resolution_status: Should be "resolved"
        volume: Trading volume in USD
        start_date: When market opened
        end_date: When market was scheduled to end
        closed_time: When market actually closed
        description: Optional detailed description
    """

    id: str
    condition_id: str
    question: str
    slug: str
    outcomes: list[str]
    outcome_prices: list[str]
    resolved_outcome: float
    resolution_status: str
    volume: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    closed_time: Optional[str] = None
    description: Optional[str] = None

    @property
    def resolved_yes(self) -> bool:
        """True if Yes outcome won (outcome_prices[0] == '1')."""
        return len(self.outcome_prices) > 0 and self.outcome_prices[0] == "1"

    @property
    def is_resolved(self) -> bool:
        """True if market is resolved."""
        return self.resolution_status == "resolved"

    @classmethod
    def from_polymarket_json(cls, data: dict) -> "Question":
        """Create Question from polymarket-downloader JSON format.

        Args:
            data: Market dict from polymarket-downloader markets.json

        Returns:
            Question instance

        Example input:
            {
                "id": "abc123",
                "question": "Will X happen?",
                "conditionId": "...",
                "slug": "will-x-happen",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["1", "0"],
                "umaResolutionStatus": "resolved",
                "volume": "12345678",
                ...
            }
        """
        outcome_prices = data.get("outcomePrices", ["0", "0"])

        # Derive resolved_outcome: 1.0 if Yes won, 0.0 if No won
        # outcomePrices[0] == "1" means the first outcome (Yes) won
        resolved_outcome = 1.0 if (len(outcome_prices) > 0 and outcome_prices[0] == "1") else 0.0

        return cls(
            id=data.get("id", ""),
            condition_id=data.get("conditionId", ""),
            question=data.get("question", ""),
            slug=data.get("slug", ""),
            outcomes=data.get("outcomes", ["Yes", "No"]),
            outcome_prices=outcome_prices,
            resolved_outcome=resolved_outcome,
            resolution_status=data.get("umaResolutionStatus", ""),
            volume=float(data.get("volume", 0)),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            closed_time=data.get("closedTime"),
            description=data.get("description"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "condition_id": self.condition_id,
            "question": self.question,
            "slug": self.slug,
            "outcomes": self.outcomes,
            "outcome_prices": self.outcome_prices,
            "resolved_outcome": self.resolved_outcome,
            "resolution_status": self.resolution_status,
            "volume": self.volume,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "closed_time": self.closed_time,
            "description": self.description,
        }

    def __repr__(self) -> str:
        outcome = "Yes" if self.resolved_yes else "No"
        return f"Question(id={self.id[:8]}..., question='{self.question[:50]}...', resolved={outcome})"
