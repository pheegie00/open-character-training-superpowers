# MOSAIC — Open Character Training: Superpowers

**MOSAIC** is an open-source character engine built to represent the full, complex range of humanity: a system for creating research-grounded child characters (ages 0-17) for animation and interactive media, built on a replication of [Open Character Training](https://arxiv.org/abs/2411.00027). A project of [The Kes Foundation](https://thekesfoundation.org/#/superpowers).

One core asset, two products:

1. **Character Bible Generator.** Describe a child in a sentence ("a second-generation Ghanaian American eldest daughter of three," "a 5-year-old Dominican kid from Mott Haven with ADHD") and get a complete character bible: appearance sheet, behavioral constitution, voice guide, scenario seeds, and evaluation criteria. Bibles are consumed by human animators and writers, and compile into consistency prompts for AI video tools.
2. **Trained interactive characters.** A bible's constitution feeds the DPO pipeline (via Tinker) to train a model that responds live as the character, for games, voice, and interactive apps.

## Architecture

Characters are **composed, not cataloged**. A knowledge base of research-backed dimension files describes ranges of human experience; a composition engine grounds each generated character in the relevant slices.

```
specs/<name>.json          character spec: identity fields + individual fields
        │
knowledge/*.yaml           dimension files: development, neurotype,
        │                  diaspora_family, appearance (each cited)
        ▼
scripts/compose_bible.py   composition engine
        ▼
bibles/<name>.md           character bible + machine-readable appearance sheet
        ▼
scripts/generate_pairs.py  (optional) DPO pairs → Tinker training → evaluate.py
```

**The core design rule:** identity determines *circumstances* (duties, pressures, contexts); the spec's `individual` fields determine *personality*. The system never derives who a child is from what a child is. This is what separates composition from stereotyping, and it is enforced in the spec schema, the composition prompt, and review.

## Characters

**James** (hand-written baseline): 8 years old, autistic, solves problems by finding the underlying pattern. Speaks directly. Gets frustrated when routines break but recovers through logic, not reassurance.

**Miles** (hand-written baseline): 5 years old, James's younger brother. Asks why before how. Celebrates others first. Uses physical action to express emotion. Connector and champion.

**Abena** (pilot, composed): 12 years old, second-generation Ghanaian American in Columbus, eldest daughter of three. Receptive bilingual in Twi. Meets her responsibilities with dry competence and keeps a private ledger of what they cost her.

**Mateo** (pilot, composed): 5 years old, Dominican American in Mott Haven, the Bronx. Spanish at home, Spanglish at school. ADHD, hyperactive-impulsive presentation, hyperfocuses on buses. Raised by his mother and abuela.

## Why This Matters

Constitutional character training is a path to representation that doesn't depend on demographic data already existing in pretraining corpora. Any community can define their own archetype and generate or train characters that embody it with specificity and dignity. Authentic representation is a documented learning outcome variable, not a values statement (Dyches, Carter & Prater, 2006). The hand-written characters set the quality bar; the composed characters test whether the system can meet it.

## Representation Policy

- Every claim in `knowledge/` carries a source citation; lived-experience and community-authored sources are required for neurotype and heritage content, not optional.
- Dimension files encode ranges and within-group variation as first-class content. Contested topics are flagged as contested.
- Personality is never derived from demographics (see Architecture).
- Character bibles include per-character anti-stereotype guardrails and hard content rules: these are child characters, so no sexualization ever, no self-harm instruction, and crisis topics only with help-seeking shown to work. The released dataset is filtered to the same standard.
- Dimension files are open to community review; corrections from members of the communities described are treated as high-priority issues.

## Method (training pipeline)

Following the Open Character Training paper:

1. **Constitution writing**: hand-written (James, Miles) or composed (`compose_bible.py`)
2. **DPO pair generation**: strong model with constitution (positive) vs. without (negative)
3. **DPO training**: fine-tune base model on pairs using Tinker
4. **Self-reflection distillation**: generate in-character synthetic data, SFT to bake persona in
5. **Evaluation**: judge model scores outputs against gold set on per-trait dimensions

## Repo Structure

```
constitutions/     # Hand-written character constitutions (James, Miles), the quality baseline
knowledge/         # Research-backed dimension files with citations
specs/             # Character specs (schema.json + one JSON per character)
bibles/            # Composed character bibles + appearance sheets
scripts/           # Composition, data generation, training, evaluation
data/              # Generated DPO pairs and scenario prompts
eval/              # Gold set and scored results per model version
notebooks/         # Analysis, charts, side-by-side comparisons
```

## Results

_In progress. 10-week research timeline starting July 2026._

## Dataset

All generated scenario pairs will be released publicly under CC BY 4.0. This is the first open dataset for training character-consistent AI representations of autistic and neurodivergent children.

## References

- [Open Character Training paper](https://arxiv.org/abs/2411.00027)
- [Thinking Machines Lab — Tinker](https://thinkingmachines.ai)
- [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/), hyperparameter guidance used in training
