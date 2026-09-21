"""
MCP (Model context protocol) is open protocal is designed to standardize how applications provide context to the LLM. 
Think the MCP like a USB-C port for AI applications just as USB-C provide a standandized way connect devices to various peripheral, MCl provides a stardardized way to connect AI model to 
different data source and tools.


Why MCP matters for AI agent

1. Tradditional of AI model connect with external resoueces oftent involve custom interaction for each data source ot tool. This Lead to:
    + Integration complexity: Each new data source require unique implementation
    + Scalability Issures: Add a new tools progressive harder.
    + Maintenance Overhead: updata to one integration may break other
2. MCP slove this challenge by providing a standandized that enables:
    + Unified Access: A single interface for multiple data source and tools.
    + Plus and play extention: easy addition a new capabilities.
    + Stateful Communication: Real-time, two way communication between Ai resources
    + Dynamic dicovery: AI can find and use new tool on the fly

    
Implement:
1. Build MCP and use it: build a MCP server with customizes tools and connect to Claude Desktio
2. Customize Tool-Enable Agent: Create an customized agent that can use external via MCP


MCP follow a clien-serve architecture with three main components:
+ Host: The AI application(like Clause Desktop, Cursor or a cutimized agent) That needs access to external resourses.
+ Cliens: Connectors that maintain with theit servers.
+ Serves Lightweight program that expose capability (data, tools, promtp) via the MCP protocol
+ Data Source: Both local(file, database) and remote services(APIs) that MCP servers can access



Understanding architechture 
This Script will build our own MCP Host and client. 
Connect to claude-desktop we can create the agent can:
1. ACT at an MCP Host.
2. Dicover available tools from our MCp server
3. Understand when to use which tool based on user queries
4. Execute tools with appropriate parameters
5. Process tool results to provide helpful response

This architecture follows a pattern common in modern AI systems:

+ Discovery Phase: Our custom host discovers what tools are available
+ Planning Phase: The agent decides which tool to use based on the user's query
+ Execution Phase: Our client connects to the server and executes the selected tool
+ Interpretation Phase: The agent explains the results in natural language
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from typing import Any, List, Dict
# MCP libraries for connecting to server
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Anthropic API for Claude
from anthropic import Anthropic

load_dotenv()

# Path to your MCP server
client = Anthropic()

mcp_server_path = "scripts/mcp_servers.py"
print("Setup complete!")




"""
Tool discover to build MCP host

Function act as our host's discovery component:
1. Create Sercer Parameter: configures how to launch and connect to MCP server
2. Estabalishes Connection: User stdio_client to create communication channel
3. Initialize Session: Set up the MCP session using communication channel
4. Discovers Tools: call list_tools() to get all available tools
5. Format results: Convert tool into a more urable format for our agent
"""

async def discover_tools():
    """
    Connect to the MCP server and discover available tools
    Run information about available tools
    """
    # ANSI color code for better log visibility
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RESET = "\033[0m"
    SEP = "=" * 40

    # create server parameter to connecting to your MCP server throught Stdio
    server_params = StdioServerParameters(
        command= 'python', #comman to run server
        args = [mcp_server_path] # path to your MCP server script
    )

    #connect to to server via stdio 
    async with stdio_client(server_params) as (read, write):
        # create a client session
        async with ClientSession(read, write) as session:
            # initialize connection
            print(f"{BLUE}📡 Initializing MCP connection...{RESET}")
            await session.initialize()

            # List tools available
            print(f"{BLUE}🔎 Discovering available tools...{RESET}")
            tools = await session.list_tools()

            # format list tools information for easier viewing
            tool_info = []
            for tool_type, tool_list in tools:
                if tool_type == "tools":
                    for tool in tool_list:
                        tool_info.append({
                            "name": tool.name, 
                            "description": tool.description,
                            "schema": tool.inputSchema}
                        )
            print(f"{GREEN}✅ Successfully discovered {len(tool_info)} tools{RESET}")
            print(f"{SEP}")
            return tool_info

"""
Tool execution: Implementing our MCP client


This function from the core of our MCP client:
1. Connect to Server:  Similar to our discovery function, it establishes a connection to the MCP server 
2, Exection tool: Calls the specified tool with the provided arguments
3. return results: Gives back whatever the tool returns


Notice that for each tool execution, we create a new connection to the MCP server. While this may seem inefficient, 
it ensures clean separation between tool calls and avoids potential state issues. This stateless approach simplifies our implementation and makes it more robust.
In a production system, you might optimize this by maintaining a persistent connection, 
but the current approach is excellent for educational purposes as it clearly separates each step in the process.
"""
async def execute_tool(tool_name: str, arguments : dict[str: Any]):
    """
    Execute specific tool to provided by MCP server
    ARGs:
    tool_name: the name of a tool to execute
    arguments: a dictionatu of argument to pass to the tool
    returns:
        the result from excuting from the tool
    """
    # ANSI color codes for better log visibility
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    SEP = "-" * 40

    server_params = StdioServerParameters(
        command = "python",
        args = [mcp_server_path]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call the specific tool with the provided arguments
            print(f"{BLUE}📡 Sending request to MCP server...{RESET}")
            result = await session.call_tool(tool_name, arguments)
            
            print(f"{GREEN}✅ Tool execution complete{RESET}")
            
            # Format result preview for cleaner output
            result_preview = str(result)
            if len(result_preview) > 150:
                result_preview = result_preview[:147] + "..."
                
            print(f"{BLUE}📊 Result: {result_preview}{RESET}")
            print(f"{SEP}")
            
            return result


"""
Integating AI with our MCP implemantation

This function complete our custom MCP host Implementation with sophisticated reasoning   and execution for: 
1. Tools Description: We format the tool information in a way can help claude understand
2. System prompt: We provide instructions on when and how to use tool
3. Response Analysis: Look for the Json tools request in Claude's response
4. Tool Execution: If tool request is detected, we use  client to execute the appropriate tool
5. Result processing: send result back to claude for interpretation
6. Conversation Management: Maintain context by tracking messages


Claude provide the reasoning and communication skills, 
while MCP tools provide specialized capabilities and real-time data access.

"""

async def query_claude(prompt: str, tool_info: List[Dict], previous_messages=None):
    """
    Send a query to Claude and process the response.
    
    Args:
        prompt: User's query
        tool_info: Information about available tools
        previous_messages: Previous messages for maintaining context
        
    Returns:
        Claude's response, potentially after executing tools
    """
    # ANSI color codes for better log visibility
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    PURPLE = "\033[95m"
    RESET = "\033[0m"
    SEP = "=" * 40
    
    if previous_messages is None:
        previous_messages = []
    
    print(f"{PURPLE}{SEP}")
    print("🧠 REASONING PHASE: Processing query with Claude")
    print(f"🔤 Query: \"{prompt}\"")
    print(f"{SEP}{RESET}")
    
    # Format tool information for Claude
    tool_descriptions = "\n\n".join([
        f"Tool: {tool['name']}\nDescription: {tool['description']}\nSchema: {json.dumps(tool['schema'], indent=2)}"
        for tool in tool_info
    ])
    
    # Build the system prompt
    system_prompt = f"""You are an AI assistant with access to specialized tools through MCP (Model Context Protocol).
    
Available tools:
{tool_descriptions}

When you need to use a tool, respond with a JSON object in the following format:
{{
    "tool": "tool_name",
    "arguments": {{
        "arg1": "value1",
        "arg2": "value2"
    }}
}}

Do not include any other text when using a tool, just the JSON object.
For regular responses, simply respond normally.
"""
    
    # Filter out system messages from previous messages
    filtered_messages = [msg for msg in previous_messages if msg["role"] != "system"]
    
    # Build the messages for the conversation (WITHOUT system message)
    messages = filtered_messages.copy()
    
    # Add the current user query
    messages.append({"role": "user", "content": prompt})
    
    print(f"{BLUE}📡 Sending request to Claude API...{RESET}")
    
    # Send the request to Claude with system as a top-level parameter
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_prompt,  # System prompt as a separate parameter
        messages=messages      # Only user and assistant messages
    )
    
    # Get Claude's response
    claude_response = response.content[0].text
    print(f"{GREEN}✅ Received response from Claude{RESET}")
    
    # Try to extract and parse JSON from the response
    try:
        # Look for JSON pattern in the response
        import re
        json_match = re.search(r'(\{[\s\S]*\})', claude_response)
        
        if json_match:
            json_str = json_match.group(1)
            # print(f"{YELLOW}🔍 Tool usage detected in response{RESET}")
            print(f"{BLUE}📦 Extracted JSON: {json_str}{RESET}")
            
            tool_request = json.loads(json_str)
            
            if "tool" in tool_request and "arguments" in tool_request:
                tool_name = tool_request["tool"]
                arguments = tool_request["arguments"]
                
                print(f"{YELLOW}🔧 Claude wants to use tool: {tool_name}{RESET}")
                
                # Execute the tool using our MCP client
                tool_result = await execute_tool(tool_name, arguments)
                
                # Convert tool result to string if needed
                if not isinstance(tool_result, str):
                    tool_result = str(tool_result)
                
                # Update messages with the tool request and result
                messages.append({"role": "assistant", "content": claude_response})
                messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
                
                # print(f"{PURPLE}🔄 Getting Claude's interpretation of the tool result...{RESET}")
                
                # Get Claude's interpretation of the tool result
                final_response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=messages
                )
                
                print(f"{GREEN}✅ Final response ready{RESET}")
                print(f"{SEP}")
                
                return final_response.content[0].text, messages
        
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"{YELLOW}⚠️ No tool usage detected in response: {str(e)}{RESET}")
    
    print(f"{GREEN}✅ Response ready{RESET}")
    print(f"{SEP}")
    
    return claude_response, messages

print("Claude query function defined")


"""
========================
process direct tool with clien
"""
async def test_direct_client():
    tools = await discover_tools()
    # print(f"Discovered {len(tools)} tools")
    # for i, tool in enumerate(tools):
    #     print(f"{i}. {tool['name']}: {tool['description']}")
    # Run a single query using the tools from your MCP server
    query = "What is the current price of Bitcoin?"
    print(f"Sending query: {query}")

    response, messages = await query_claude(query, tools)
    print(f"\nAssistant's response:\n{response}")

    # response, messages = await query_claude(query, tools)
    try: 
        if tools:
            first_tool = tools[0]
            tool_name = first_tool["name"]

            # Use the correct parameter name for get_crypto_price
            arguments = {"crypto_id": "bitcoin"}
            
            print(f"Executing tool '{tool_name}' with arguments: {arguments}")
            result = await execute_tool(tool_name, arguments)
            print(f"Tool result :{result}")
        else:
            print("No tools discovered to test")
    except Exception as e:
        print(f"Error executing tool: {str(e)}")



"""
============================
Interactive MCP host with interface
============================ 
"""

async def chat_session():
    
    """
    Run interactive chat session with AI agent
    """
    tools = await discover_tools()
    # ANSI color codes for better log visibility
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    SEP = "=" * 50


    # make sure tool is defined from a previous cell, or dicover them  again
    try:
        # Check if tools is defined and not empty
        if 'tools' not in globals() or not tools:
            print(f"{BLUE}🔍 No tools found, discovering available tools...{RESET}")
            tools_local = await discover_tools()
        else:
            tools_local = tools

        for i, tool in enumerate(tools_local):
            print(f"{YELLOW}  {i}. {tool['name']}{RESET}")
            print(f"     {tool['description'].strip()}")

        print(f"💬 INTERACTIVE CHAT SESSION") 

        print(f"Type 'exit' or 'quit' to end the session{RESET}")


        messages = []
        while True:
            user_input = input(f"\n{BOLD}You:{RESET} ")

            # check if user want to exit
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n{GREEN}Ending chat session. Goodbye!{RESET}")
                break

            print(f"\n{BLUE}Processing...{RESET}")
            response, messages = await query_claude(user_input, tools_local, messages)

            # Display Claude's response
            print(f"\n{BOLD}Assistant:{RESET} {response}")
            
    except Exception as e:
        print(f"\n{YELLOW}⚠️ An error occurred: {str(e)}{RESET}")
if __name__ == "__main__":  
    # asyncio.run(check_tool())
    # print("hello")
    # asyncio.run(test_direct_client())
    
    asyncio.run(chat_session())

