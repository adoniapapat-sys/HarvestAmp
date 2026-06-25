# harvestamp/agents/compliance.py
from harvestamp.agents.specialists import ComplianceAgent as SpecialistComplianceAgent

class ComplianceAgent(SpecialistComplianceAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Compliance Agent"
