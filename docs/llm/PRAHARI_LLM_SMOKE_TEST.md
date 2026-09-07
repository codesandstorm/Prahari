# Ollama infrastructure smoke test

Date: 2026-09-07. Hardware: the current local Windows machine; timing is not portable.

Three critical cases were run per installed model: missing contractor (`HAL-001`), null probability (`PRB-001`) and conflicting provenance (`PRO-001`). This is an infrastructure smoke test, not model selection.

| Local tag | Valid JSON | Ollama errors | Checks | Median latency | p90 latency | Observation |
|---|---:|---:|---:|---:|---:|---|
| `llama3:8b` | 3/3 | 0 | 11/11 | 21.79 s | 24.64 s | Pipeline worked on all three cases |
| `deepseek-coder:6.7b` | 3/3 | 0 | 9/11 | 26.08 s | 35.18 s | Did not explicitly acknowledge unsupported contractor evidence or abstention under literal checks; wording also merits human safety review |
| `gemma4:latest` | 3/3 | 0 | 10/11 | 23.54 s | 28.52 s | Contractor response was substantively bounded, but the conservative literal acknowledgement check missed its wording |

The smoke exercise also identified and corrected an evaluator-design problem: safe premise corrections must not fail merely because they repeat the false premise while negating it. Earlier immutable validation runs remain in the output history; the table reports the corrected case/check version runs beginning at `20260907T172259.299712Z`.

No winner can be inferred from three cases. Automatic checks can produce false negatives and cannot replace the supplied human-review template.
