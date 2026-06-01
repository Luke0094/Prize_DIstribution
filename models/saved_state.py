from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .date_range import DateRange
from .prize import Prize
from .participant import Participant


@dataclass
class SavedState:
    date_range: DateRange
    event: str
    prizes: List[Prize]
    participants: List[Participant]
    distributions: Dict[int, List[Tuple]]
    total_damage: float = 0.0
    saved_date: str = ""

    def to_dict(self) -> dict:
        return {
            "date_range": self.date_range.to_dict(),
            "event": self.event,
            "prizes": [p.to_dict() for p in self.prizes],
            "participants": [p.to_dict() for p in self.participants],
            "distributions": {str(k): v for k, v in self.distributions.items()},
            "total_damage": self.total_damage,
            "saved_date": self.saved_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SavedState":
        for field_name in ("date_range", "prizes", "participants", "distributions"):
            if field_name not in data:
                raise KeyError(f"Missing field: {field_name}")
        return cls(
            date_range=DateRange.from_dict(data["date_range"]),
            event=data.get("event", ""),
            prizes=[Prize.from_dict(p) for p in data["prizes"]],
            participants=[Participant.from_dict(p) for p in data["participants"]],
            distributions={
                int(k): [tuple(row) for row in v]
                for k, v in data.get("distributions", {}).items()
            },
            total_damage=data.get("total_damage", 0.0),
            saved_date=data.get("saved_date", ""),
        )
