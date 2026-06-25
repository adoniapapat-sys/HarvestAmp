# harvestamp/agents/market_sales.py
from harvestamp.agents.specialists import MarketAgent

class MarketSalesAgent(MarketAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Market + Sales Agent"
