import tempfile
import unittest
from pathlib import Path

from tools.filesystem import read_text_file
from tools.safety import is_sensitive_path, redact_text


class SecurityTests(unittest.TestCase):
    def test_env_is_sensitive(self):
        self.assertTrue(is_sensitive_path(Path("/tmp/project/.env")))

    def test_ssh_key_path_is_sensitive(self):
        self.assertTrue(is_sensitive_path(Path.home() / ".ssh" / "id_rsa"))

    def test_secret_text_is_redacted(self):
        text = "GEMINI_API_KEY=super-secret\nAuthorization: Bearer abc123"
        redacted = redact_text(text)
        self.assertNotIn("super-secret", redacted)
        self.assertNotIn("abc123", redacted)

    def test_normal_file_is_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.py"
            path.write_text("VALUE = 1\n", encoding="utf-8")
            result = read_text_file(str(path))
            self.assertTrue(result["success"])
            self.assertIn("VALUE = 1", result["content"])


if __name__ == "__main__":
    unittest.main()
