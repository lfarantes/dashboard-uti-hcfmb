from pathlib import Path

import yaml
from streamlit_authenticator.utilities import Hasher


def add_user_to_config(config_path, username, name, email, password):
    config_path = Path(config_path)
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    else:
        config = {}

    credentials = config.setdefault("credentials", {})
    usernames = credentials.setdefault("usernames", {})
    usernames[username] = {
        "email": email,
        "name": name,
        "password": Hasher.hash(password),
    }

    if "cookie" not in config:
        config["cookie"] = {
            "expiry_days": 1,
            "key": "random_signature_key",
            "name": "dashboard_uti_key",
        }

    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)

    return usernames[username]["password"]


if __name__ == "__main__":
    username = input("Nome de usuário: ").strip()
    name = input("Nome completo: ").strip()
    email = input("E-mail: ").strip()
    password = input("Senha: ").strip()

    config_file = Path(__file__).with_name("config.yaml")
    hashed_password = add_user_to_config(config_file, username, name, email, password)
    print(f"Usuário '{username}' criado com sucesso.")
    print(f"Hash da senha: {hashed_password}")