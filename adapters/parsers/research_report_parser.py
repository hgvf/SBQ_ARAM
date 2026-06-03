from .json_parser import JSONParser


class ResearchReportParser(JSONParser):
    def parse(self, raw: str) -> dict:
        result = super().parse(raw)
        result.setdefault("rating_view", "neutral")
        result.setdefault("investment_thesis", [])
        result.setdefault("key_risks", [])
        result.setdefault("report_markdown", raw if result.get("parse_error") else "")
        return result
