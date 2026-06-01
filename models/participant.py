from dataclasses import dataclass, asdict


@dataclass
class Participant:
    id: int
    name: str
    damage: float
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Participant":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def copy(self) -> "Participant":
        return Participant(**self.to_dict())
