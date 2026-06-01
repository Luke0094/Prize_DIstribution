from dataclasses import dataclass, field, asdict
from calendar import monthrange
from datetime import date
from typing import Optional


@dataclass
class DateRange:
    start_year: int
    start_month: int
    start_day: Optional[int] = None
    end_year: Optional[int] = None
    end_month: Optional[int] = None
    end_day: Optional[int] = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _start_date(self) -> date:
        return date(self.start_year, self.start_month, self.start_day or 1)

    def _end_date(self) -> date:
        ey = self.end_year or self.start_year
        em = self.end_month or self.start_month
        ed = self.end_day or monthrange(ey, em)[1]
        return date(ey, em, ed)

    # ── Validation ────────────────────────────────────────────────────────────

    def is_valid(self) -> bool:
        """True if start ≤ end (or no end set)."""
        if not any([self.end_year, self.end_month, self.end_day]):
            return True
        return self._start_date() <= self._end_date()

    def overlaps(self, other: "DateRange") -> bool:
        s, e = self._start_date(), self._end_date()
        os, oe = other._start_date(), other._end_date()
        return not (e < os or s > oe)

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DateRange":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __str__(self) -> str:
        s = f"{self.start_year}-{self.start_month:02d}"
        if self.start_day:
            s += f"-{self.start_day:02d}"
        if not any([self.end_year, self.end_month, self.end_day]):
            return s
        ey = self.end_year or self.start_year
        em = self.end_month or self.start_month
        e = f"{ey}-{em:02d}"
        if self.end_day:
            e += f"-{self.end_day:02d}"
        return f"{s} → {e}"
