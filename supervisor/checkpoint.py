import json
from pathlib import Path


class Checkpoint:
    """Simple file-based checkpoint for workflow state."""

    def __init__(self, trace_id: str, base_dir: str = "storage/cache"):
        self._path = Path(base_dir) / f"{trace_id}_checkpoint.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: dict):
        with open(self._path, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def load(self) -> dict:
        if self._path.exists():
            with open(self._path) as f:
                return json.load(f)
        return {}

    def exists(self) -> bool:
        return self._path.exists()

    def clear(self):
        if self._path.exists():
            self._path.unlink()
