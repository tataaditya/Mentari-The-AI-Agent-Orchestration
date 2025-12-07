"""
MENTARI V.22 PRO - FIXED STREAMING & HARD STOPS
AI Assistant with Office, File Management, PDF & SOCIAL MEDIA FILE UPLOAD

FIXES:
✅ Fixed async generator cleanup
✅ Proper tool limit enforcement
✅ Better MCP resource management
✅ Hard stop after success
✅ Reduced API calls
"""

import asyncio
import os
import sys
import shutil
import urllib.request
from contextlib import AsyncExitStack
from typing import Optional, List, Dict
from collections import deque
from pathlib import Path
import time

import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

# ============================================================================
# CONFIGURATION
# ============================================================================
current_dir = os.getcwd()

USER_FILES_DIR = os.path.join(current_dir, "USER_FILES")
os.makedirs(USER_FILES_DIR, exist_ok=True)

fs_js_path = os.path.join(current_dir, "filesystem-mcp-server", "dist", "index.js")

excel_src = os.path.join(current_dir, "excel-mcp-server", "src")
if excel_src not in sys.path:
    sys.path.insert(0, excel_src)

excel_env = os.environ.copy()
excel_env["PYTHONPATH"] = excel_src + os.pathsep + excel_env.get("PYTHONPATH", "")

MCP_CONFIG = {
    "filesystem": {
        "command": "node",
        "args": [fs_js_path, USER_FILES_DIR],
        "env": None,
        "timeout": 10
    },
    "word": {
        "command": sys.executable,
        "args": ["Office-Word-MCP-Server/word_mcp_server.py"],
        "env": None,
        "timeout": 15
    },
    "excel": {
        "command": sys.executable,
        "args": ["-m", "excel_mcp", "stdio"],
        "env": excel_env,
        "cwd": excel_src,
        "timeout": 15
    },
    "powerpoint": {
        "command": sys.executable,
        "args": ["Office-PowerPoint-MCP-Server/ppt_mcp_server.py"],
        "env": None,
        "timeout": 15
    },
    "pdf": {
        "command": sys.executable,
        "args": [r"D:\Ruang_Lab\Percobaan_Menhan2\PDF-Reader-MCP.py"],
        "env": None,
        "timeout": 20
    }
}

# ============================================================================
# GLOBAL STATE
# ============================================================================
class GlobalState:
    def __init__(self):
        self.tool_calls = {}
        self.should_stop = False
        self.last_result = None
    
    def reset(self):
        self.tool_calls.clear()
        self.should_stop = False
        self.last_result = None
    
    def track_call(self, tool_name: str) -> int:
        if tool_name not in self.tool_calls:
            self.tool_calls[tool_name] = 0
        self.tool_calls[tool_name] += 1
        return self.tool_calls[tool_name]
    
    def mark_success(self, result: str):
        self.should_stop = True
        self.last_result = result
    
    def mark_failure(self, result: str):
        self.should_stop = True
        self.last_result = result

global_state = GlobalState()

# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================
class ChatHistoryManager:
    def __init__(self, max_pairs: int = 6):  # Further reduced
        self.max_pairs = max_pairs
        self.system_prompt: Optional[SystemMessage] = None
        self.history: deque = deque(maxlen=max_pairs * 2)
    
    def set_system_prompt(self, prompt: str):
        self.system_prompt = SystemMessage(content=prompt)
    
    def add_message(self, message: BaseMessage):
        self.history.append(message)
    
    def get_messages(self) -> List[BaseMessage]:
        messages = []
        if self.system_prompt:
            messages.append(self.system_prompt)
        messages.extend(list(self.history))
        return messages
    
    def clear(self):
        self.history.clear()

# ============================================================================
# FILE DETECTION
# ============================================================================
def detect_file_category(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    
    categories = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'},
        'video': {'.mp4', '.avi', '.mov', '.mkv', '.webm'},
        'office': {'.docx', '.xlsx', '.pptx'},
        'pdf': {'.pdf'},
        'code': {'.py', '.js', '.html', '.css'},
        'document': {'.txt', '.md', '.csv', '.json'},
    }
    
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    
    return 'other'

# ============================================================================
# OPTIMIZED TOOL WRAPPER WITH HARD STOP
# ============================================================================
def create_verified_tool(session, tool, work_dir, server_name):
    """Tool wrapper with hard stop capability"""
    async def verified_wrapper(**kwargs):
        # Check global stop flag
        if global_state.should_stop:
            return f"🛑 STOPPED: Previous operation completed. No further actions needed."
        
        tool_full_name = f"{server_name}_{tool.name}"
        call_count = global_state.track_call(tool_full_name)
        
        # Hard limit
        max_allowed = 3 if 'pdf' in server_name else 2
        if call_count > max_allowed:
            global_state.mark_failure(f"Tool {tool_full_name} blocked after {call_count-1} calls")
            return f"🛑 BLOCKED: {tool_full_name} called too many times. Stop and report to user."
        
        try:
            # Unwrap kwargs
            if 'kwargs' in kwargs:
                kwargs = kwargs['kwargs']
            
            # Parameter fixing
            if hasattr(tool, 'inputSchema') and 'properties' in tool.inputSchema:
                expected_params = list(tool.inputSchema['properties'].keys())
                
                file_param = None
                for param in expected_params:
                    if any(kw in param.lower() for kw in ['path', 'file', 'name']):
                        file_param = param
                        break
                
                if file_param:
                    user_file_param = None
                    for key in list(kwargs.keys()):
                        if any(kw in key.lower() for kw in ['path', 'file', 'name']):
                            user_file_param = key
                            break
                    
                    if user_file_param and user_file_param != file_param:
                        kwargs[file_param] = kwargs.pop(user_file_param)
            
            # Server-specific fixes
            if server_name == 'pdf':
                if 'convert_word_to_pdf' in tool.name.lower():
                    renames = {'filepath': 'word_path', 'filename': 'word_path'}
                elif 'convert_pdf_to_word' in tool.name.lower():
                    renames = {'filepath': 'pdf_path', 'filename': 'pdf_path'}
                else:
                    renames = {'file_path': 'filepath', 'filename': 'filepath'}
                
                for old, new in renames.items():
                    if old in kwargs and new not in kwargs:
                        kwargs[new] = kwargs.pop(old)
            
            elif server_name == 'excel':
                if 'filename' in kwargs:
                    kwargs['filepath'] = kwargs.pop('filename')
            
            else:
                renames = {'file_path': 'filename', 'filepath': 'filename'}
                for old, new in renames.items():
                    if old in kwargs and new not in kwargs:
                        kwargs[new] = kwargs.pop(old)
            
            # Fix paths
            file_keys = [
                'filename', 'filepath', 'path', 'image_path', 
                'destination', 'source', 'word_path', 'pdf_path'
            ]
            
            for key in file_keys:
                if key in kwargs and isinstance(kwargs[key], str):
                    if not os.path.isabs(kwargs[key]):
                        kwargs[key] = os.path.abspath(os.path.join(work_dir, kwargs[key]))
            
            # Validate required
            if hasattr(tool, 'inputSchema'):
                required = tool.inputSchema.get('required', [])
                missing = [r for r in required if r not in kwargs]
                if missing:
                    global_state.mark_failure(f"Missing params: {missing}")
                    return f"❌ Missing: {', '.join(missing)}. Ask user."
            
            # Aggressive timeout
            if 'convert' in tool.name.lower() and server_name == 'pdf':
                timeout = 45.0  # Reduced from 60
            elif server_name == 'pdf':
                timeout = 20.0
            else:
                timeout = 12.0  # Reduced from 15
            
            # Execute
            result = await asyncio.wait_for(
                session.call_tool(tool.name, arguments=kwargs),
                timeout=timeout
            )
            
            result_text = str(result)
            result_lower = result_text.lower()
            
            # Detect hard errors
            hard_errors = [
                'validation error', 'failed to', 'error:', 'exception:',
                'could not', 'unable to', 'not found', 'invalid', 'timeout'
            ]
            
            if any(err in result_lower for err in hard_errors):
                error_msg = result_text[:150]
                global_state.mark_failure(error_msg)
                return f"❌ FAILED: {error_msg}\n\n🛑 STOP. Report to user. Do NOT retry."
            
            # Detect success
            success_keywords = [
                'successfully', 'created', 'saved', 'completed', 'done', '✅'
            ]
            
            if any(kw in result_lower for kw in success_keywords):
                global_state.mark_success(result_text)
                return f"✅ SUCCESS\n\n{result_text[:200]}\n\n🛑 TASK COMPLETE. STOP NOW. Report to user."
            
            # Neutral
            return f"✅ Executed\n\n{result_text[:150]}"
            
        except asyncio.TimeoutError:
            global_state.mark_failure("Timeout")
            return f"⏱️ TIMEOUT ({timeout}s)\n\n🛑 STOP. Do NOT retry."
        
        except Exception as e:
            error_msg = str(e)[:100]
            global_state.mark_failure(error_msg)
            return f"❌ ERROR: {error_msg}\n\n🛑 STOP. Do NOT retry."
    
    return verified_wrapper

# ============================================================================
# PARALLEL MCP LOADER
# ============================================================================
async def load_single_mcp(server_name, config, exit_stack, work_dir):
    """Load a single MCP server with proper error handling"""
    try:
        if server_name in ["word", "powerpoint", "pdf"]:
            script_path = os.path.abspath(config["args"][0])
            if not os.path.exists(script_path):
                print(f"[SKIP] {server_name}: Script not found")
                return server_name, []
            real_args = [script_path] + config["args"][1:]
        else:
            real_args = config["args"]
        
        env_to_use = config.get("env") or os.environ.copy()
        
        server_params = StdioServerParameters(
            command=config["command"], 
            args=real_args, 
            env=env_to_use
        )
        
        init_timeout = config.get("timeout", 15)
        
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        read, write = stdio_transport
        
        session = await exit_stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)
        
        result = await session.list_tools()
        langchain_tools = []
        
        for tool in result.tools:
            verified_func = create_verified_tool(session, tool, work_dir, server_name)
            
            lc_tool = StructuredTool.from_function(
                func=None, 
                coroutine=verified_func, 
                name=f"{server_name}_{tool.name}",
                description=f"[{server_name.upper()}] {tool.description}"
            )
            langchain_tools.append(lc_tool)
        
        print(f"[OK] {server_name}: {len(langchain_tools)} tools")
        return server_name, langchain_tools
    
    except Exception as e:
        print(f"[ERROR] {server_name}: {str(e)[:50]}")
        return server_name, []

async def load_all_mcp_parallel(exit_stack, work_dir):
    """Load all servers in parallel"""
    tasks = [
        load_single_mcp(name, cfg, exit_stack, work_dir)
        for name, cfg in MCP_CONFIG.items()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_tools = []
    status_lines = []
    
    for result in results:
        if isinstance(result, Exception):
            continue
        
        server_name, tools = result
        if tools:
            all_tools.extend(tools)
            status_lines.append(f"✅ **{server_name.upper()}**: {len(tools)} tools")
        else:
            status_lines.append(f"⚠️ **{server_name.upper()}**: Failed")
    
    return all_tools, status_lines

# ============================================================================
# SMART FILTERING
# ============================================================================
def filter_tools_smart(all_tools):
    """Filter only essential tools"""
    keywords = [
        'create', 'add', 'write', 'insert', 'read', 'get', 
        'table', 'paragraph', 'list', 'file', 'content',
        'move', 'copy', 'delete', 'pdf', 'extract'
    ]
    
    blacklist = ['pivot', 'macro', 'vba', 'advanced', 'complex']
    
    final = []
    for t in all_tools:
        name_lower = t.name.lower()
        
        if any(b in name_lower for b in blacklist):
            continue
        
        if any(k in name_lower for k in keywords):
            final.append(t)
    
    return final

# ============================================================================
# CONCISE SYSTEM PROMPT
# ============================================================================
def get_system_prompt(work_dir):
    return f"""You are MENTARI, an efficient AI assistant for Office automation and file management.

Working Directory: {work_dir}

CRITICAL RULES:
1. Call each tool ONLY ONCE
2. When you see "✅ SUCCESS" or "🛑" → STOP IMMEDIATELY
3. NEVER retry failed tools
4. Keep responses SHORT

Tools: filesystem_*, word_*, excel_*, powerpoint_*, pdf_*

Files: Uploaded files are in {work_dir}. Use just the filename.

Stop conditions:
- Tool returns success → Report to user → STOP
- Tool returns failure → Report error → STOP
- Tool blocked → Explain → STOP

Be concise and stop when done."""

# ============================================================================
# CHAINLIT HANDLERS
# ============================================================================
@cl.on_chat_start
async def start():
    """Initialize with parallel loading"""
    
    background_url = "http://localhost:8000/public/mentari(2).png"
    
    await cl.Message(
        content=f"""
<style>
    html, body {{ background: #0a0e27 url('{background_url}') center/cover fixed !important; }}
    body::before {{ content: ""; position: fixed; inset: 0; background: rgba(0,0,0,0.35); backdrop-filter: blur(8px); z-index: 0; }}
    #root {{ position: relative; z-index: 1; }}
    .user-message {{ background: rgba(59,130,246,0.9) !important; color: white !important; }}
    .assistant-message {{ background: rgba(255,255,255,0.9) !important; }}
</style>
""",
        author="System"
    ).send()
    
    global_state.reset()
    
    welcome = await cl.Message(
        content="""# 🌤️ MENTARI V.22

**Fixed Issues:**
✅ Proper streaming cleanup
✅ Hard stop after success
✅ Better tool limits
✅ Faster responses

Ready to help with Office tasks!
""",
        author="Mentari"
    ).send()
    
    loading = await cl.Message(
        content="🚀 **Loading servers...**",
        author="System"
    ).send()
    
    try:
        work_dir = USER_FILES_DIR
        exit_stack = AsyncExitStack()
        
        # Parallel loading
        all_tools, status_lines = await load_all_mcp_parallel(exit_stack, work_dir)
        
        if not all_tools:
            loading.content = "❌ **Failed to load servers**"
            await loading.update()
            return
        
        # Smart filter
        final_tools = filter_tools_smart(all_tools)
        
        # Setup LLM
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            loading.content = "❌ **OPENROUTER_API_KEY not found**"
            await loading.update()
            return
        
        llm = ChatOpenAI(
            model="mistralai/mistral-7b-instruct:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
            request_timeout=25  # Shorter timeout
        )
        
        agent = create_react_agent(llm, final_tools)
        
        memory = ChatHistoryManager(max_pairs=6)
        memory.set_system_prompt(get_system_prompt(work_dir))
        
        cl.user_session.set("agent", agent)
        cl.user_session.set("exit_stack", exit_stack)
        cl.user_session.set("work_dir", work_dir)
        cl.user_session.set("memory", memory)
        
        status_text = "\n".join(status_lines)
        
        loading.content = f"""## 🎉 Ready!

{status_text}

🔧 **Tools**: {len(final_tools)}
💾 **Memory**: 6 pairs

Upload files or ask for help! 👇
"""
        await loading.update()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        loading.content = f"❌ {str(e)[:150]}"
        await loading.update()

@cl.on_message
async def main(message: cl.Message):
    """Handle messages with hard stop enforcement"""
    
    agent = cl.user_session.get("agent")
    memory: ChatHistoryManager = cl.user_session.get("memory")
    work_dir = cl.user_session.get("work_dir")
    
    if not agent or not memory:
        await cl.Message(content="❌ Not ready. Refresh.", author="System").send()
        return
    
    global_state.reset()
    
    status = await cl.Message(content="🤔 **Processing...**", author="System").send()
    
    try:
        # Handle uploads
        uploaded_context = ""
        if message.elements:
            files = []
            for elem in message.elements:
                try:
                    dest = os.path.join(work_dir, elem.name)
                    
                    if hasattr(elem, "path") and elem.path and os.path.exists(elem.path):
                        shutil.copy(elem.path, dest)
                    elif hasattr(elem, "content") and elem.content:
                        with open(dest, "wb") as f:
                            f.write(elem.content)
                    elif hasattr(elem, "url") and elem.url:
                        urllib.request.urlretrieve(elem.url, dest)
                    
                    if os.path.exists(dest):
                        category = detect_file_category(elem.name)
                        emoji = {'image':'🖼️','office':'📊','pdf':'📄','document':'📝'}.get(category,'📎')
                        files.append(f"{emoji} {elem.name}")
                
                except Exception as e:
                    print(f"[FILE] {elem.name}: {e}")
            
            if files:
                uploaded_context = f"\n\nFiles uploaded: {', '.join(files)}"
        
        # Build message
        final_content = message.content + uploaded_context
        memory.add_message(HumanMessage(content=final_content))
        messages = memory.get_messages()
        input_data = {"messages": messages}
        
        # Execute with HARD LIMITS
        tool_count = 0
        MAX_TOOLS = 3  # STRICT LIMIT
        
        try:
            # Stream with early termination
            async for event in agent.astream(input_data, config={"recursion_limit": 5}):
                # Check stop flag
                if global_state.should_stop:
                    print(f"[HARD STOP] Stop flag triggered")
                    break
                
                for key, value in event.items():
                    if key == "tools":
                        tool_count += 1
                        
                        # ENFORCE HARD LIMIT
                        if tool_count >= MAX_TOOLS:
                            print(f"[HARD STOP] Tool limit: {tool_count}")
                            global_state.should_stop = True
                            break
                
                if global_state.should_stop:
                    break
        
        except Exception as e:
            print(f"[STREAM] {str(e)[:100]}")
        
        # Get final result
        result = await agent.ainvoke(input_data)
        ai_msgs = [m for m in result['messages'] if isinstance(m, AIMessage)]
        
        if ai_msgs:
            ai_response = ai_msgs[-1]
            memory.add_message(ai_response)
            response_text = ai_response.content
            
            await status.remove()
            
            # Detect files
            file_elements = []
            created = []
            
            for line in response_text.split('\n'):
                for ext in ['.docx', '.xlsx', '.pptx', '.txt', '.pdf']:
                    if ext in line:
                        for word in line.split():
                            clean = word.strip("'\",.!?[]()")
                            if clean.endswith(ext):
                                fname = os.path.basename(clean) if os.path.isabs(clean) else clean
                                fpath = os.path.join(work_dir, fname) if not os.path.isabs(clean) else clean
                                
                                if os.path.exists(fpath) and fname not in created:
                                    created.append(fname)
                                    file_elements.append(cl.File(name=fname, path=fpath, display="inline"))
            
            await cl.Message(
                content=response_text,
                author="Mentari",
                elements=file_elements if file_elements else None
            ).send()
        else:
            await status.remove()
            await cl.Message(content="✅ Done!", author="Mentari").send()
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        await status.remove()
        
        error = str(e)
        if "402" in error or "credits" in error.lower():
            await cl.Message(content="❌ **API credits exhausted**", author="System").send()
        elif "timeout" in error.lower():
            await cl.Message(content="⏱️ **Timeout - try simpler request**", author="System").send()
        else:
            await cl.Message(content=f"❌ {error[:150]}", author="System").send()

@cl.on_chat_end
async def end():
    """Safe cleanup"""
    exit_stack = cl.user_session.get("exit_stack")
    if exit_stack:
        try:
            await exit_stack.aclose()
        except Exception as e:
            # Suppress cleanup errors
            pass
    
    global_state.reset()

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("MENTARI V.22 PRO - FIXED STREAMING & HARD STOPS")
    print("=" * 70)
    print("Fixes:")
    print("  ✅ Async generator cleanup")
    print("  ✅ Hard stop enforcement")
    print("  ✅ Tool limit: 3 max")
    print("  ✅ Recursion: 5 max")
    print("  ✅ Timeouts: 12-45s")
    print("=" * 70)
    print("http://localhost:8000")
    print("=" * 70)