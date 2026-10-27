"""Read the Lab 01 values from .env and print a safe key preview."""

from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    """Load simple KEY=VALUE entries without adding a package dependency."""
    values: dict[str, str] = {}

    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid line {line_number} in {path.name}")

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[name] = value

    return values


def main() -> None:
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        raise SystemExit("Missing .env. Copy .env.example to .env and fill in its values.")

    values = load_env(env_path)
    api_key = values.get("API_KEY", "")
    user_agent = values.get("SEC_USER_AGENT", "")

    if len(api_key) < 4:
        raise SystemExit("API_KEY must contain at least 4 characters.")
    if not user_agent:
        raise SystemExit("SEC_USER_AGENT is missing.")

    print(f"{api_key[:4]}...")
    print(user_agent)


if __name__ == "__main__":
    main()
