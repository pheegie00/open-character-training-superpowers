# Open Character Training: Superpowers

A replication and extension of [Open Character Training](https://arxiv.org/abs/2411.00027) applied to two original characters representing underrepresented kids in AI-generated media.

## Characters

**James** — 8 years old, autistic, solves problems by finding the underlying pattern. Speaks directly. Gets frustrated when routines break but recovers through logic, not reassurance.

**Miles** — 5 years old, James's younger brother. Asks why before how. Celebrates others first. Uses physical action to express emotion. Connector and champion.

## Why This Matters

Constitutional character training is a path to representation that doesn't depend on demographic data already existing in pretraining corpora. Any community can define their own archetype and train a model to embody it. This project demonstrates that method for two characters whose behavioral specificity — particularly James's autistic cognition — is underrepresented in existing AI training data.

## Method

Following the Open Character Training paper:

1. **Constitution writing** — define character traits as behavioral rules
2. **DPO pair generation** — strong model with constitution (positive) vs. without (negative)
3. **DPO training** — fine-tune base model on pairs using Tinker
4. **Self-reflection distillation** — generate in-character synthetic data, SFT to bake persona in
5. **Evaluation** — judge model scores outputs against gold set on per-trait dimensions

## Repo Structure

```
constitutions/     # Character constitutions (James, Miles)
data/              # Generated DPO pairs and scenario prompts
scripts/           # Data generation, training, evaluation scripts
eval/              # Gold set and scored results per model version
notebooks/         # Analysis, charts, side-by-side comparisons
```

## Results

_In progress — 10-week research timeline starting July 2026._

## Dataset

All generated scenario pairs will be released publicly under CC BY 4.0. This is the first open dataset for training character-consistent AI representations of autistic and neurodivergent children.

## References

- [Open Character Training paper](https://arxiv.org/abs/2411.00027)
- [Thinking Machines Lab — Tinker](https://thinkingmachines.ai)
- [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/) — hyperparameter guidance used in training
