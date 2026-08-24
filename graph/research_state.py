from typing_extensions import TypedDict
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class ResearchState(TypedDict):
    # Existing core fields
    messages: List[BaseMessage]
    brief: str
    file_path: str
    selected_prompts: Dict[str, Any]
    required_agents: List[str]
    topics: Dict[str, Any]
    coordination_plan: str
    agent_findings: Dict[str, Any]
    current_agent: str
    completed_agents: List[str]
    final_report: str
    next_action: str
    analysis_result: Optional[Dict[str, Any]]

    # Existing fields for agent handoff
    accumulated_context: str                    
    agent_queue: List[str]                     
    last_completed_agent: str                  
    supervisor_feedback: str                   
    previous_findings: Optional[Dict[str, Any]] 

    # Existing fields for pausing and resuming
    is_paused_for_input: bool                  
    selected_test_case: Optional[str]          

    # New fields for memory agent workflow
    is_paused_for_memory_save: bool            
    user_memory_save_decision: Optional[bool]  
    findings_to_save: Optional[Dict[str, Any]] 
    retrieved_memories: Optional[Dict[str, Any]] # UPDATED: To store memories from DB
    findings_for_current_agent: Optional[Dict[str, Any]]