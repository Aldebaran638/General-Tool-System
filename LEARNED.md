# What We Learned Today

1. **Custom LangChain chat model** — `MyVLLMChatModel` is a project-defined class in `backend/app/modules/ai_assistant/llm.py`. It directly calls the vLLM `/chat/completions` HTTP API and parses the JSON response, including the non-standard `reasoning` field.

2. **Runnable abstraction** — LangChain's `Runnable` is an interface for callable components. `RunnableLambda` wraps plain functions so they can join the chain.

3. **Operator chaining** — The `|` operator is overloaded via `Runnable.__or__()` to build a `RunnableSequence`, which runs each step in order.

4. **Agent chain** — `_AGENT_RUNNABLE` is a simple three-step pipeline: extract messages → call the bound model → wrap the output back into state.
