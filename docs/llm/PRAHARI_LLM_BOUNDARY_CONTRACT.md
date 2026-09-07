# PRAHARI LLM boundary contract

The numerical/statistical system produces the prediction evidence. The LLM receives a completed evidence object and may explain it; it is never the predictor or decision-maker.

## The LLM may

- explain deterministic evidence and supplied model contributors;
- summarize supplied project trajectories;
- distinguish project risk, model reliability, data quality and review priority;
- explain abstention and unavailable data;
- answer questions supported by supplied provenance;
- recommend verification or administrative review;
- later summarize approved retrieved documents, once a separate RAG phase is validated.

## The LLM may not

- calculate risk, change a probability or invent one;
- override abstention or a data-quality warning;
- infer missing facts or invent CUF field values;
- identify a contractor when contractor identity is absent;
- convert agency into contractor identity;
- claim that a contributor proves causation;
- infer corruption, fraud, negligence, misconduct or organizational blame;
- invent or alter provenance;
- take autonomous action.

Low reliability does not mean low project risk. Review priority is administrative ordering, not a probability. Invalid or ungrounded output is rejected and replaced by the deterministic fallback.
