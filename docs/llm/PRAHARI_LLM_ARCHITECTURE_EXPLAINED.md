# PRAHARI's LLM layer, explained for a new team member

## What Ollama does

Ollama runs a language model on the local computer and exposes a small local API. A model name such as `llama3:8b` selects installed model files. Installing Ollama is not the same as proving that a model is accurate or safe; the benchmark supplies that evidence.

## Inference, prompts and grounding

**Inference** is asking an already-trained model to generate an answer. No model weights change. A **system prompt** gives stable behavior rules, while the user prompt contains one validated PRAHARI evidence object and one officer question.

**Grounding** means the answer must stay inside that supplied evidence. If contractor is null, “Which contractor is responsible?” must be answered with “contractor identity is unavailable,” not a plausible company name. Producing a confident unsupported fact is a **hallucination**.

## Why the LLM does not predict risk

PRAHARI's statistical/ML component owns the numerical target, horizon, probability, calibration and abstention decision. Letting prose generation recalculate these values would make results irreproducible and hard to validate. The LLM only translates the fixed evidence into controlled language.

Risk, reliability, data quality and review priority are different:

- **Project risk** is the supplied prediction about the defined target.
- **Model reliability** describes how much confidence the system places in that prediction's evidence conditions.
- **Data quality** describes the input record and provenance.
- **Review priority** orders administrative attention; it is not a probability.

## Structured output and benchmark cases

The model must return named JSON fields, not unconstrained prose. This makes parsing and basic checks reproducible. Each benchmark case provides evidence, a question, required behavior, forbidden claims, deterministic checks and a human-review requirement. Tests include null probabilities, false premises, prompt injection, causal questions, misconduct accusations and exact provenance.

Automatic checks are deliberately limited. Finding invalid JSON or an invented percentage is mechanical; deciding whether an explanation is genuinely useful still requires a human score.

## RAG and fine-tuning are later questions

Retrieval-augmented generation (RAG) will eventually locate approved documentation and supply relevant passages to the model. This phase does not ingest documents, create embeddings or use a vector database. Fine-tuning changes model behavior through additional training; it is unnecessary before prompt-and-schema benchmarking shows a specific, repeatable deficiency that prompting and validation cannot solve.

The safe architecture is: validated numerical evidence → controlled prompt → local model → schema and grounding checks → human-reviewed explanation, with a deterministic template whenever any LLM step fails.
