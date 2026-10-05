import unittest

from tools.shell import run_command


class ShellSafetyTests(unittest.TestCase):
    def test_read_only_command_is_allowed(self):
        result = run_command("pwd")
        self.assertTrue(result["success"])

    def test_git_is_not_available_through_generic_shell(self):
        result = run_command("git status")
        self.assertFalse(result["success"])

    def test_redirection_is_blocked(self):
        result = run_command("echo hello > bad.txt")
        self.assertFalse(result["success"])

    def test_python_execution_is_blocked(self):
        result = run_command("python -c 'print(1)'")
        self.assertFalse(result["success"])

    def test_find_exec_is_blocked(self):
        result = run_command("find . -exec touch bad.txt {} \\;")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
