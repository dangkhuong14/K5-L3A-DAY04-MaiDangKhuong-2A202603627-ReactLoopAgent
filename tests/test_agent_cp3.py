"""CP3: phục hồi sau tool error, dừng đúng và giữ trace đủ để debug."""
import json
import unittest
from unittest.mock import Mock

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class RobustnessTests(unittest.TestCase):
    def test_provider_error_ends_run_without_logging_exception_secret(self):
        provider = Mock()
        provider.complete.side_effect = RuntimeError('sensitive-provider-token')
        tools = Mock()
        result = run_agent('Kiểm tra', provider, tools)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['trace'][-1]['event'], 'error')
        self.assertIn('RuntimeError', result['error'])
        self.assertNotIn('sensitive-provider-token', json.dumps(result))
        tools.execute.assert_not_called()

    def test_tool_errors_are_returned_to_model_with_original_call_id(self):
        cases = [
            ('missing', '{}', StatusTools(), 'UNKNOWN_TOOL'),
            ('get_status', '{"provider":"invalid"}', StatusTools(), 'ValueError'),
            ('get_status', '{"provider":"github"}', StatusTools(fail=True), 'TimeoutError'),
        ]
        for name, arguments, tools, expected_error in cases:
            with self.subTest(error=expected_error):
                provider = FakeProvider([
                    tool_call('failed-call', name, arguments),
                    final('Chưa đủ dữ liệu để kết luận.'),
                ])
                result = run_agent('Kiểm tra', provider, tools)
                self.assertEqual(result['status'], 'completed')
                observation = provider.histories[1][-1]
                self.assertEqual(observation['tool_call_id'], 'failed-call')
                self.assertEqual(json.loads(observation['content'])['error'], expected_error)
                self.assertEqual(result['trace'][1]['result']['error'], expected_error)

    def test_unhandled_tool_exception_is_an_observation(self):
        tools = Mock()
        tools.execute.side_effect = TimeoutError('internal timeout details')
        provider = FakeProvider([
            tool_call('timeout', 'get_status', '{"provider":"github"}'),
            final('Không kiểm tra được GitHub.'),
        ])
        result = run_agent('Kiểm tra', provider, tools)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'], 'TimeoutError')

    def test_non_object_json_arguments_do_not_execute_tool(self):
        for arguments in ('[]', 'null', '42', '"github"'):
            with self.subTest(arguments=arguments):
                tools = Mock()
                provider = FakeProvider([
                    tool_call('bad-args', 'get_status', arguments), final('Thiếu tham số hợp lệ.'),
                ])
                result = run_agent('Kiểm tra', provider, tools)
                self.assertEqual(result['status'], 'completed')
                self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'], 'INVALID_ARGUMENTS')
                tools.execute.assert_not_called()

    def test_abnormal_finish_does_not_execute_partial_tool_calls(self):
        for finish in ('length', 'content_filter', None):
            with self.subTest(finish=finish):
                response = tool_call('partial', 'get_status', '{"provider":"github"}')
                response['finish'] = finish
                tools = Mock()
                result = run_agent('Kiểm tra', FakeProvider([response]), tools)
                self.assertEqual(result['status'], 'error')
                tools.execute.assert_not_called()

    def test_multiple_calls_use_one_model_step_and_preserve_assistant_message(self):
        response = tool_call('github', 'get_status', '{"provider":"github"}')
        other = tool_call('cloudflare', 'get_status', '{"provider":"cloudflare"}')
        response['calls'] += other['calls']
        response['message']['tool_calls'] += other['message']['tool_calls']
        response['message']['content'] = 'Kiểm tra cả hai nhà cung cấp.'
        response['usage'] = {'total_tokens': 17}
        provider = FakeProvider([response, final('Đã nhận hai kết quả.')])
        result = run_agent('Kiểm tra', provider, StatusTools(), max_steps=2)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(provider.histories[1][2], response['message'])
        self.assertEqual([m['tool_call_id'] for m in provider.histories[1][-2:]], ['github', 'cloudflare'])
        tool_events = [event for event in result['trace'] if event['event'] == 'tool']
        self.assertEqual([event['step'] for event in tool_events], [1, 1])
        for event in tool_events:
            self.assertTrue({'event', 'step', 'name', 'arguments', 'result'} <= event.keys())
        self.assertEqual(result['usage'], [{'total_tokens': 17}, {}])

    def test_exhausted_budget_has_terminal_trace_event(self):
        provider = FakeProvider([tool_call('one', 'get_status', '{"provider":"github"}')])
        result = run_agent('Kiểm tra', provider, StatusTools(), max_steps=1)
        self.assertEqual(result['status'], 'max_steps')
        self.assertEqual(len(provider.histories), 1)
        self.assertEqual(result['trace'][-1], {'event': 'max_steps', 'step': 1})

    def test_invalid_budget_does_not_call_model(self):
        for budget in (0, -1, True, 1.5, '6'):
            with self.subTest(budget=budget):
                provider = Mock()
                result = run_agent('Kiểm tra', provider, StatusTools(), max_steps=budget)
                self.assertEqual(result['status'], 'error')
                provider.complete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
