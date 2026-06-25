# harvestamp/agents/weather_fieldwork.py
from harvestamp.agents.specialists import WeatherAgent

class WeatherFieldworkAgent(WeatherAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "Weather + Fieldwork Agent"
