import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.saved_state import SavedState


class StateManager:
    def __init__(self, data_folder: str = "saved_states", backup_folder: str = "backups"):
        self.data_folder = data_folder
        self.backup_folder = backup_folder
        os.makedirs(data_folder, exist_ok=True)
        os.makedirs(backup_folder, exist_ok=True)
        self.states: List[SavedState] = []
        self.load_all()

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_all(self):
        self.states = []
        folder = Path(self.data_folder)
        for fpath in sorted(folder.glob("*.json")):
            try:
                with open(fpath, encoding="utf-8") as f:
                    raw = json.load(f)
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    try:
                        self.states.append(SavedState.from_dict(item))
                    except Exception as e:
                        print(f"[StateManager] Skipping item in {fpath.name}: {e}")
            except Exception as e:
                print(f"[StateManager] Cannot read {fpath.name}: {e}")

    # ── Save / Update ─────────────────────────────────────────────────────────

    def save(self, state: SavedState) -> str:
        """Persist a state. Returns the filename written."""
        state.saved_date = datetime.now().isoformat()
        fname = self._fname_for(state)
        fpath = Path(self.data_folder) / fname

        # Load existing records in that file
        existing: list = []
        if fpath.exists():
            try:
                with open(fpath, encoding="utf-8") as f:
                    raw = json.load(f)
                existing = raw if isinstance(raw, list) else [raw]
            except Exception:
                existing = []

        # Replace if event+date already present, else append
        target = state.to_dict()
        replaced = False
        for i, item in enumerate(existing):
            if (item.get("event") == state.event and
                    item.get("date_range") == state.date_range.to_dict()):
                existing[i] = target
                replaced = True
                break
        if not replaced:
            existing.append(target)

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        self.load_all()
        return fname

    def delete(self, state: SavedState):
        fname = self._fname_for(state)
        fpath = Path(self.data_folder) / fname
        if not fpath.exists():
            return
        try:
            with open(fpath, encoding="utf-8") as f:
                existing = json.load(f)
            existing = existing if isinstance(existing, list) else [existing]
            existing = [
                item for item in existing
                if not (item.get("event") == state.event and
                        item.get("date_range") == state.date_range.to_dict())
            ]
            if existing:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)
            else:
                fpath.unlink()
        except Exception as e:
            print(f"[StateManager] delete error: {e}")
        self.load_all()

    # ── Export / Import ───────────────────────────────────────────────────────

    def export_json(self, path: str, states: Optional[List[SavedState]] = None):
        data = [s.to_dict() for s in (states or self.states)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_json(self, path: str) -> List[SavedState]:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        items = raw if isinstance(raw, list) else [raw]
        imported = []
        for item in items:
            s = SavedState.from_dict(item)
            self.save(s)
            imported.append(s)
        self.load_all()
        return imported

    # ── Backup ────────────────────────────────────────────────────────────────

    def create_backup(self, retention: int = 10) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"backup_{ts}.json"
        fpath = Path(self.backup_folder) / fname
        self.export_json(str(fpath))
        self._cleanup_backups(retention)
        return fname

    def restore_backup(self, backup_path: str):
        self.import_json(backup_path)

    def list_backups(self) -> List[str]:
        folder = Path(self.backup_folder)
        if not folder.exists():
            return []
        return sorted(
            [f.name for f in folder.glob("backup_*.json")],
            reverse=True,
        )

    def _cleanup_backups(self, retention: int):
        backups = self.list_backups()
        for old in backups[retention:]:
            try:
                (Path(self.backup_folder) / old).unlink()
            except OSError:
                pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fname_for(state: SavedState) -> str:
        yr = state.date_range.start_year
        mo = state.date_range.start_month
        return f"{yr}_{mo:02d}.json"
