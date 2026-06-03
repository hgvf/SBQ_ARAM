from adapters.parsers.json_parser import JSONParser
from adapters.parsers.trading_decision_parser import TradingDecisionParser
from adapters.parsers.research_report_parser import ResearchReportParser


def test_json_parser_valid():
    p = JSONParser()
    result = p.parse('{"decision": "buy", "confidence": 0.8}')
    assert result["decision"] == "buy"


def test_json_parser_markdown_block():
    p = JSONParser()
    raw = '```json\n{"decision": "sell"}\n```'
    result = p.parse(raw)
    assert result["decision"] == "sell"


def test_trading_decision_parser_defaults():
    p = TradingDecisionParser()
    result = p.parse("invalid json")
    assert "decision" in result
    assert "confidence" in result


def test_research_report_parser_defaults():
    p = ResearchReportParser()
    result = p.parse("invalid json")
    assert "rating_view" in result
    assert "investment_thesis" in result
