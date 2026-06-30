# harvestamp/agents/procurement.py
from typing import Any, Dict, List, Optional
from harvestamp.agents.specialists import ProcurementAgent as SpecialistProcurementAgent

class ProcurementAgent(SpecialistProcurementAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Input Procurement Agent"

    def run(self, work_item: Dict[str, Any], context: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        finding = super().run(work_item, context, *args, **kwargs)
        if isinstance(finding, list):
            for f in finding:
                self._fix_missing_data(f)
        elif finding:
            self._fix_missing_data(finding)
        return finding

    def _fix_missing_data(self, f: Dict[str, Any]):
        if "missing_data" in f:
            new_missing = []
            for item in f["missing_data"]:
                if item in ["expected harvest volume", "expected harvest volumes"]:
                    new_missing.append("expected harvest volume for unharvested blocks")
                else:
                    new_missing.append(item)
            f["missing_data"] = new_missing
