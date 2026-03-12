from __future__ import annotations

from collections import deque
from typing import Callable, Deque, List

from .models import LogEntry


class LogService:
    def __init__(self, limit: int = 200) -> None:
        self._entries: Deque[LogEntry] = deque(maxlen=limit)
        self._listeners: List[Callable[[LogEntry], None]] = []

    def subscribe(self, listener: Callable[[LogEntry], None]) -> None:
        self._listeners.append(listener)

    def set_limit(self, limit: int) -> None:
        self._entries = deque(self._entries, maxlen=limit)

    def add(self, entry: LogEntry) -> None:
        self._entries.appendleft(entry)
        for listener in list(self._listeners):
            listener(entry)

    def entries(self) -> List[LogEntry]:
        return list(self._entries)
