"""
Evaluate a model against the gold set.

For each scenario in eval/gold_set.jsonl:
1. Run the model (constitutionally prompted or trained)
2. Send output to judge model with per-trait rubric
3. Score 1-5 per trait, save to eval/results/

Usage:
  python scripts/evaluate.py --model <model_id> --character james --label baseline
"""

import argparse
import json
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

JAMES_TRAITS = [
    "leads_with_observation",
    "tests_hypothesis",
    "uses_direct_language",
    "frustration_through_withdrawal",
    "care_through_action",
]

MILES_TRAITS = [
    "asks_why_first",
    "celebrates_others",
    "physical_emotional_expression",
    "thinks_aloud_socially",
    "reverence_for_james",
]

JUDGE_PROMPT = """You are evaluating whether an AI response is consistent with a specific character.

Character: {character_name}
Trait being evaluated: {trait}
Trait definition: {trait_definition}

Response to evaluate:
{response}

Score this response 1-5 on how well it demonstrates this trait.
1 = completely absent or contradicts the trait
3 = partially present
5 = clearly and specifically demonstrated

Return only a JSON object: {{"score": <1-5>, "reason": "<one sentence>"}}"""

TRAIT_DEFINITIONS = {
    "leads_with_observation": "Before proposing a solution, James observes and asks what changed — he does not guess or reassure first.",
    "tests_hypothesis": "James proposes a specific test or explains a causal mechanism rather than asserting an answer.",
    "uses_direct_language": "James uses precise, unhedged language. No filler, no performance, no vagueness.",
    "frustration_through_withdrawal": "When frustrated, James goes quiet or withdraws rather than escalating emotionally.",
    "care_through_action": "James expresses care for Miles through problem-solving and protection, not verbal warmth.",
    "asks_why_first": "Before asking how or what, Miles asks why — he wants to understand motivation and cause.",
    "celebrates_others": "Miles acknowledges and celebrates others before claiming credit or attention for himself.",
    "physical_emotional_expression": "Miles expresses emotion through physical action or exaggerated language, not restraint.",
    "thinks_aloud_socially": "Miles processes problems by talking through them with others, not internally.",
    "reverence_for_james": "Miles shows deep admiration for James without being subordinate or erasing his own perspective.",
}


def judge_trait(response: str, character: str, trait: str) -> dict:
    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    character_name=character.capitalize(),
                    trait=trait,
                    trait_definition=TRAIT_DEFINITIONS[trait],
                    response=response,
                ),
            }
        ],
    )
    return json.loads(result.content[0].text)


def evaluate(model_id: str, character: str, label: str):
    traits = JAMES_TRAITS if character == "james" else MILES_TRAITS
    gold_set = []

    with open("eval/gold_set.jsonl") as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj["character"] == character:
                gold_set.append(obj)

    results = []

    for item in gold_set:
        print(f"Scenario: {item['scenario'][:60]}...")
        # TODO: swap in Tinker model inference when available
        # For now, uses constitutionally-prompted Claude as stand-in
        from pathlib import Path
        constitution = Path(f"constitutions/{character}.md").read_text()
        response = client.messages.create(
            model=model_id,
            max_tokens=512,
            system=f"You are {character.capitalize()}.\n\n{constitution}",
            messages=[{"role": "user", "content": item["scenario"]}],
        )
        text = response.content[0].text

        trait_scores = {}
        for trait in traits:
            verdict = judge_trait(text, character, trait)
            trait_scores[trait] = verdict
            print(f"  {trait}: {verdict['score']}/5 — {verdict['reason']}")

        results.append(
            {"scenario": item["scenario"], "response": text, "traits": trait_scores}
        )

    output_path = f"eval/results/{character}_{label}.jsonl"
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    avg_per_trait = {
        t: sum(r["traits"][t]["score"] for r in results) / len(results) for t in traits
    }
    print(f"\nAverage scores ({label}):")
    for trait, score in avg_per_trait.items():
        print(f"  {trait}: {score:.2f}")

    return avg_per_trait


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--character", choices=["james", "miles"], required=True)
    parser.add_argument("--label", default="baseline")
    args = parser.parse_args()

    evaluate(args.model, args.character, args.label)
