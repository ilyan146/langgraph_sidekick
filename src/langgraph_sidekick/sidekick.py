import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph_sidekick.agent_worker import AgentWorker
from langgraph_sidekick.agent_evaluator import AgentEvaluator

# from langgraph_sidekick.utils import sql_memory
from langgraph_sidekick.utils import setup_async_db
from langgraph_sidekick.schema import State


class SideKick:
    def __init__(self):
        self.agent_worker = None
        self.agent_evaluator = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = None

    async def setup(self):
        self.memory = await setup_async_db()

        # Initialize the agents
        self.agent_worker = await AgentWorker().setup()
        self.agent_evaluator = await AgentEvaluator().setup()

        # Build the graph
        await self.build_graph()

    def agent_worker_router(self, state: State) -> str:
        """Route decision for tool calls or to evaluator"""
        last_message = state.messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "agent_evaluator"

    def agent_evaluator_router(self, state: State) -> str:
        """Route decision for user input needed or success and the response can be provided"""
        if state.success_criteria_met or state.user_input_needed:
            return "END"
        else:
            return "agent_worker"

    async def build_graph(self):
        # Set the graph
        graph_builder = StateGraph(State)

        # Add Nodes
        graph_builder.add_node("agent_worker", self.agent_worker.run)
        graph_builder.add_node("tools", ToolNode(tools=self.agent_worker.tools))
        graph_builder.add_node("agent_evaluator", self.agent_evaluator.run)

        # Add Edges
        graph_builder.add_conditional_edges(
            "agent_worker", self.agent_worker_router, {"tools": "tools", "agent_evaluator": "agent_evaluator"}
        )
        graph_builder.add_edge("tools", "agent_worker")

        graph_builder.add_conditional_edges(
            "agent_evaluator", self.agent_evaluator_router, {"agent_worker": "agent_worker", "END": END}
        )
        graph_builder.add_edge(START, "agent_worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

        # For viewing
        graph_filepath = "sidekick_graph.png"
        with open(graph_filepath, "wb") as f:
            f.write(self.graph.get_graph().draw_mermaid_png())
        print(f"Graph saved to {graph_filepath}")

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = State(
            messages=[{"role": "user", "content": message}],
            success_criteria=success_criteria or "The answer should be clear and accurate.",
            feedback_on_work=None,  # to be set by the evaluator agent
            success_criteria_met=False,  # to start with its false
            user_input_needed=False,  # To start with its false
        )

        result = await self.graph.ainvoke(state, config=config)

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def free_resources(self):
        """Clean up resources"""
        if self.agent_worker:
            self.agent_worker.cleanup()
        # Add any other cleanup here
        print(f"Cleaned up resources for sidekick {self.sidekick_id}")
