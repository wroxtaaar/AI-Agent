import os
import unittest


class ServerImportTests(unittest.TestCase):
    def test_server_imports_without_ai_key(self):
        os.environ.pop("OPENROUTER_API_KEY", None)
        import server
        self.assertEqual(server.app.title, "Oracle VPS AI Agent")


if __name__ == "__main__":
    unittest.main()
