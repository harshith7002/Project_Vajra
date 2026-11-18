"""Wire the nodes into a LangGraph StateGraph and compile it with a checkpointer."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph

from backend.config import settings
from backend.graph.agents import (Deps, make_analyst, make_approval, make_critic, make_retriever, make_supervisor,
                                  make_writer)
from backend.graph.state import VajraState


def sqlite_checkpointer(path: Path | None = None) -> SqliteSaver:
    path = path or (settings.index_dir / "checkpoints.sqlite")
    path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(path), check_same_thread=False))


def build_graph(deps: Deps, checkpointer: BaseCheckpointSaver | None = None):
    g = StateGraph(VajraState)
    g.add_node("supervisor", make_supervisor(deps),
               destinations=("retriever", "analyst", "writer", "critic", "approval", "__end__"))
    g.add_node("retriever", make_retriever(deps))
    g.add_node("analyst", make_analyst(deps))
    g.add_node("writer", make_writer(deps))
    g.add_node("critic", make_critic(deps))
    g.add_node("approval", make_approval(deps))

    g.add_edge(START, "supervisor")
    for worker in ("retriever", "analyst", "writer", "critic"):
        g.add_edge(worker, "supervisor")  # hierarchy: every worker reports back to the supervisor
    g.add_edge("approval", "__end__")
    return g.compile(checkpointer=checkpointer or sqlite_checkpointer())
