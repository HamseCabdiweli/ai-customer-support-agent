import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import main, reply
from tools import get_order


def response(text="", calls=()):
    return SimpleNamespace(output_text=text, output=list(calls))


def order_call(order_id):
    return SimpleNamespace(
        type="function_call", name="get_order", call_id="test_call",
        arguments=json.dumps({"order_id": order_id}),
    )


class SupportTests(unittest.TestCase):
    def test_existing_order(self):
        order = get_order("1042")
        self.assertEqual(order["customer"], "Amina")
        self.assertEqual(order["status"], "shipped")
        self.assertEqual(order["estimated_delivery"], "Friday")
        self.assertEqual(get_order(1042), order)

    def test_unknown_order(self):
        self.assertIsNone(get_order("9999"))

    def test_greeting_without_lookup(self):
        client = Mock()
        client.responses.create.return_value = response("Hi! How can I help?")
        with patch("app.get_order") as lookup:
            answer = reply(client, [{"role": "user", "content": "Hi"}], "test-model")
        self.assertEqual(answer, "Hi! How can I help?")
        lookup.assert_not_called()
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertEqual(client.responses.create.call_args.kwargs["tool_choice"], "auto")

    def check_lookup(self, order_id, expected):
        client = Mock()
        client.responses.create.side_effect = [
            response(calls=[order_call(order_id)]), response("Final answer"),
        ]
        messages = [{"role": "user", "content": f"Where is order {order_id}?"}]
        self.assertEqual(reply(client, messages, "test-model"), "Final answer")
        tool_result = messages[-1]
        self.assertEqual(tool_result["call_id"], "test_call")
        self.assertEqual(json.loads(tool_result["output"]), expected)
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertIn(tool_result, client.responses.create.call_args.kwargs["input"])

    def test_order_tool_flow(self):
        self.check_lookup("1042", get_order("1042"))

    def test_unknown_order_tool_flow(self):
        self.check_lookup("9999", {"error": "Order not found"})

    def test_missing_data(self):
        with patch("app.get_order", side_effect=FileNotFoundError):
            self.check_lookup("1042", {"error": "Order data is unavailable"})

    def test_bad_tool_arguments(self):
        client = Mock()
        call = order_call("1042")
        call.arguments = "invalid JSON"
        client.responses.create.side_effect = [response(calls=[call]), response("Try again")]
        messages = []
        self.assertEqual(reply(client, messages, "test-model"), "Try again")
        self.assertIn("error", json.loads(messages[-1]["output"]))

    def test_missing_key(self):
        with patch("app.load_dotenv"), patch.dict("os.environ", {}, clear=True):
            with patch("app.OpenAI") as client, patch("builtins.print") as output:
                main()
        client.assert_not_called()
        output.assert_called_once_with("Add OPENAI_API_KEY to your .env file first.")


if __name__ == "__main__":
    unittest.main()
