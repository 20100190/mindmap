mindmap/
├── main.py                         # ✅ FastAPI app entrypoint (includes routers)
│
├── config.py                       # ✅ Load .env, manage typed settings via `settings`
│
├── api/                            # ✅ Public/private HTTP routes (FastAPI routers)
│   ├── __init__.py
│   ├── query.py                    # POST /query endpoint
│   └── logs.py                     # Logs or admin endpoints (may be private)
│
├── services/                       # ✅ Business logic layer (calls orchestrator, db, GCS)
│   ├── __init__.py
│   └── query_service.py            # High-level logic for handling /query flow
│
├── llm/                            # ✅ Handles LLM orchestration and calling
│   ├── __init__.py
│   ├── client.py                   # Raw OpenAI or Gemini API call
│   ├── orchestrator.py             # Retry loop, validation, schema enforcement
│   ├── prompts.py                  # System prompt builders
│   ├── schema.py                   # Expected LLM output schema (for JSON validation)
│   └── tools.py                    # LLM tools (function calling support)
│
├── db/                             # ✅ All database models and sessions
│   ├── __init__.py
│   ├── models.py                   # SQLAlchemy ORM models
│   └── session.py                  # DB engine setup, sessionmaker, get_db()
│
├── alembic/                        # ✅ Alembic migrations
│   ├── env.py                      # Migration DB logic
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       └── xxxx_create_query_logs_table.py
│
├── util/                           # ✅ Pure utilities (GCS upload, depth calc, etc.)
│   ├── __init__.py
│   ├── gcs_util.py                 # Upload JSON files to Cloud Storage
│   └── process_json_mindmap.py    # Mindmap processing, depth calculation
│
├── logs/                           # ✅ Logs directory (used by logging setup)
│   └── app.log
│
├── logs_management/                # ✅ Optional: logging cleanup, rotation
│   ├── __init__.py
│   └── log_manager.py
│
├── secrets/                        # 🔒 Service account keys (in `.gitignore`)
│   └── service-account.json
│
├── requirements.txt
├── cloudbuild.yaml                 # ✅ Cloud Build config (if using GCP)
├── alembic.ini                     # ✅ Alembic DB settings
└── README.md