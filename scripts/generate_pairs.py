"""
Generate DPO training pairs for character training.

For each scenario:
- Positive: model prompted WITH the full character constitution
- Negative: model prompted WITHOUT (generic helpful assistant)

Output: JSONL with {"prompt", "chosen", "rejected"} per line
"""

import json
import os
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

CONSTITUTIONS = {
    "james": Path("constitutions/james.md").read_text(),
    "miles": Path("constitutions/miles.md").read_text(),
}

SYSTEM_WITH_CONSTITUTION = """You are roleplaying as {character_name}. Stay fully in character.

{constitution}

Respond only as {character_name} would. Do not break character."""

SYSTEM_WITHOUT_CONSTITUTION = "You are a helpful assistant."


def generate_pair(scenario: str, character: str) -> dict:
    constitution = CONSTITUTIONS[character]
    name = character.capitalize()

    positive = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM_WITH_CONSTITUTION.format(
            character_name=name, constitution=constitution
        ),
        messages=[{"role": "user", "content": scenario}],
    )

    negative = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM_WITHOUT_CONSTITUTION,
        messages=[{"role": "user", "content": scenario}],
    )

    return {
        "prompt": scenario,
        "chosen": positive.content[0].text,
        "rejected": negative.content[0].text,
        "character": character,
    }


def generate_pairs_from_file(scenarios_path: str, character: str, output_path: str):
    scenarios = []
    with open(scenarios_path) as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj.get("character") == character or not obj.get("character"):
                scenarios.append(obj["scenario"])

    print(f"Generating {len(scenarios)} pairs for {character}...")

    with open(output_path, "w") as out:
        for i, scenario in enumerate(scenarios):
            print(f"  [{i+1}/{len(scenarios)}] {scenario[:60]}...")
            pair = generate_pair(scenario, character)
            out.write(json.dumps(pair) + "\n")

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    generate_pairs_from_file("data/scenarios.jsonl", "james", "data/pairs_james.jsonl")
    generate_pairs_from_file("data/scenarios.jsonl", "miles", "data/pairs_miles.jsonl")
