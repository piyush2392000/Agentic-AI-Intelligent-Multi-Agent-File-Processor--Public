
# # graph/research_graph.py

# from typing import Dict, Any
# from langgraph.graph import StateGraph, START, END
# from langchain_core.messages import HumanMessage
# from tools.memory_tools import save_memories, load_memories
# import json
# import traceback
# from graph.research_state import ResearchState
# import logging
# from tools.memory_tools import AGENT_DB_MAP
# import os
# from agents.a2a_factory import A2AAgentFactory

# logger = logging.getLogger(__name__)

# class ResearchGraph:
#     def __init__(self, prompts: Dict[str, Dict[str, str]], supervisor_agent, agent_factory: A2AAgentFactory):
#         self.prompts = prompts
#         self.supervisor = supervisor_agent
#         self.agent_factory = agent_factory
#         self.graph = self._build_graph()

#     def _create_agent_node(self, agent_id: str):
#         def agent_node(state: ResearchState) -> ResearchState:
#             try:
#                 agent_prompts = self.prompts.get(agent_id, {}).copy()
#                 selection_info = (state.get("selected_prompts") or {}).get(agent_id)
#                 if selection_info:
#                     prompt_text = selection_info.get("prompt_text")
#                     agent_prompts["system_prompt"] = prompt_text
#                     agent_prompts["custom_prompt"] = prompt_text

#                 state_with_context = { **state, "prompts": agent_prompts }

#                 logger.info(f"🤖 Starting agent: {agent_id}")
#                 agent = self.agent_factory.create_agent(agent_id, agent_prompts)
#                 findings = agent.run(state=state_with_context)
#                 logger.info(f"✅ Agent {agent_id} completed.")

#                 updated_context = self._update_accumulated_context(state.get("accumulated_context", ""), agent_id, findings)

#                 return {
#                     "completed_agents": state["completed_agents"] + [agent_id],
#                     "agent_findings": {**state["agent_findings"], agent_id: findings},
#                     "accumulated_context": updated_context,
#                     "last_completed_agent": agent_id,
#                 }
#             except Exception as e:
#                 logger.error(f"❌ Agent {agent_id} failed: {e}")
#                 traceback.print_exc()
#                 return { "completed_agents": state["completed_agents"] + [agent_id], "agent_findings": {**state["agent_findings"], agent_id: f"Error: {e}"} }
#         return agent_node

#     def _update_accumulated_context(self, current_context: str, source: str, findings) -> str:
#         summary = str(findings)[:400]
#         new_entry = f"\n\n--- Findings from {source.upper()} ---\n{summary}"
#         return (current_context + new_entry).strip()

#     def _build_graph(self) -> StateGraph:
#         graph = StateGraph(ResearchState)

#         graph.add_node("planner", self._planner_node)
#         graph.add_node("memory_loader", self._memory_loader_node)
#         graph.add_node("agent_router", lambda state: state)
#         graph.add_node("supervisor_review", self._supervisor_review_node)
#         graph.add_node("ask_to_save_memory", self._ask_to_save_memory_node)
#         graph.add_node("memory_saver", self._memory_saver_node)
#         graph.add_node("synthesizer", self._synthesizer_node)

#         available_agents = [a for a in self.agent_factory.get_all_agent_ids() if a not in ["research_supervisor", "memory_agent"]]
#         for agent_id in available_agents:
#             graph.add_node(f"agent_{agent_id}", self._create_agent_node(agent_id))
#             graph.add_edge(f"agent_{agent_id}", "supervisor_review")

#         graph.add_edge(START, "planner")
#         graph.add_edge("planner", "memory_loader")
#         graph.add_edge("memory_loader", "agent_router")
#         graph.add_edge("memory_saver", "synthesizer")
#         graph.add_edge("synthesizer", END)

#         graph.add_conditional_edges("supervisor_review", self._route_after_agent_run, {"pause_for_input": "pause_for_input", "continue": "agent_router"})
#         graph.add_node("pause_for_input", lambda state: state)
#         graph.add_edge("pause_for_input", END)

#         graph.add_conditional_edges("agent_router", self._route_to_next_agent, {f"agent_{a}": f"agent_{a}" for a in available_agents} |
#                                         {"ask_to_save": "ask_to_save_memory"})
#         graph.add_conditional_edges("ask_to_save_memory", self._route_after_save_prompt,
#                                     {"save_memory": "memory_saver", "synthesize": "synthesizer"})

#         return graph.compile()

#     def _planner_node(self, state: ResearchState) -> ResearchState:
#         logger.info("📋 Supervisor is creating the execution plan...")
#         analysis_result = self.supervisor.run(state)
#         parsed = json.loads(analysis_result) if isinstance(analysis_result, str) else analysis_result
#         agent_queue = parsed.get("required_agents", [])
#         logger.info(f"Plan created. Agent queue: {agent_queue}")
#         return {"analysis_result": parsed, "agent_queue": agent_queue.copy()}

#     def _memory_loader_node(self, state: ResearchState) -> ResearchState:
#         agent_queue = state.get("agent_queue", [])
#         brief = state.get("brief", "")
#         file_path = state.get("file_path", "unknown_file")
#         if not agent_queue: return {}

#         logger.info(f"🧠 Loading memories for agents: {agent_queue} related to file: {file_path}")

#         all_memory_findings = {}
#         for agent_id in agent_queue:
#             try:
#                 result = load_memories.invoke({
#                     "agent_id": agent_id,
#                     "query": brief,
#                     "file_path": file_path
#                 })
#                 all_memory_findings[agent_id] = result
#             except Exception as e:
#                 logger.error(f"❌ Failed to load memory directly for {agent_id}: {e}")
#                 all_memory_findings[agent_id] = {"success": False, "error": str(e), "memories": []}

#         return {"retrieved_memories": all_memory_findings}

#     def _supervisor_review_node(self, state: ResearchState) -> ResearchState:
#         last_agent = state.get("last_completed_agent")
#         if last_agent == 'test_case_agent' and 'test_script_agent' in state.get("agent_queue", []):
#             logger.info("⏸️ PAUSING workflow for user to select a test case.")
#             return {"is_paused_for_input": True}
#         return {}

#     def _route_after_agent_run(self, state: ResearchState) -> str:
#         return "pause_for_input" if state.get("is_paused_for_input") else "continue"

#     def _route_to_next_agent(self, state: ResearchState) -> str:
#         agent_queue = state.get("agent_queue", [])
#         if not agent_queue: return "ask_to_save"
#         return f"agent_{agent_queue.pop(0)}"

#     def _ask_to_save_memory_node(self, state: ResearchState) -> ResearchState:
#         logger.info("⏸️ PAUSING workflow to ask user about saving memories.")
#         return {"is_paused_for_memory_save": True, "findings_to_save": state.get("agent_findings")}

#     def _route_after_save_prompt(self, state: ResearchState) -> str:
#         return "save_memory" if state.get("user_memory_save_decision") else "synthesize"

#     def _memory_saver_node(self, state: ResearchState) -> ResearchState:
#         findings_to_save = state.get("findings_to_save", {})
#         file_path = state.get("file_path", "unknown_file")
#         query = state.get("brief", "No query provided")

#         if not findings_to_save: return {}

#         logger.info(f"💾 Saving findings to memory for file: {file_path}...")
#         for agent_id, findings in findings_to_save.items():
#             if not findings or agent_id not in AGENT_DB_MAP: continue

#             # UPDATED: Extract only the most relevant text to save as the memory.
#             content_to_save = None
#             if isinstance(findings, dict):
#                 # Prioritize the final 'response' from the RAG tool
#                 rag_response = findings.get('tool_results', {}).get('query_rag_store', {}).get('response')
#                 # Fall back to the agent's overall 'summary' if the RAG response isn't available
#                 summary = findings.get('summary')
#                 content_to_save = rag_response or summary

#             # Ensure we have something to save before calling the tool
#             if content_to_save:
#                 try:
#                     save_memories.invoke({
#                         "agent_id": agent_id,
#                         "file_path": file_path,
#                         "content": content_to_save,  # Pass the extracted string
#                         "query": query
#                     })
#                 except Exception as e:
#                     logger.error(f"❌ Failed to save memory directly for {agent_id}: {e}")
#         logger.info("✅ Memories saved.")
#         return {}

#     def _synthesizer_node(self, state: ResearchState) -> ResearchState:
#         logger.info("✍️ Synthesizing final report...")
#         final_report = self.supervisor.synthesize_findings(state.get("agent_findings", {}))
#         return {"final_report": final_report}

#     def run_research(self, brief: str, file_path: str, selected_prompts: Dict, analysis_result: Dict) -> Dict:
#         initial_state = ResearchState(
#             messages=[HumanMessage(content=brief)], brief=brief, file_path=file_path or "",
#             selected_prompts=selected_prompts or {}, analysis_result=analysis_result,
#             agent_queue=[], completed_agents=[], agent_findings={},
#             accumulated_context=f"Initial Brief: {brief}"
#         )
#         final_state = self.graph.invoke(initial_state)
#         return {"success": True, "final_state": final_state}

#     def resume_research(self, paused_state: Dict) -> Dict:
#         logger.info("🚀 Resuming research workflow...")
#         paused_state["is_paused_for_input"] = False
#         paused_state["is_paused_for_memory_save"] = False
#         final_state = self.graph.invoke(paused_state)
#         return {"success": True, "final_state": final_state}




# graph/research_graph.py

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from tools.memory_tools import save_memories, load_memories
import json
import traceback
from graph.research_state import ResearchState
import logging
from tools.memory_tools import AGENT_DB_MAP
import os
from agents.a2a_factory import A2AAgentFactory

logger = logging.getLogger(__name__)

class ResearchGraph:
    def __init__(self, prompts: Dict[str, Dict[str, str]], supervisor_agent, agent_factory: A2AAgentFactory):
        self.prompts = prompts
        self.supervisor = supervisor_agent
        self.agent_factory = agent_factory
        self.graph = self._build_graph()

    def _create_agent_node(self, agent_id: str):
        def agent_node(state: ResearchState) -> ResearchState:
            try:
                agent_prompts = self.prompts.get(agent_id, {}).copy()
                selection_info = (state.get("selected_prompts") or {}).get(agent_id)
                if selection_info:
                    prompt_text = selection_info.get("prompt_text")
                    agent_prompts["system_prompt"] = prompt_text
                    agent_prompts["custom_prompt"] = prompt_text

                state_with_context = { **state, "prompts": agent_prompts }

                logger.info(f"🤖 Starting agent: {agent_id}")
                agent = self.agent_factory.create_agent(agent_id, agent_prompts)
                findings = agent.run(state=state_with_context)
                logger.info(f"✅ Agent {agent_id} completed.")

                updated_context = self._update_accumulated_context(state.get("accumulated_context", ""), agent_id, findings)

                return {
                    "completed_agents": state["completed_agents"] + [agent_id],
                    "agent_findings": {**state["agent_findings"], agent_id: findings},
                    "accumulated_context": updated_context,
                    "last_completed_agent": agent_id,
                }
            except Exception as e:
                logger.error(f"❌ Agent {agent_id} failed: {e}")
                traceback.print_exc()
                return { "completed_agents": state["completed_agents"] + [agent_id], "agent_findings": {**state["agent_findings"], agent_id: f"Error: {e}"} }
        return agent_node
    

    def _update_accumulated_context(self, current_context: str, source: str, findings) -> str:
        summary = str(findings)[:400]
        new_entry = f"\n\n--- Findings from {source.upper()} ---\n{summary}"
        return (current_context + new_entry).strip()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(ResearchState)

        graph.add_node("planner", self._planner_node)
        graph.add_node("memory_loader", self._memory_loader_node)
        graph.add_node("agent_router", lambda state: state)
        graph.add_node("supervisor_review", self._supervisor_review_node)
        graph.add_node("ask_to_save_memory", self._ask_to_save_memory_node)
        graph.add_node("memory_saver", self._memory_saver_node)
        graph.add_node("synthesizer", self._synthesizer_node)

        available_agents = [a for a in self.agent_factory.get_all_agent_ids() if a not in ["research_supervisor", "memory_agent"]]
        for agent_id in available_agents:
            graph.add_node(f"agent_{agent_id}", self._create_agent_node(agent_id))
            graph.add_edge(f"agent_{agent_id}", "supervisor_review")

        graph.add_edge(START, "planner")
        graph.add_edge("planner", "memory_loader")
        graph.add_edge("memory_loader", "agent_router")
        graph.add_edge("memory_saver", "synthesizer")
        graph.add_edge("synthesizer", END)

        graph.add_conditional_edges("supervisor_review", self._route_after_agent_run, {"pause_for_input": "pause_for_input", "continue": "agent_router"})
        graph.add_node("pause_for_input", lambda state: state)
        graph.add_edge("pause_for_input", END)

        graph.add_conditional_edges("agent_router", self._route_to_next_agent, {f"agent_{a}": f"agent_{a}" for a in available_agents} |
                                        {"ask_to_save": "ask_to_save_memory"})
        graph.add_conditional_edges("ask_to_save_memory", self._route_after_save_prompt,
                                    {"save_memory": "memory_saver", "synthesize": "synthesizer"})

        return graph.compile()

    # def _planner_node(self, state: ResearchState) -> ResearchState:
    #     logger.info("📋 Supervisor is creating the execution plan...")
    #     analysis_result = self.supervisor.run(state)
    #     parsed = json.loads(analysis_result) if isinstance(analysis_result, str) else analysis_result
    #     agent_queue = parsed.get("required_agents", [])
    #     logger.info(f"Plan created. Agent queue: {agent_queue}")
    #     return {"analysis_result": parsed, "agent_queue": agent_queue.copy()}
    def _planner_node(self, state: ResearchState) -> ResearchState:
        # If a plan and agent queue already exist in the state, we are resuming.
        # This check prevents the supervisor from creating a new plan.
        if state.get("analysis_result") and state.get("agent_queue"):
            logger.info("✅ Execution plan already exists. Resuming workflow by skipping planner.")
            return {}

        # Otherwise, it's a new run, so we create a plan.
        logger.info("📋 Supervisor is creating the execution plan for a new workflow...")
        analysis_result = self.supervisor.run(state)
        parsed = json.loads(analysis_result) if isinstance(analysis_result, str) else analysis_result
        agent_queue = parsed.get("required_agents", [])
        logger.info(f"Plan created. Agent queue: {agent_queue}")
        return {"analysis_result": parsed, "agent_queue": agent_queue.copy()}
    
    
    

    def _memory_loader_node(self, state: ResearchState) -> ResearchState:
        agent_queue = state.get("agent_queue", [])
        brief = state.get("brief", "")
        file_path = state.get("file_path", "unknown_file")
        if not agent_queue: return {}

        logger.info(f"🧠 Loading memories for agents: {agent_queue} related to file: {file_path}")

        all_memory_findings = {}
        for agent_id in agent_queue:
            try:
                result = load_memories.invoke({
                    "agent_id": agent_id,
                    "query": brief,
                    "file_path": file_path
                })
                all_memory_findings[agent_id] = result
            except Exception as e:
                logger.error(f"❌ Failed to load memory directly for {agent_id}: {e}")
                all_memory_findings[agent_id] = {"success": False, "error": str(e), "memories": []}

        return {"retrieved_memories": all_memory_findings}

    def _supervisor_review_node(self, state: ResearchState) -> ResearchState:
        last_agent = state.get("last_completed_agent")
        if last_agent == 'test_case_agent' and 'test_script_agent' in state.get("agent_queue", []):
            logger.info("⏸️ PAUSING workflow for user to select a test case.")
            return {"is_paused_for_input": True}
        return {}

    def _route_after_agent_run(self, state: ResearchState) -> str:
        return "pause_for_input" if state.get("is_paused_for_input") else "continue"

    def _route_to_next_agent(self, state: ResearchState) -> str:
        agent_queue = state.get("agent_queue", [])
        if not agent_queue: return "ask_to_save"
        return f"agent_{agent_queue.pop(0)}"

    def _ask_to_save_memory_node(self, state: ResearchState) -> ResearchState:
        logger.info("⏸️ PAUSING workflow to ask user about saving memories.")
        return {"is_paused_for_memory_save": True, "findings_to_save": state.get("agent_findings")}

    def _route_after_save_prompt(self, state: ResearchState) -> str:
        return "save_memory" if state.get("user_memory_save_decision") else "synthesize"

    def _memory_saver_node(self, state: ResearchState) -> ResearchState:
        findings_to_save = state.get("findings_to_save", {})
        file_path = state.get("file_path", "unknown_file")
        query = state.get("brief", "No query provided")

        if not findings_to_save: return {}

        logger.info(f"💾 Saving findings to memory for file: {file_path}...")
        for agent_id, findings in findings_to_save.items():
            if not findings or agent_id not in AGENT_DB_MAP: continue

            # UPDATED: Extract only the most relevant text to save as the memory.
            content_to_save = None
            if isinstance(findings, dict):
                # Prioritize the final 'response' from the RAG tool
                rag_response = findings.get('tool_results', {}).get('query_rag_store', {}).get('response')
                # Fall back to the agent's overall 'summary' if the RAG response isn't available
                summary = findings.get('summary')
                content_to_save = rag_response or summary

            # Ensure we have something to save before calling the tool
            if content_to_save:
                try:
                    save_memories.invoke({
                        "agent_id": agent_id,
                        "file_path": file_path,
                        "content": content_to_save,  # Pass the extracted string
                        "query": query
                    })
                except Exception as e:
                    logger.error(f"❌ Failed to save memory directly for {agent_id}: {e}")
        logger.info("✅ Memories saved.")
        return {}

    def _synthesizer_node(self, state: ResearchState) -> ResearchState:
        logger.info("✍️ Synthesizing final report...")
        final_report = self.supervisor.synthesize_findings(state.get("agent_findings", {}))
        return {"final_report": final_report}

    # In graph/research_graph.py

    def run_research(self, brief: str, file_path: str, selected_prompts: Dict, analysis_result: Dict, agent_queue: list) -> Dict:
        initial_state = ResearchState(
            messages=[HumanMessage(content=brief)], brief=brief, file_path=file_path or "",
            selected_prompts=selected_prompts or {}, analysis_result=analysis_result,
            agent_queue=agent_queue, completed_agents=[], agent_findings={}, #<-- Corrected
            accumulated_context=f"Initial Brief: {brief}"
        )
        final_state = self.graph.invoke(initial_state)
        return {"success": True, "final_state": final_state}

    def resume_research(self, paused_state: Dict) -> Dict:
        logger.info("🚀 Resuming research workflow...")
        paused_state["is_paused_for_input"] = False
        paused_state["is_paused_for_memory_save"] = False
        final_state = self.graph.invoke(paused_state)
        return {"success": True, "final_state": final_state}








