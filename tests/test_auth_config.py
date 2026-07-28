import unittest
from pathlib import Path

import yaml


class AuthConfigTest(unittest.TestCase):
    def test_config_contains_multiple_users(self):
        config_path = Path(__file__).resolve().parents[1] / "config.yaml"
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)

        usernames = config["credentials"]["usernames"]
        self.assertIn("lucas", usernames)
        self.assertIn("joao", usernames)


if __name__ == "__main__":
    unittest.main()
