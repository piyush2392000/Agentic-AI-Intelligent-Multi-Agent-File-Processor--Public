# import asyncio
# import streamlit as st
# from typing import Dict, Any
# import os
# import json
# import re
 
# # Assume these imports are correctly pointing to your project structure
# from agents.agent_executor import ResearchSupervisorAgent
# from agents.a2a_factory import A2AAgentFactory
# from agents.a2a_system import _global_registry
# from graph.research_graph import ResearchGraph
# from config import load_prompts, load_email_config
# from tools.registry import get_all_registered_tools
 
 
# class AgenticAIApp:
#     def __init__(self):
#         self.prompts = load_prompts()
#         supervisor_card = _global_registry.get_agent_card("research_supervisor")
#         self.supervisor_agent = ResearchSupervisorAgent(supervisor_card, self.prompts)
#         self.agent_factory = A2AAgentFactory()
#         self.graph = ResearchGraph(self.prompts, self.supervisor_agent, self.agent_factory)
 
#     def _tokenize_key(self, key: str) -> set:
#         words = re.split(r'[_\-]+', key)
#         final_tokens = set()
#         for word in words:
#             tokens_from_word = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\s|$)', word)
#             for token in tokens_from_word:
#                 final_tokens.add(token.lower())
#         final_tokens.discard("prompt")
#         return final_tokens
 
#     # def _split_test_cases(self, text: str) -> list[str]:
#     #     pattern = r'(Test\s*Case\s*-\s*\d+.*?)(?=Test\s*Case\s*-\s*\d+|$)'
#     #     return [m.strip() for m in re.findall(pattern, text, flags=re.DOTALL)]
#     def _split_test_cases(self,text: str) -> list[str]:
#         """
#         Splits a string into a list of test cases.

#         This version handles test case headers both with and without a hyphen,
#         e.g., "Test Case - 1" and "Test Case 1".
#         """
#         # The modified pattern makes the hyphen and its surrounding spaces optional
#         # using the non-capturing group `(?:\s*-\s*)?`.
#         pattern = r'(Test\s*Case\s+(?:-\s*)?\d+.*?)(?=Test\s*Case\s+(?:-\s*)?\d+|$)'
        
#         return [m.strip() for m in re.findall(pattern, text, flags=re.DOTALL)]
    
#     def match_prompts_to_query(self, user_query: str, required_agents: list) -> Dict[str, Dict[str, str]]:
#         user_query_lower = user_query.lower()
#         final_selections = {}
 
#         for agent_id in required_agents:
#             agent_prompts = self.prompts.get(agent_id, {})
#             if not agent_prompts:
#                 continue
 
#             matched_info = None
#             matched_keywords = []
 
#             for key, text in agent_prompts.items():
#                 if key.strip().lower() in ["system_prompt", "default"]:
#                     continue
 
#                 key_tokens = self._tokenize_key(key)
 
#                 for token in key_tokens:
#                     if token in user_query_lower:
#                         matched_keywords.append(token)
 
#                 if matched_keywords:
#                     matched_info = {
#                         "prompt_text": text,
#                         "match_type": "keyword",
#                         "matched_keywords": matched_keywords
#                     }
#                     break
 
#             if not matched_info and "default" in (k.lower() for k in agent_prompts.keys()):
#                 matched_info = {
#                     "prompt_text": agent_prompts.get("Default", agent_prompts.get("default")),
#                     "match_type": "default",
#                     "matched_keywords": []
#                 }
 
#             if matched_info:
#                 final_selections[agent_id] = matched_info
 
#         return final_selections
 
#     async def process_query(self, file_path: str, user_query: str) -> Dict[str, Any]:
#         """Initiates a new research task."""
#         try:
#             with st.spinner("Analyzing request and creating execution plan..."):
#                 analysis_json = self.supervisor_agent.run({"brief": user_query, "file_path": file_path})
#                 analysis_result = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
#             st.session_state['execution_plan'] = analysis_result.get('required_agents', [])
#             required_agents = analysis_result.get("required_agents", [])
#             selected_prompts = self.match_prompts_to_query(user_query, required_agents)

#             return await asyncio.to_thread(
#                 self.graph.run_research,
#                 brief=user_query,
#                 file_path=file_path,
#                 selected_prompts=selected_prompts,
#                 analysis_result=analysis_result
#             )
#         except Exception as e:
#             st.error(f"Error during initial processing: {e}")
#             return {"success": False, "error": str(e)}

#     async def resume_with_test_case(self, paused_state: Dict[str, Any], selected_case: str) -> Dict[str, Any]:
#         """Resumes the graph after a test case has been selected."""
#         if not paused_state:
#             return {"success": False, "error": "Cannot resume, no paused state found."}
 
#         paused_state['selected_test_case'] = selected_case
#         return await asyncio.to_thread(self.graph.resume_research, paused_state)

#     async def resume_with_memory_decision(self, paused_state: Dict[str, Any], decision: bool) -> Dict[str, Any]:
#         """Resumes the graph after the user decides whether to save memories."""
#         if not paused_state:
#             return {"success": False, "error": "Cannot resume, no paused state found."}

#         paused_state['user_memory_save_decision'] = decision
#         return await asyncio.to_thread(self.graph.resume_research, paused_state)

#     def _apply_custom_styling(self):
#         st.markdown("""<style>/* 
#                         /* Top menu bar */
#                 header, .css-1v3fvcr {
#                     background-color: #1c1f26 !important;
#                     color: #e0e0e0 !important;
#                 }
                
#                 /* Hamburger menu and text */
#                 .css-1v3fvcr div {
#                     color: #e0e0e0 !important;
#                 }
#                 /* Set a high-contrast default text color for the entire app */
#                 .stApp {
#                     background: linear-gradient(to right bottom, #0d1b2a, #1b263b, #415a77);
#                     background-attachment: fixed;
#                     color: #FFFFFF !important;
#                 }
                
#                 /* Style the top header bar to match the dark theme */
#                 div[data-testid="stHeader"] {
#                     background-color: #0d1b2a !important;
#                 }

#                 /* Style the st.info box for better visibility */
#                 div[data-testid="stAlert"] {
#                     background-color: rgba(119, 141, 169, 0.2) !important;
#                     border: 1px solid #778da9 !important;
#                     border-radius: 8px !important;
#                 }
#                 div[data-testid="stAlert"] div { /* Target the text inside */
#                     color: #EAEAEA !important;
#                 }

#                 /* Force all headers to be bright white */
#                 h1, h2, h3, h4, h5, h6 {
#                     color: #FFFFFF !important;
#                 }

#                 /* Target specific Streamlit elements to ensure their text is white */
#                 div[data-testid="stMarkdown"] p,
#                 div[data-testid="stMarkdown"] li,
#                 label[data-testid="stWidgetLabel"],
#                 div[data-testid="stText"] {
#                     color: #FFFFFF !important;
#                 }
                
#                 /* Reduce spacing around the main divider */
#                 hr {
#                     margin-top: 0.75rem !important;
#                     margin-bottom: 1rem !important;
#                 }
#                 h3 {
#                     margin-top: 0 !important;
#                 }

#                 /* --- Input & Widget Styling --- */
#                 .stTextInput input, .stTextArea textarea {
#                     background-color: #1b263b;
#                     border: 1px solid #778da9;
#                     color: #FFFFFF;
#                     border-radius: 5px;
#                 }

#                 /* Make placeholder text visible */
#                 ::placeholder {
#                     color: #bdc3c7 !important;
#                     opacity: 1;
#                 }
                
#                 /* This uses the exact class name from your browser's HTML */
#                 .st-emotion-cache-1gulkj5 {
#                     background-color: #1b263b !important;
#                     border: 2px dashed #778da9 !important;
#                     border-radius: 5px !important;
#                 }
#                 /* This makes all text and icons inside the dropzone white */
#                 .st-emotion-cache-1gulkj5 * {
#                     color: #FFFFFF !important;
#                 }
#                 /* This styles the 'Browse files' button to be orange */
#                 .st-emotion-cache-1gulkj5 button {
#                     background-color: #F39C12 !important;
#                     color: #FFFFFF !important;
#                     border: none !important;
#                     transition: all 0.3s ease;
#                 }
#                 .st-emotion-cache-1gulkj5 button:hover {
#                     background-color: #E67E22 !important;
#                 }
                
#                 /* This targets the label and any text element inside it */
#                 div[data-testid="stCheckbox"] label,
#                 div[data-testid="stCheckbox"] label p,
#                 div[data-testid="stCheckbox"] label span {
#                     color: #FFFFFF !important;
#                 }

#                 /* --- Button Styling --- */
#                 .stButton > button {
#                     background-color: #415A77;
#                     color: #FFFFFF !important;
#                     border: 2px solid #778DA9;
#                     border-radius: 8px;
#                     font-weight: bold;
#                     transition: all 0.3s ease;
#                 }
#                 .stButton > button:hover {
#                     background-color: #778DA9;
#                     border-color: #FFFFFF;
#                 }
#                      */</style>""", unsafe_allow_html=True) # Abridged for brevity

#     def run_streamlit_app(self):
#         st.set_page_config(layout="wide")
#         self._apply_custom_styling()
 
#         # --- SESSION STATE INITIALIZATION ---
#         if 'rag_response' not in st.session_state: st.session_state['rag_response'] = None
#         if 'split_test_cases' not in st.session_state: st.session_state['split_test_cases'] = []
#         if 'selected_testcase' not in st.session_state: st.session_state['selected_testcase'] = None
#         if 'generated_script' not in st.session_state: st.session_state['generated_script'] = None
#         if 'paused_graph_state' not in st.session_state: st.session_state['paused_graph_state'] = None
#         if 'final_report' not in st.session_state: st.session_state['final_report'] = None
#         if 'uploaded_filename' not in st.session_state: st.session_state['uploaded_filename'] = ""
#         if 'original_query' not in st.session_state: st.session_state['original_query'] = ""
       
#         # --- HEADER ---
#         st.title("🚀 Agentic AI - Intelligent File Processor")
#         st.markdown("Upload a file, describe your goal, and let the AI agents handle the rest.")
#         st.divider()
 
#         # --- INPUT SECTION ---
#         with st.container():
#             st.subheader("1. Provide your file and instructions")
           
#             user_query = st.text_input("What do you want to do with the uploaded file?", placeholder="e.g., analyze this pcap for suspicious traffic")
#             uploaded_file = st.file_uploader("Upload your file", type=['pcap', 'txt', 'log', 'json', 'csv', 'pdf'])
           
#             if st.button("▶️ Run Analysis", use_container_width=True):
#                 st.session_state.clear()
#                 if uploaded_file and user_query:
#                     st.session_state['original_query'] = user_query
#                     st.session_state['uploaded_filename'] = uploaded_file.name
                   
#                     temp_path = f"temp_{uploaded_file.name}"
#                     try:
#                         with open(temp_path, "wb") as f: f.write(uploaded_file.getvalue())
#                         run_output = asyncio.run(self.process_query(temp_path, user_query))
                        
#                         if run_output and run_output.get("success"):
#                             st.session_state['paused_graph_state'] = run_output.get("final_state", {})
#                             st.rerun() # Rerun to display results and new UI components
#                         else:
#                             st.error(f"Processing failed: {run_output.get('error', 'Unknown error')}")
                    
#                     except Exception as e:
#                         st.error(f"Application error: {str(e)}")
#                     finally:
#                         if os.path.exists(temp_path): os.remove(temp_path)
        
#         # --- CENTRALIZED STATE HANDLING & DISPLAY ---
#         paused_state = st.session_state.get('paused_graph_state') # Get state once
#         if paused_state:
#             findings = paused_state.get("agent_findings", {})

#             # Extract RAG response for display if it exists
#             response_found = False
#             for agent_data in findings.values():
#                 if isinstance(agent_data, dict):
#                     tool_results = agent_data.get("tool_results", {})
#                     for tool_data in tool_results.values():
#                         if isinstance(tool_data, dict) and "response" in tool_data:
#                             st.session_state['rag_response'] = tool_data["response"]
#                             response_found = True
#                             break
#                 if response_found: break

#         # --- AGENT RESPONSE SECTION ---
#         if st.session_state.get('rag_response'):
#             with st.container(border=True):
#                 st.subheader("🤖 Agent Response")
#                 st.markdown(st.session_state['rag_response'])
 
#         # --- TEST CASE UI SECTION ---
#         # FIX 1: Check if paused_state is not None before calling .get()
#         if paused_state and paused_state.get('is_paused_for_input'):
#             with st.container(border=True):
#                 st.subheader("🧪 Choose a Test Case to Generate a Script")
#                 print(st.session_state.get('rag_response'),"responseeeeeee")
#                 if not st.session_state.get('split_test_cases') and st.session_state.get('rag_response'):
#                     st.session_state['split_test_cases'] = self._split_test_cases(st.session_state['rag_response'])
#                     print(st.session_state['split_test_cases'],"test cases")
                
#                 test_cases = st.session_state.get('split_test_cases', [])
#                 if test_cases:
#                     cols = st.columns(min(5, len(test_cases)))
#                     for i, case in enumerate(test_cases):
#                         case_id = f"Test Case {i + 1}"
#                         if cols[i % len(cols)].button(case_id, key=f"button_{i}", use_container_width=True):
#                             st.session_state['selected_testcase'] = case
#                             st.rerun() # Rerun to show the selected case editor
#                 else:
#                     st.warning("No test cases were found in the agent's response.")
 
#         # --- SELECTED TEST CASE & SCRIPT GENERATION ---
#         if st.session_state.get('selected_testcase') and not st.session_state.get('generated_script'):
#              with st.container(border=True):
#                 st.subheader("📝 Edit Selected Test Case")
#                 edited_testcase = st.text_area("You can edit the test case below before generating the script:", st.session_state['selected_testcase'], height=250)
#                 if st.button("Generate Test Script", use_container_width=True):
#                     with st.spinner("Resuming workflow and generating script..."):
#                         resume_output = asyncio.run(self.resume_with_test_case(paused_state, edited_testcase))
#                         if resume_output and resume_output.get("success"):
#                             st.session_state['paused_graph_state'] = resume_output.get("final_state", {})
#                             script_findings = st.session_state['paused_graph_state'].get("agent_findings", {}).get("test_script_agent", {})
#                             script_output = script_findings.get("tool_results", {}).get("generate_test_script", {})
#                             if script_output.get("success"):
#                                 st.session_state['generated_script'] = script_output.get("test_script")
#                             st.rerun()

#         # --- DISPLAY GENERATED SCRIPT ---
#         if st.session_state.get('generated_script'):
#             with st.container(border=True):
#                 st.subheader("🐍 Generated Test Script")
#                 st.code(st.session_state['generated_script'], language="python")

#         # --- MEMORY SAVE UI SECTION ---
#         # FIX 2: Check if paused_state is not None before calling .get()
#         if paused_state and paused_state.get('is_paused_for_memory_save'):
#             with st.container(border=True):
#                 st.subheader("💾 Save Agent Findings to Memory?")
#                 st.info("Saving these findings will allow agents to reference this analysis in future tasks, potentially improving accuracy and relevance.")
                
#                 col1, col2 = st.columns(2)
#                 if col1.button("✅ Yes, Save and Finish", use_container_width=True, type="primary"):
#                     with st.spinner("Saving memories and finalizing report..."):
#                         resume_output = asyncio.run(self.resume_with_memory_decision(paused_state, True))
#                         if resume_output and resume_output.get("success"):
#                             st.session_state['final_report'] = resume_output.get("final_state", {}).get('final_report')
#                             st.session_state['paused_graph_state'] = None # Clear paused state
#                             st.success("Findings saved to memory!")
#                             st.rerun()

#                 if col2.button("❌ No, Just Finish", use_container_width=True):
#                     with st.spinner("Finalizing report..."):
#                         resume_output = asyncio.run(self.resume_with_memory_decision(paused_state, False))
#                         if resume_output and resume_output.get("success"):
#                              st.session_state['final_report'] = resume_output.get("final_state", {}).get('final_report')
#                              st.session_state['paused_graph_state'] = None # Clear paused state
#                              st.rerun()

#         # --- FINAL REPORT AND EMAIL SECTION ---
#         if st.session_state.get("final_report"):
#             with st.container(border=True):
#                 st.header("📋 Final Report")
#                 st.markdown(st.session_state['final_report'])
            
#             with st.container(border=True):
#                 st.header("📧 Share Report via Email")
#                 email_cfg = load_email_config()
#                 default_recipients = ", ".join(email_cfg.get("default_recipients", []))
                
#                 recipients_text = st.text_input("Recipients (comma-separated)", value=default_recipients)
#                 subject_text = st.text_input("Subject", value=f"AgenticAI Analysis Report - {st.session_state.get('uploaded_filename', 'Analysis')}")
                
#                 # Show preview of what will be in the email
#                 st.info("📋 Email Preview: A professional report card will be sent with the complete analysis attached as a TXT file.")
                
#                 # with st.expander("📄 View Email Content Preview"):
#                 #     st.markdown("**Email will contain:**")
#                 #     st.markdown("- 🎨 Professional header with LTTS branding")
#                 #     st.markdown("- 📊 Executive summary of analysis")
#                 #     st.markdown("- 🔍 Original query and file information")
#                 #     st.markdown("- 🚦 System status indicator (Green/Yellow/Red)")
#                 #     st.markdown("- 📎 Complete detailed analysis as TXT attachment")
#                 #     st.markdown("- 💼 Professional footer with company branding")
                
#                 if st.checkbox("Send this professional report by email"):
#                     if st.button("📤 Send Professional Report", use_container_width=True):
#                         all_tools = get_all_registered_tools()
#                         send_tool = all_tools.get("send_email")
#                         if send_tool is None:
#                             st.error("Email tool not found.")
#                         else:
#                             # Get the original query from session state
#                             original_query = st.session_state.get("original_query", "Analysis request")
                            
#                             payload = {
#                                 "recipients": [r.strip() for r in recipients_text.split(",") if r.strip()],
#                                 "subject": subject_text,
#                                 "body": st.session_state.get("rag_response", ""),
#                                 "query": original_query,
#                                 "filename": st.session_state.get('uploaded_filename', ''),
#                             }
#                             with st.spinner("📧 Sending professional report with attachment..."):
#                                 try:
#                                     resp = send_tool.invoke(payload)
#                                     if isinstance(resp, dict) and resp.get("success"):
#                                         st.success(f"✅ Professional report sent successfully!")
#                                         st.info(f"📊 Report details: {resp.get('message')}")
                                        
#                                     else:
#                                         err = resp.get("error") if isinstance(resp, dict) else str(resp)
#                                         st.error(f"Failed to send email: {err}")
#                                 except Exception as e:
#                                     st.error(f"Exception while sending email: {e}")

 
# if __name__ == "__main__":
#     app = AgenticAIApp()
#     app.run_streamlit_app()



import asyncio
import streamlit as st
from typing import Dict, Any
import os
import json
import re
 
# Assume these imports are correctly pointing to your project structure
from agents.agent_executor import ResearchSupervisorAgent
from agents.a2a_factory import A2AAgentFactory
from agents.a2a_system import _global_registry
from graph.research_graph import ResearchGraph
from config import load_prompts, load_email_config
from tools.registry import get_all_registered_tools
 
 
class AgenticAIApp:
    def __init__(self):
        self.prompts = load_prompts()
        supervisor_card = _global_registry.get_agent_card("research_supervisor")
        self.supervisor_agent = ResearchSupervisorAgent(supervisor_card, self.prompts)
        self.agent_factory = A2AAgentFactory()
        self.graph = ResearchGraph(self.prompts, self.supervisor_agent, self.agent_factory)
 
    def _tokenize_key(self, key: str) -> set:
        words = re.split(r'[_\-]+', key)
        final_tokens = set()
        for word in words:
            tokens_from_word = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\s|$)', word)
            for token in tokens_from_word:
                final_tokens.add(token.lower())
        final_tokens.discard("prompt")
        return final_tokens
 
    def _split_test_cases(self,text: str) -> list[str]:
        """
        Splits a string into a list of test cases.
        This version handles test case headers both with and without a hyphen,
        e.g., "Test Case - 1" and "Test Case 1".
        """
        # The modified pattern makes the hyphen and its surrounding spaces optional
        # using the non-capturing group `(?:\s*-\s*)?`.
        pattern = r'(Test\s*Case\s+(?:-\s*)?\d+.*?)(?=Test\s*Case\s+(?:-\s*)?\d+|$)'
        
        return [m.strip() for m in re.findall(pattern, text, flags=re.DOTALL)]
    
    def match_prompts_to_query(self, user_query: str, required_agents: list) -> Dict[str, Dict[str, str]]:
        user_query_lower = user_query.lower()
        final_selections = {}
 
        for agent_id in required_agents:
            agent_prompts = self.prompts.get(agent_id, {})
            if not agent_prompts:
                continue
 
            matched_info = None
            matched_keywords = []
 
            for key, text in agent_prompts.items():
                if key.strip().lower() in ["system_prompt", "default"]:
                    continue
 
                key_tokens = self._tokenize_key(key)
 
                for token in key_tokens:
                    if token in user_query_lower:
                        matched_keywords.append(token)
 
                if matched_keywords:
                    matched_info = {
                        "prompt_text": text,
                        "match_type": "keyword",
                        "matched_keywords": matched_keywords
                    }
                    break
 
            if not matched_info and "default" in (k.lower() for k in agent_prompts.keys()):
                matched_info = {
                    "prompt_text": agent_prompts.get("Default", agent_prompts.get("default")),
                    "match_type": "default",
                    "matched_keywords": []
                }
 
            if matched_info:
                final_selections[agent_id] = matched_info
 
        return final_selections
 
    async def process_query(self, file_path: str, user_query: str) -> Dict[str, Any]:
        """Initiates a new research task."""
        try:
            with st.spinner("Analyzing request and creating execution plan..."):
                analysis_json = self.supervisor_agent.run({"brief": user_query, "file_path": file_path})
                analysis_result = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
            st.session_state['execution_plan'] = analysis_result.get('required_agents', [])
            # required_agents = analysis_result.get("required_agents", [])
            # selected_prompts = self.match_prompts_to_query(user_query, required_agents)

            # return await asyncio.to_thread(
            #     self.graph.run_research,
            #     brief=user_query,
            #     file_path=file_path,
            #     selected_prompts=selected_prompts,
            #     analysis_result=analysis_result
            # )
            # In main2.py -> process_query method

            required_agents = analysis_result.get("required_agents", [])
            selected_prompts = self.match_prompts_to_query(user_query, required_agents)

            return await asyncio.to_thread(
                self.graph.run_research,
                brief=user_query,
                file_path=file_path,
                selected_prompts=selected_prompts,
                analysis_result=analysis_result,
                agent_queue=required_agents #<-- Add this line
            )
        except Exception as e:
            st.error(f"Error during initial processing: {e}")
            return {"success": False, "error": str(e)}

    async def resume_with_test_case(self, paused_state: Dict[str, Any], selected_case: str) -> Dict[str, Any]:
        """Resumes the graph after a test case has been selected."""
        if not paused_state:
            return {"success": False, "error": "Cannot resume, no paused state found."}
 
        paused_state['selected_test_case'] = selected_case
        return await asyncio.to_thread(self.graph.resume_research, paused_state)

    async def resume_with_memory_decision(self, paused_state: Dict[str, Any], decision: bool) -> Dict[str, Any]:
        """Resumes the graph after the user decides whether to save memories."""
        if not paused_state:
            return {"success": False, "error": "Cannot resume, no paused state found."}

        paused_state['user_memory_save_decision'] = decision
        return await asyncio.to_thread(self.graph.resume_research, paused_state)

    def _apply_custom_styling(self):
        st.markdown("""<style>
                /* Set a high-contrast default text color for the entire app */
                .stApp {
                    background: linear-gradient(to right bottom, #0d1b2a, #1b263b, #415a77);
                    background-attachment: fixed;
                    color: #FFFFFF !important;
                }
                
                /* Style the top header bar to match the dark theme */
                div[data-testid="stHeader"] {
                    background-color: #0d1b2a !important;
                }

                /* Style the st.info box for better visibility */
                div[data-testid="stAlert"] {
                    background-color: rgba(119, 141, 169, 0.2) !important;
                    border: 1px solid #778da9 !important;
                    border-radius: 8px !important;
                }
                div[data-testid="stAlert"] div { /* Target the text inside */
                    color: #EAEAEA !important;
                }

                /* Force all headers to be bright white */
                h1, h2, h3, h4, h5, h6 {
                    color: #FFFFFF !important;
                }

                /* Target specific Streamlit elements to ensure their text is white */
                div[data-testid="stMarkdown"] p,
                div[data-testid="stMarkdown"] li,
                label[data-testid="stWidgetLabel"],
                div[data-testid="stText"] {
                    color: #FFFFFF !important;
                }
                
                hr {
                    margin-top: 0.75rem !important;
                    margin-bottom: 1rem !important;
                }
                h3 {
                    margin-top: 0 !important;
                }

                /* --- Input & Widget Styling --- */
                .stTextInput input, .stTextArea textarea {
                    background-color: #1b263b;
                    border: 1px solid #778da9;
                    color: #FFFFFF;
                    border-radius: 5px;
                }

                ::placeholder {
                    color: #bdc3c7 !important;
                    opacity: 1;
                }
                
                .st-emotion-cache-1gulkj5 {
                    background-color: #1b263b !important;
                    border: 2px dashed #778da9 !important;
                    border-radius: 5px !important;
                }
                .st-emotion-cache-1gulkj5 * {
                    color: #FFFFFF !important;
                }
                .st-emotion-cache-1gulkj5 button {
                    background-color: #F39C12 !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    transition: all 0.3s ease;
                }
                .st-emotion-cache-1gulkj5 button:hover {
                    background-color: #E67E22 !important;
                }
                
                div[data-testid="stCheckbox"] label,
                div[data-testid="stCheckbox"] label p,
                div[data-testid="stCheckbox"] label span {
                    color: #FFFFFF !important;
                }

                /* --- Button Styling --- */
                .stButton > button {
                    background-color: #415A77;
                    color: #FFFFFF !important;
                    border: 2px solid #778DA9;
                    border-radius: 8px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                }
                .stButton > button:hover {
                    background-color: #778DA9;
                    border-color: #FFFFFF;
                }
                </style>""", unsafe_allow_html=True)

    def run_streamlit_app(self):
        st.set_page_config(layout="wide")
        self._apply_custom_styling()
 
        # --- SESSION STATE INITIALIZATION ---
        if 'rag_response' not in st.session_state: st.session_state['rag_response'] = None
        if 'split_test_cases' not in st.session_state: st.session_state['split_test_cases'] = []
        if 'selected_testcase' not in st.session_state: st.session_state['selected_testcase'] = None
        if 'generated_script' not in st.session_state: st.session_state['generated_script'] = None
        if 'paused_graph_state' not in st.session_state: st.session_state['paused_graph_state'] = None
        if 'final_report' not in st.session_state: st.session_state['final_report'] = None
        if 'uploaded_filename' not in st.session_state: st.session_state['uploaded_filename'] = ""
        if 'original_query' not in st.session_state: st.session_state['original_query'] = ""
       
        # --- HEADER ---
        st.title("🚀 Agentic AI - Intelligent File Processor")
        st.markdown("Upload a file, describe your goal, and let the AI agents handle the rest.")
        st.divider()
 
        # --- INPUT SECTION ---
        with st.container():
            st.subheader("1. Provide your file and instructions")
           
            user_query = st.text_input("What do you want to do with the uploaded file?", placeholder="e.g., analyze this pcap for suspicious traffic")
            uploaded_file = st.file_uploader("Upload your file", type=['pcap', 'txt', 'log', 'json', 'csv', 'pdf'])
           
            if st.button("▶️ Run Analysis", use_container_width=True):
                st.session_state.clear()
                if uploaded_file and user_query:
                    st.session_state['original_query'] = user_query
                    st.session_state['uploaded_filename'] = uploaded_file.name
                   
                    temp_path = f"temp_{uploaded_file.name}"
                    try:
                        with open(temp_path, "wb") as f: f.write(uploaded_file.getvalue())
                        run_output = asyncio.run(self.process_query(temp_path, user_query))
                        
                        if run_output and run_output.get("success"):
                            st.session_state['paused_graph_state'] = run_output.get("final_state", {})
                            st.rerun() 
                        else:
                            st.error(f"Processing failed: {run_output.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"Application error: {str(e)}")
                    finally:
                        if os.path.exists(temp_path): os.remove(temp_path)
        
        # --- CENTRALIZED STATE HANDLING & DISPLAY ---
        paused_state = st.session_state.get('paused_graph_state') 
        if paused_state:
            findings = paused_state.get("agent_findings", {})

            # Extract RAG response for display if it exists
            response_found = False
            for agent_data in findings.values():
                if isinstance(agent_data, dict):
                    tool_results = agent_data.get("tool_results", {})
                    for tool_data in tool_results.values():
                        if isinstance(tool_data, dict) and "response" in tool_data:
                            st.session_state['rag_response'] = tool_data["response"]
                            response_found = True
                            break
                if response_found: break

        # --- AGENT RESPONSE SECTION ---
        if st.session_state.get('rag_response'):
            with st.container(border=True):
                st.subheader("🤖 Agent Response")
                st.markdown(st.session_state['rag_response'])
 
        # --- TEST CASE UI SECTION ---
        if paused_state and paused_state.get('is_paused_for_input'):
            with st.container(border=True):
                st.subheader("🧪 Choose a Test Case to Generate a Script")
                
                if not st.session_state.get('split_test_cases') and st.session_state.get('rag_response'):
                    st.session_state['split_test_cases'] = self._split_test_cases(st.session_state['rag_response'])
                
                test_cases = st.session_state.get('split_test_cases', [])
                if test_cases:
                    cols = st.columns(min(5, len(test_cases)))
                    for i, case in enumerate(test_cases):
                        case_id = f"Test Case {i + 1}"
                        if cols[i % len(cols)].button(case_id, key=f"button_{i}", use_container_width=True):
                            st.session_state['selected_testcase'] = case
                            st.rerun() 
                else:
                    st.warning("No test cases were found in the agent's response.")
 
        # --- SELECTED TEST CASE & SCRIPT GENERATION ---
        if st.session_state.get('selected_testcase') and not st.session_state.get('generated_script'):
             with st.container(border=True):
                st.subheader("📝 Edit Selected Test Case")
                edited_testcase = st.text_area("You can edit the test case below before generating the script:", st.session_state['selected_testcase'], height=250)
                if st.button("Generate Test Script", use_container_width=True):
                    with st.spinner("Resuming workflow and generating script..."):
                        resume_output = asyncio.run(self.resume_with_test_case(paused_state, edited_testcase))
                        if resume_output and resume_output.get("success"):
                            st.session_state['paused_graph_state'] = resume_output.get("final_state", {})
                            
                            # ✅ ROBUST SCRIPT EXTRACTION LOGIC
                            agent_findings = st.session_state['paused_graph_state'].get("agent_findings", {})
                            script_findings = agent_findings.get("test_script_agent", {})

                            # Check if script_findings is a dictionary and contains the script
                            if isinstance(script_findings, dict) and script_findings.get("test_script"):
                                st.session_state['generated_script'] = script_findings.get("test_script")
                            else:
                                # Fallback for nested structure if needed
                                tool_results = script_findings.get("tool_results", {}).get("generate_test_script", {})
                                if isinstance(tool_results, dict) and tool_results.get("test_script"):
                                    st.session_state['generated_script'] = tool_results.get("test_script")
                                else:
                                    st.warning("Could not find the generated test script in the agent's response.")
                                    st.write("Agent Findings for Debugging:", script_findings)

                            st.rerun()

        # --- DISPLAY GENERATED SCRIPT ---
        if st.session_state.get('generated_script'):
            with st.container(border=True):
                st.subheader("🐍 Generated Test Script")
                st.code(st.session_state['generated_script'], language="python")

        # --- MEMORY SAVE UI SECTION ---
        if paused_state and paused_state.get('is_paused_for_memory_save'):
            with st.container(border=True):
                st.subheader("💾 Save Agent Findings to Memory?")
                st.info("Saving these findings will allow agents to reference this analysis in future tasks, potentially improving accuracy and relevance.")
                
                col1, col2 = st.columns(2)
                if col1.button("✅ Yes, Save and Finish", use_container_width=True, type="primary"):
                    with st.spinner("Saving memories and finalizing report..."):
                        resume_output = asyncio.run(self.resume_with_memory_decision(paused_state, True))
                        if resume_output and resume_output.get("success"):
                            st.session_state['final_report'] = resume_output.get("final_state", {}).get('final_report')
                            st.session_state['paused_graph_state'] = None 
                            st.success("Findings saved to memory!")
                            st.rerun()

                if col2.button("❌ No, Just Finish", use_container_width=True):
                    with st.spinner("Finalizing report..."):
                        resume_output = asyncio.run(self.resume_with_memory_decision(paused_state, False))
                        if resume_output and resume_output.get("success"):
                             st.session_state['final_report'] = resume_output.get("final_state", {}).get('final_report')
                             st.session_state['paused_graph_state'] = None
                             st.rerun()

        # --- FINAL REPORT AND EMAIL SECTION ---
        if st.session_state.get("final_report"):
            with st.container(border=True):
                st.header("📋 Final Report")
                st.markdown(st.session_state['final_report'])
            
            with st.container(border=True):
                st.header("📧 Share Report via Email")
                email_cfg = load_email_config()
                default_recipients = ", ".join(email_cfg.get("default_recipients", []))
                
                recipients_text = st.text_input("Recipients (comma-separated)", value=default_recipients)
                subject_text = st.text_input("Subject", value=f"AgenticAI Analysis Report - {st.session_state.get('uploaded_filename', 'Analysis')}")
                
                st.info("📋 Email Preview: A professional report card will be sent with the complete analysis attached as a TXT file.")
                
                if st.checkbox("Send this professional report by email"):
                    if st.button("📤 Send Professional Report", use_container_width=True):
                        all_tools = get_all_registered_tools()
                        send_tool = all_tools.get("send_email")
                        if send_tool is None:
                            st.error("Email tool not found.")
                        else:
                            original_query = st.session_state.get("original_query", "Analysis request")
                            
                            payload = {
                                "recipients": [r.strip() for r in recipients_text.split(",") if r.strip()],
                                "subject": subject_text,
                                "body": st.session_state.get("rag_response", ""),
                                "query": original_query,
                                "filename": st.session_state.get('uploaded_filename', ''),
                            }
                            with st.spinner("📧 Sending professional report with attachment..."):
                                try:
                                    resp = send_tool.invoke(payload)
                                    if isinstance(resp, dict) and resp.get("success"):
                                        st.success(f"✅ Professional report sent successfully!")
                                        st.info(f"📊 Report details: {resp.get('message')}")
                                        
                                    else:
                                        err = resp.get("error") if isinstance(resp, dict) else str(resp)
                                        st.error(f"Failed to send email: {err}")
                                except Exception as e:
                                    st.error(f"Exception while sending email: {e}")
 
if __name__ == "__main__":
    app = AgenticAIApp()
    app.run_streamlit_app()

