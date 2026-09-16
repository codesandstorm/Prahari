# Ask PRAHARI Deterministic Demo

Ask PRAHARI makes no network or LLM call in Frontend V2. It resolves normalized questions against `src/data/mock/askPrahariResponses.js`, waits briefly, retains session conversation history, and uses a safe fallback for unsupported questions.

## Supported questions

Project: Why is the schedule at risk?; Which milestone is delayed?; What is the latest cost status?; What are the key risks for this project?; Summarize this project.; What action should I review first?

Portfolio: Which projects need attention?; Show high concern projects.; How many projects need data verification?; What changed this month?

Alert: Why was this alert raised?; What evidence supports this alert?; What should the officer do next?

Review: Summarize this review.; What actions are pending?; What evidence has been checked?

Answers explicitly separate a short conclusion from evidence and remind the officer to verify material decisions. Unknown questions do not invent facts; they direct the user back to supported project, schedule, cost, alert, review, and evidence topics.

UX: launcher, minimize/expand, drawer close, Escape close, suggested prompts, free-text submission, history, typing indicator, auto-scroll where supported, context-aware prompt groups, and disabled empty send.
