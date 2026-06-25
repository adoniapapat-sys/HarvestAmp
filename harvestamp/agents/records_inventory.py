# harvestamp/agents/records_inventory.py
from harvestamp.agents.specialists import RecordsAgent

class RecordsInventoryAgent(RecordsAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Records + Inventory Agent"
