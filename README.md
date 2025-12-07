# Mentari-The-AI-Agent-Orchestration

![Screenshot](public/Screenshot%202025-12-07%20180632.png)

Mentari is an AI-powered automation assistant designed to orchestrate multiple productivity tools through isolated processes. It integrates document automation, file handling, and controlled web interactions under one unified system.

## Please clone the MCP server you’ve chosen into your Environtment
### MCP Servers Used

- [Office Word MCP Server](https://github.com/GongRzhe/Office-Word-MCP-Server.git)
- [Excel MCP Server](https://github.com/haris-musa/excel-mcp-server.git)
- [Office PowerPoint MCP Server](https://github.com/GongRzhe/Office-PowerPoint-MCP-Server.git)
- [Filesystem MCP Server](https://github.com/modelcontextprotocol/servers.git)

🛠️ Capabilities
📝 Microsoft Word

Create and edit .docx files

Add headings, tables, and structured content

Apply formatting and modify document structure

📊 Microsoft Excel

Create and update workbook files

Perform data analysis

Read/write cells using Pandas or OpenPyXL

📄 PDF & Filesystem

Extract text from PDF files

List, move, and rename files in a secure sandbox

Support for structured file workflows

🌐 Social Media & Web Automation

Automated messaging and file upload

Supports WhatsApp Web and Discord

Powered by Selenium (requires Chrome Debug Mode)

| Component        | Role in the System                        |
|------------------|--------------------------------------------|
| Language         | Python 3.11+                               |
| Orchestration    | LangGraph / LangChain                      |
| Protocol         | Model Context Protocol (MCP)               |
| Inference        | OpenRouter (Grok / Gemini)                 |
| UI / Frontend    | Chainlit                                   |
| Automation       | Selenium / Playwright                      |

⚠️ Important Usage Notes

This system is a development prototype and should not be used in production without:

- Complete security auditing

- Validation of automation behavior

- Proper sandboxing and permission control

Chrome must be run in Remote Debug Mode for automation features to function correctly.
