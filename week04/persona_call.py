#!/usr/bin/env python3
"""Make the worksheet's one permitted model call with a student persona."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openai import OpenAI

from worksheet import ROOT, load_simple_config


def env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
                key, value = raw.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persona", required=True, type=Path)
    parser.add_argument("--payload", required=True, type=Path)
    args = parser.parse_args()
    env = env_values(ROOT / ".env")
    client = OpenAI(api_key=env["API_KEY"], base_url=env.get("BASE_URL"), timeout=120)
    response = client.chat.completions.create(
        model=env.get("MODEL", "llama3.1:latest"),
        temperature=0,
        max_tokens=350,
        messages=[
            {"role": "system", "content": args.persona.read_text(encoding="utf-8") + "\nUse no number outside the JSON. Do not calculate. Write why it may be cheap or why it is not that story. End with what in the next filing would change the view."},
            {"role": "user", "content": args.payload.read_text(encoding="utf-8")},
        ],
    )
    print(response.choices[0].message.content or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
