from .json_parser import JSONParser


class TradingDecisionParser(JSONParser):
    def parse(self, raw: str) -> dict:
        result = super().parse(raw)
        # Ensure required fields exist with defaults
        result.setdefault("decision", "hold")
        result.setdefault("confidence", 0.5)
        result.setdefault("bull_case", [])
        result.setdefault("bear_case", [])
        return result
