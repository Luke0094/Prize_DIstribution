"""
DistributionEngine
==================
Tre casi, in base al rapporto quantità / n_partecipanti:

  Case A  qty == n_partecipanti
    → 1 premio esatto a ciascuno.

  Case B  qty < n_partecipanti
    → Ordina i partecipanti per danno decrescente.
      I primi `qty` ricevono esattamente 1 premio ciascuno.
      Gli altri ricevono 0.
      (Parità di danno → tiebreak per id ascendente.)

  Case C  qty > n_partecipanti
    → 1 premio garantito a ciascuno (minimum).
      Le unità rimanenti (qty - n) vengono distribuite
      proporzionalmente al danno con il metodo
      Largest Remainder / Hamilton:
        exact_i  = remaining * (damage_i / total_damage)
        base_i   = floor(exact_i)
        leftover = remaining - Σbase_i
        +1 ai `leftover` partecipanti con resto frazionario maggiore
          (tiebreak: id ascendente).
      Risultato finale = 1 + base_i [+ eventuale +1 dal passo precedente].
      Garanzia: Σquote == qty esatto, ogni partecipante ≥ 1.
"""

from typing import List, Tuple
from models.participant import Participant


class DistributionEngine:

    @staticmethod
    def calculate(
        participants: List[Participant],
        total_damage: float,
        quantity: float,
        integer_only: bool,
    ) -> List[Tuple[int, str, float]]:
        if not participants or total_damage <= 0:
            return []
        if integer_only:
            return DistributionEngine._integer_dist(participants, total_damage, quantity)
        return DistributionEngine._float_dist(participants, total_damage, quantity)

    # ── Float distribution (non-integer) ─────────────────────────────────────

    @staticmethod
    def _float_dist(
        participants: List[Participant],
        total_damage: float,
        quantity: float,
    ) -> List[Tuple[int, str, float]]:
        return [
            (p.id, p.name, quantity * (p.damage / total_damage))
            for p in sorted(participants, key=lambda x: x.id)
        ]

    # ── Integer distribution ─────────────────────────────────────────────────

    @staticmethod
    def _integer_dist(
        participants: List[Participant],
        total_damage: float,
        quantity: float,
    ) -> List[Tuple[int, str, float]]:
        total_int = int(quantity)
        n         = len(participants)

        # ── Case A: exactly one each ──────────────────────────────────────
        if total_int == n:
            return [
                (p.id, p.name, 1.0)
                for p in sorted(participants, key=lambda x: x.id)
            ]

        # ── Case B: fewer prizes than participants ────────────────────────
        # Top `total_int` participants by damage get 1 each, rest get 0.
        if total_int < n:
            ranked = sorted(
                participants,
                key=lambda p: (-p.damage, p.id)   # damage desc, id asc for ties
            )
            winners = {p.id for p in ranked[:total_int]}
            return [
                (p.id, p.name, 1.0 if p.id in winners else 0.0)
                for p in sorted(participants, key=lambda x: x.id)
            ]

        # ── Case C: more prizes than participants ─────────────────────────
        # Reserve 1 per participant, then distribute the remainder by Hamilton.
        remaining = total_int - n
        return DistributionEngine._hamilton_with_bonus(
            participants, total_damage, remaining, bonus=1
        )

    # ── Hamilton / Largest Remainder helper ───────────────────────────────────

    @staticmethod
    def _hamilton_with_bonus(
        participants: List[Participant],
        total_damage: float,
        distribute: int,
        bonus: int,
    ) -> List[Tuple[int, str, float]]:
        """
        Distribute *distribute* units proportionally (Hamilton method),
        then add *bonus* to every participant.
        """
        sorted_p = sorted(participants, key=lambda x: x.id)
        entries  = []
        for p in sorted_p:
            if distribute > 0:
                exact     = distribute * (p.damage / total_damage)
                floor_val = int(exact)
                rem       = exact - floor_val
            else:
                floor_val = 0
                rem       = 0.0
            entries.append({"p": p, "floor": floor_val, "rem": rem})

        leftover = distribute - sum(e["floor"] for e in entries)
        ranked   = sorted(
            range(len(entries)),
            key=lambda i: (-entries[i]["rem"], entries[i]["p"].id),
        )
        for rank, idx in enumerate(ranked):
            if rank < leftover:
                entries[idx]["floor"] += 1

        return [
            (e["p"].id, e["p"].name, float(e["floor"] + bonus))
            for e in entries
        ]

    # ── Number formatting ─────────────────────────────────────────────────────

    @staticmethod
    def format_number(value: float, force_integer: bool = False) -> str:
        if force_integer:
            return str(int(round(value)))
        return f"{value:.10f}".rstrip("0").rstrip(".")
