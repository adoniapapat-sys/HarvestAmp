# harvestamp/agents/margin_scenario.py
from harvestamp.agents.specialists import MarginAgent

class MarginScenarioAgent(MarginAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Margin + Scenario Agent"
