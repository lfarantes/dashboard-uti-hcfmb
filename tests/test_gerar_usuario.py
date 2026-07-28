import tempfile
from pathlib import Path

import yaml

from gerar_usuario import add_user_to_config


def test_add_user_appends_to_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "credentials:\n"
        "  usernames: {}\n"
        "cookie:\n"
        "  expiry_days: 1\n"
        "  key: key\n"
        "  name: dashboard\n",
        encoding="utf-8",
    )

    add_user_to_config(config_path, "maria", "Maria", "maria@teste.com", "Senha123")

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    user = config["credentials"]["usernames"]["maria"]
    assert user["name"] == "Maria"
    assert user["email"] == "maria@teste.com"
    assert user["password"].startswith("$2b$")
