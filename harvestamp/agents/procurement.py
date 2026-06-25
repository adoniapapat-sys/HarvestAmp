# harvestamp/agents/procurement.py
from harvestamp.agents.specialists import ProcurementAgent as SpecialistProcurementAgent

class ProcurementAgent(SpecialistProcurementAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Input Procurement Agent"
