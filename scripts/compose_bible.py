"""
Compose a character bible from a character spec.

Pipeline: spec (specs/*.json) + grounding knowledge (knowledge/*.yaml)
-> LLM draft -> bibles/<name>.md + bibles/<name>_appearance.json

The spec's identity fields select which knowledge entries get loaded as
grounding. The spec's individual fields are passed through untouched —
personality is never derived from demographics.

Usage: python scripts/compose_bible.py specs/abena.json
"""

import json
import re
import sys
from pathlib import Path

import yaml
from anthropic import Anthropic

client = Anthropic()

MODEL = "claude-sonnet-5"


def load_knowledge():
    knowledge = {}
    for path in Path("knowledge").glob("*.yaml"):
        knowledge[path.stem] = yaml.safe_load(path.read_text())
    return knowledge


def select_development(knowledge, age):
    """The character's band plus adjacent bands (kids straddle bands)."""
    bands = knowledge["development"]["bands"]
    keep = []
    for i, band in enumerate(bands):
        lo, hi = parse_age_range(band.get("age_range", ""))
        if lo is not None and lo - 2 <= age <= hi + 2:
            keep.append(band)
    out = dict(knowledge["development"])
    out["bands"] = keep or bands
    return out


def parse_age_range(text):
    nums = re.findall(r"\d+", str(text))
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return None, None


def select_neurotype(knowledge, spec):
    wanted = {n["condition"] for n in spec["identity"].get("neurotype", [])}
    if not wanted:
        return None
    out = dict(knowledge["neurotype"])
    out["conditions"] = [
        c for c in knowledge["neurotype"]["conditions"] if c.get("id") in wanted
    ]
    return out


def select_diaspora(knowledge, spec):
    src = knowledge["diaspora_family"]
    identity = spec["identity"]
    out = {k: src[k] for k in ("dimension", "scope", "design_rule") if k in src}

    gen = identity.get("generation_status")
    out["generation_status"] = [
        g for g in src.get("generation_status", []) if g.get("id") == gen
    ] or src.get("generation_status", [])

    role = identity.get("family", {}).get("role")
    out["family_roles"] = [
        r for r in src.get("family_roles", []) if r.get("id") == role
    ] or src.get("family_roles", [])

    practice_ids = {
        l.get("practice_id") for l in identity.get("languages", []) if l.get("practice_id")
    }
    out["language_practice"] = [
        p for p in src.get("language_practice", []) if p.get("id") in practice_ids
    ] or src.get("language_practice", [])

    profile_ids = {
        h.get("profile_id") for h in identity.get("heritage", []) if h.get("profile_id")
    }
    out["heritage_profiles"] = [
        p for p in src.get("heritage_profiles", []) if p.get("id") in profile_ids
    ]
    return out


def select_appearance(knowledge, spec):
    src = knowledge["appearance"]
    out = {k: v for k, v in src.items() if k != "ancestry_distributions"}
    cultures = " ".join(
        h.get("culture", "") + " " + h.get("profile_id", "")
        for h in spec["identity"].get("heritage", [])
    ).lower()
    out["ancestry_distributions"] = [
        d
        for d in src.get("ancestry_distributions", [])
        if any(word in cultures for word in str(d.get("id", "")).lower().split("_"))
    ] or src.get("ancestry_distributions", [])
    return out


SYSTEM = """You are a character writer producing a character bible for an animated series about children. You write with the specificity of good fiction and the accuracy of good research.

Hard rules:
1. Identity determines CIRCUMSTANCES (duties, pressures, contexts, textures). The spec's `individual` fields determine PERSONALITY. Never infer personality from demographics — the grounding notes tell you what this child's world is like, the individual fields tell you who they are inside it.
2. Ground every developmental detail (speech, cognition, motor, emotion) in the development notes for the character's age. A 5-year-old must sound 5, not 8.
3. If the character has a neurotype, express the SPECIFIC presentation named in the spec — a small, consistent subset of the trait repertoire, never the whole checklist. Follow the portrayal do/avoid guidance.
4. Language practice must be concrete: show actual example lines of how this child talks in each context, using the language-practice grounding.
5. Within-group variation is real. Where you use a heritage detail, use it as THIS family's specific texture, not as "what those families are like."
6. No more than 2 em-dashes in the entire document.
7. Dignity floor: the character is never a lesson, a burden, or a mascot. Write them as the protagonist of their own life."""

BIBLE_TEMPLATE = """# {name} — Character Bible

## Identity Snapshot
(one tight paragraph: who this kid is, in the voice of a showrunner pitching them)

## Appearance
(prose description for humans, then a fenced ```json block: a flat appearance sheet with keys like age, height_range, skin_tone_mst, hair_texture, hair_style, hair_color, eye_color, face_notes, build, distinguishing, wardrobe. Values must be specific and stable enough to keep the character visually consistent across AI-generated shots.)

## Core Identity
## Daily World
(their actual routine, household, neighborhood, school — the circumstances)

## Behavior & Problem-Solving
## Voice & Communication
(with 4-6 example lines of dialogue per context — e.g. at home vs at school — that sound like a real child of this age)

## Emotional Life
## Family & Relationships
## What {first} Is Not
(anti-stereotype guardrails specific to this character)

## Scenario Seeds
(8 numbered, specific scene premises drawn from their real circumstances, in the style of: "You've been doing your Lego set for an hour and you're on step 47...")

## Evaluation Criteria
(numbered list: what makes a response/portrayal in-character; then what makes it out-of-character — same format as constitutions/james.md)

## Portrayal Guardrails
(hard content rules: this is a child character — no sexualization ever, no self-harm content, crisis topics handled with help-seeking shown to work; plus this character's specific representation do/avoid list)"""


def compose(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    knowledge = load_knowledge()

    grounding = {
        "development": select_development(knowledge, spec["age"]),
        "neurotype": select_neurotype(knowledge, spec),
        "diaspora_family": select_diaspora(knowledge, spec),
        "appearance": select_appearance(knowledge, spec),
    }
    grounding = {k: v for k, v in grounding.items() if v}

    first = spec["name"]["goes_by"]
    prompt = (
        "CHARACTER SPEC:\n```json\n"
        + json.dumps(spec, indent=2)
        + "\n```\n\nGROUNDING KNOWLEDGE (research-backed; use it, don't recite it):\n```yaml\n"
        + yaml.safe_dump(grounding, sort_keys=False, allow_unicode=True)
        + "\n```\n\nWrite the complete character bible using exactly this structure:\n\n"
        + BIBLE_TEMPLATE.format(name=spec["name"]["full"], first=first)
    )

    print(f"Composing bible for {spec['name']['full']}...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    bible = response.content[0].text

    out_md = Path("bibles") / f"{first.lower()}.md"
    out_md.parent.mkdir(exist_ok=True)
    out_md.write_text(bible)
    print(f"Saved {out_md}")

    match = re.search(r"```json\n(.*?)```", bible, re.DOTALL)
    if match:
        sheet = json.loads(match.group(1))
        out_json = Path("bibles") / f"{first.lower()}_appearance.json"
        out_json.write_text(json.dumps(sheet, indent=2) + "\n")
        print(f"Saved {out_json}")


if __name__ == "__main__":
    for spec_path in sys.argv[1:] or ["specs/abena.json", "specs/mateo.json"]:
        compose(spec_path)
