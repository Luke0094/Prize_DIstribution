from dataclasses import dataclass, asdict


@dataclass
class Prize:
    id: int
    name: str
    quantity: float
    is_special: bool = False
    top_winners: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Prize":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def copy(self) -> "Prize":
        return Prize(**self.to_dict())
