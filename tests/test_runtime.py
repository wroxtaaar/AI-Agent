import json
import unittest

from agent_runtime import AgentRuntime, ToolSpec


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "echo",
                                "arguments": json.dumps({"value": "hello"})
                            }
                        }]
                    }
                }]
            }
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Tool completed."
                }
            }]
        }


class RuntimeTests(unittest.TestCase):
    def test_tool_loop_executes_function_and_returns_answer(self):
        called = []

        def echo(value):
            called.append(value)
            return {"success": True, "value": value}

        runtime = AgentRuntime([
            ToolSpec(
                name="echo",
                description="Echo a value.",
                function=echo,
                parameters={
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                    "required": ["value"],
                },
            )
        ], provider=FakeProvider())

        result = runtime.run("say hello")
        self.assertTrue(result["success"])
        self.assertEqual(result["answer"], "Tool completed.")
        self.assertEqual(called, ["hello"])
        self.assertEqual(result["tool_trace"][0]["tool"], "echo")


if __name__ == "__main__":
    unittest.main()
