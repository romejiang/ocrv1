"""彩票票面解析模块 - 从 OCR 结果中提取彩票专属字段"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class Bet:
    match: str
    option: str
    odds: float


@dataclass
class LotteryTicket:
    issue_number: Optional[str] = None
    bet_time: Optional[str] = None
    total_amount: Optional[float] = None
    bets: List[Bet] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "issue_number": self.issue_number,
            "bet_time": self.bet_time,
            "total_amount": self.total_amount,
            "bets": [
                {"match": b.match, "option": b.option, "odds": b.odds}
                for b in self.bets
            ],
        }


class LotteryParser:
    ISSUE_PATTERN = re.compile(r"(?:第\s*)?(\d{5,6})\s*期")
    DATE_PATTERN = re.compile(r"(\d{4}[-/]\d{2}[-/]\d{2})")
    AMOUNT_PATTERN = re.compile(r"投注金额[:：]?\s*[￥$]?\s*(\d+(?:\.\d{1,2})?)")
    ODDS_PATTERN = re.compile(r"(\d+\.\d{2})")
    MATCH_PATTERN = re.compile(r"([\u4e00-\u9fa5]+)\s*vs\s*([\u4e00-\u9fa5]+)")
    OPTION_PATTERN = re.compile(r"(胜|平|负|主胜|客胜|主负)")

    def parse_issue(self, text: str) -> Optional[str]:
        match = self.ISSUE_PATTERN.search(text)
        return match.group(1) if match else None

    def parse_time(self, text: str) -> Optional[str]:
        match = self.DATE_PATTERN.search(text)
        return match.group(1) if match else None

    def parse_amount(self, text: str) -> Optional[float]:
        match = self.AMOUNT_PATTERN.search(text)
        return float(match.group(1)) if match else None

    def parse_match(self, text: str) -> Optional[str]:
        match = self.MATCH_PATTERN.search(text)
        if match:
            return f"{match.group(1)} vs {match.group(2)}"
        return None

    def parse_odds(self, text: str) -> List[float]:
        return [float(m) for m in self.ODDS_PATTERN.findall(text)]

    def _infer_option(self, segment: str) -> str:
        option_match = self.OPTION_PATTERN.search(segment)
        return option_match.group(1) if option_match else "未知"

    def _find_closest_odds(self, text: str, anchor_pos: int) -> float:
        odds_matches = list(self.ODDS_PATTERN.finditer(text))
        if not odds_matches:
            return 0.0

        closest = min(odds_matches, key=lambda m: abs(m.start() - anchor_pos))
        return float(closest.group(1))

    def _get_context_around_match(
        self, text: str, match_pos: int, window: int = 50
    ) -> str:
        start = max(0, match_pos - window)
        end = min(len(text), match_pos + window)
        return text[start:end]

    def parse_bets(self, text: str) -> List[Bet]:
        bets = []
        odds_values = self.parse_odds(text)

        if len(odds_values) == 0:
            return bets

        match_pattern = self.MATCH_PATTERN
        match_matches = list(match_pattern.finditer(text))

        if not match_matches:
            return bets

        for i, match_obj in enumerate(match_matches):
            match_name = f"{match_obj.group(1)} vs {match_obj.group(2)}"
            match_pos = match_obj.start()

            context = self._get_context_around_match(text, match_pos)
            option = self._infer_option(context)

            odds = self._find_closest_odds(context, len(context) // 2)

            if odds > 0:
                bets.append(Bet(match=match_name, option=option, odds=odds))

        return bets

    def parse(self, ocr_result: Dict) -> LotteryTicket:
        text = ocr_result.get("full_text", "")

        ticket = LotteryTicket(
            issue_number=self.parse_issue(text),
            bet_time=self.parse_time(text),
            total_amount=self.parse_amount(text),
        )

        bets = self.parse_bets(text)
        ticket.bets = bets

        return ticket


def main():
    import json
    import argparse

    parser = argparse.ArgumentParser(description="解析彩票 OCR 结果")
    parser.add_argument("ocr_json", help="OCR 结果 JSON 文件路径")
    args = parser.parse_args()

    with open(args.ocr_json, "r", encoding="utf-8") as f:
        ocr_result = json.load(f)

    lottery_parser = LotteryParser()
    ticket = lottery_parser.parse(ocr_result)

    print(json.dumps(ticket.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
