# PRAHARI LLM Benchmark Foundation V1

This package evaluates whether a local Ollama model can explain an already-produced PRAHARI evidence object safely. It does **not** predict risk and is not a chatbot, RAG system or dashboard service.

## Commands

Inventory installed models without downloading anything:

```powershell
python -m llm.benchmark.inventory --output outputs/llm/model_inventory.json
```

Run the full case set against any installed model:

```powershell
python -m llm.benchmark.runner --model llama3:8b
```

Run selected smoke cases:

```powershell
python -m llm.benchmark.runner --model llama3:8b --case-id HAL-001 --case-id PRB-001
```

Every invocation creates a new timestamped directory under `outputs/llm/benchmark/`; it never overwrites an earlier run. Settings are temperature 0, seed 42, top-p 0.9 and at most 500 output tokens. Support for settings can vary by model/Ollama version and is therefore recorded with every run.

Automatic checks catch structural and literal safety failures. They do not prove semantic correctness. A human must score groundedness, clarity, officer usefulness and uncertainty handling from 0 (fail) to 3 (strong), separately flagging hallucinations.

Future model names live in `llm/models.json`; no winner is embedded in application logic.
