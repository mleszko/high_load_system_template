from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from high_load_ai.ai.state import AgentGraphState
from high_load_ai.domain.ports import AgentExecutor


def build_graph(executor: AgentExecutor) -> StateGraph[Any, Any, Any, Any]:
    async def run_model(state: AgentGraphState) -> AgentGraphState:
        prompt = state.get("prompt", "")
        run_id = state.get("run_id", "")
        callbacks = state.get("callbacks", [])

        chunks: list[str] = []
        async for event in executor.astream(prompt, run_id, callbacks=callbacks):
            token = event.get("token")
            if token:
                chunks.append(token)

        return {"response": "".join(chunks), "callbacks": callbacks}

    graph = StateGraph(AgentGraphState)
    graph.add_node("run_model", run_model)
    graph.set_entry_point("run_model")
    graph.add_edge("run_model", END)
    return graph
