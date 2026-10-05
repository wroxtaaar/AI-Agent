import unittest
from unittest.mock import patch

from tools.docker import find_containers_for_project


class DockerDiscoveryTests(unittest.TestCase):
    @patch("tools.docker._run_docker")
    def test_translates_workspace_path_to_host_mount(self, run_docker):
        run_docker.side_effect = [
            {
                "success": True,
                "stdout": "/home/ubuntu\t/workspace\n",
                "stderr": "",
            },
            {
                "success": True,
                "stdout": "torrentflix\t/home/ubuntu/Torrent-Movie-Search:/app:rw\n",
                "stderr": "",
            },
        ]

        result = find_containers_for_project("/workspace/Torrent-Movie-Search")

        self.assertTrue(result["success"])
        self.assertEqual(result["host_project"], "/home/ubuntu/Torrent-Movie-Search")
        self.assertEqual(result["containers"][0]["name"], "torrentflix")

    @patch("tools.docker._run_docker")
    def test_non_workspace_path_is_matched_directly(self, run_docker):
        run_docker.return_value = {
            "success": True,
            "stdout": "demo\t/tmp/demo:/app:rw\n",
            "stderr": "",
        }

        result = find_containers_for_project("/tmp/demo")

        self.assertTrue(result["success"])
        self.assertIsNone(result["host_project"])
        self.assertEqual(result["containers"][0]["name"], "demo")


if __name__ == "__main__":
    unittest.main()
