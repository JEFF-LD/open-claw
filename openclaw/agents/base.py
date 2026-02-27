"""
Base agent. Minimal: logging + error wrapping.
"""

import logging
import traceback
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self):
        self.log = logging.getLogger(f"openclaw.{self.name}")

    def run(self, **kwargs) -> dict:
        self.log.info("[%s] starting", self.name)
        try:
            result = self.execute(**kwargs)
            self.log.info("[%s] done", self.name)
            return {"ok": True, "result": result}
        except Exception as e:
            self.log.error("[%s] failed: %s\n%s", self.name, e, traceback.format_exc())
            return {"ok": False, "error": str(e)}

    @abstractmethod
    def execute(self, **kwargs):
        ...
