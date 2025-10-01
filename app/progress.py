from typing import Dict, Any


class ProgressStore:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def init(self, job_id: str, title: str = "Job"):
        self._store[job_id] = {
            "title": title,
            "percent": 0,
            "status": "running",
            "logs": ["Job started"],
        }

    def get(self, job_id: str):
        return self._store.get(job_id)

    def update(self, job_id: str, percent: int, message: str):
        state = self._store.get(job_id)
        if not state:
            return
        state["percent"] = percent
        state["logs"].append(message)
        state["status"] = "running" if percent < 100 else "done"

    def log(self, job_id: str, message: str):
        state = self._store.get(job_id)
        if not state:
            return
        state["logs"].append(message)

    def set_status(self, job_id: str, status: str):
        state = self._store.get(job_id)
        if not state:
            return
        state["status"] = status

