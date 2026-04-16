#!/usr/bin/env python3
"""彩票解析模块测试"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import LotteryParser, LotteryTicket, Bet


class TestLotteryParserBasic(unittest.TestCase):
    """基础字段提取测试 (LOT-01, LOT-02, LOT-03)"""

    def setUp(self):
        self.parser = LotteryParser()

    def test_parse_issue(self):
        self.assertEqual(self.parser.parse_issue("第 25042 期"), "25042")
        self.assertEqual(self.parser.parse_issue("第25042期"), "25042")
        self.assertEqual(self.parser.parse_issue("25042期"), "25042")
        self.assertIsNone(self.parser.parse_issue("无效格式"))

    def test_parse_time(self):
        self.assertEqual(self.parser.parse_time("2026-04-16"), "2026-04-16")
        self.assertEqual(self.parser.parse_time("2026/04/16"), "2026/04/16")
        self.assertEqual(self.parser.parse_time("2026-04-16 14:30"), "2026-04-16")
        self.assertIsNone(self.parser.parse_time("无效格式"))

    def test_parse_amount(self):
        self.assertEqual(self.parser.parse_amount("投注金额：￥66"), 66.0)
        self.assertEqual(self.parser.parse_amount("投注金额：66元"), 66.0)
        self.assertEqual(self.parser.parse_amount("投注金额: 66.00"), 66.0)
        self.assertIsNone(self.parser.parse_amount("无效格式"))


class TestLotteryParserBets(unittest.TestCase):
    """投注内容解析测试 (LOT-04, LOT-05, LOT-06)"""

    def setUp(self):
        self.parser = LotteryParser()

    def test_parse_match(self):
        self.assertEqual(self.parser.parse_match("阿根廷 vs 巴西"), "阿根廷 vs 巴西")
        self.assertEqual(self.parser.parse_match("中国 vs 日本"), "中国 vs 日本")
        self.assertIsNone(self.parser.parse_match("无效格式"))

    def test_parse_odds(self):
        self.assertEqual(self.parser.parse_odds("1.85"), [1.85])
        self.assertEqual(self.parser.parse_odds("胜 1.85 平 2.10"), [1.85, 2.10])
        self.assertEqual(self.parser.parse_odds("1.85 2.10 3.50"), [1.85, 2.10, 3.50])
        self.assertEqual(self.parser.parse_odds("无效格式"), [])

    def test_parse_bets_single(self):
        text = "阿根廷 vs 巴西\n胜 1.85"
        bets = self.parser.parse_bets(text)
        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0].match, "阿根廷 vs 巴西")
        self.assertEqual(bets[0].odds, 1.85)

    def test_parse_bets_multiple(self):
        text = """
        阿根廷 vs 巴西
        胜 1.85 平 2.10 负 3.50
        """
        bets = self.parser.parse_bets(text)
        self.assertGreaterEqual(len(bets), 1)


class TestLotteryParserIntegration(unittest.TestCase):
    """完整解析流程测试"""

    def setUp(self):
        self.parser = LotteryParser()

    def test_parse_complete(self):
        ocr_result = {
            "full_text": """
            第 25042 期
            2026-04-16
            投注金额：￥66
            阿根廷 vs 巴西
              胜:1.85  平:2.10  负:3.50
            """
        }

        ticket = self.parser.parse(ocr_result)

        self.assertEqual(ticket.issue_number, "25042")
        self.assertEqual(ticket.bet_time, "2026-04-16")
        self.assertEqual(ticket.total_amount, 66.0)
        self.assertIsNotNone(ticket.bets)

    def test_to_dict(self):
        ticket = LotteryTicket(
            issue_number="25042",
            bet_time="2026-04-16",
            total_amount=66.0,
            bets=[Bet(match="阿根廷 vs 巴西", option="胜", odds=1.85)],
        )

        result = ticket.to_dict()

        self.assertEqual(result["issue_number"], "25042")
        self.assertEqual(result["bet_time"], "2026-04-16")
        self.assertEqual(result["total_amount"], 66.0)
        self.assertEqual(len(result["bets"]), 1)
        self.assertEqual(result["bets"][0]["match"], "阿根廷 vs 巴西")


if __name__ == "__main__":
    unittest.main()
