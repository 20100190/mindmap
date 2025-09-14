your_project/
│
├── app/                        # Core application package
│   ├── main.py                 # ⬅️ FastAPI app entry point
│   ├── config.py               # Environment and settings
│   ├── api/                    # All route handlers (FastAPI routers)
│   │   ├── __init__.py         # Collects and includes all routers
│   │   ├── query.py            # /query endpoint
│   │   ├── health.py           # /health and /logs endpoints
│   │   └── logs.py             # /logs/status and /logs/cleanup
│   ├── core/                   # Core LLM logic
│   │   ├── agent.py            # LLMAgent class and related logic
│   │   ├── schema.py           # JSON schema for response validation
│   │   ├── prompts.py          # Prompt templates
│   │   └── tools.py            # Custom function tools (e.g., GoogleSearch)
│   ├── services/               # Optional service layers
│   │   └── mindmap.py          # Mindmap processing & depth logic
│   ├── log_management/         # Log rotation and cleanup tools
│   │   └── log_manager.py
│   └── utils/                  # Shared utilities (validators, formatters, etc.)
│       └── logger.py           # Logging setup
│
├── .env
├── requirements.txt
├── README.md