"""Ngăn phản hồi stop rỗng bị báo nhầm là câu trả lời hoàn chỉnh."""
import unittest

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final


class FinalAnswerTests(unittest.TestCase):
    def test_empty_stop_is_not_completed(self):
        for text in ('', None, '   '):
            with self.subTest(content=text):
                result = run_agent('Kiểm tra GitHub', FakeProvider([final(text)]), StatusTools())
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['answer'], '')
                self.assertEqual(result['trace'][-1]['event'], 'error')


if __name__ == '__main__':
    unittest.main()
