# Ask PRAHARI Deterministic Demo

Ask PRAHARI currently uses `DemoAssistantService` through the `AssistantService` contract. It makes no network or LLM call, resolves normalized questions against `src/data/mock/askPrahariResponses.js`, waits 600–850 ms, retains conversation history in local storage, and uses a safe fallback for unsupported questions.

## Supported questions

Project: Why is the schedule at risk?; Which milestone is delayed?; What is the latest cost position?; Why does this project need attention?; What are the key execution concerns?; What evidence supports this assessment?; What should the officer review first?; Summarize BHATADI Expansion OC.; Has the completion date changed?; How does physical progress compare with planned progress?; What action should the officer take next?; Give me a brief for senior management.

Portfolio: Which projects need attention?; Show high concern projects.; How many projects need data verification?; What changed this month?

Alert: Why was this alert raised?; What evidence supports this alert?; What should the officer do next?

Review: Summarize this review.; What actions are pending?; What evidence has been checked?

Answers are derived from the canonical BHATADI project object and separate Answer, Key evidence, Recommended attention and Sources. Unknown questions do not invent facts.

UX: premium launcher, minimize/expand, drawer close, Escape close, clear conversation, suggested prompts, free-text submission, persisted history, typing indicator, auto-scroll, context indicator and disabled empty send.

To replace the deterministic provider, instantiate `ApiAssistantService` (or a future `OllamaAssistantService`) in `src/services/assistant/AssistantService.js`. The drawer consumes only `assistantService.ask({ question, context, history })`, so the UI does not need to be rewritten.
