# MindMap
---

A FastAPI-based app that handles LLM-powered mindmap generation, database logging, and GCS integration. 
This repo includes modular services, clean architecture, and Docker support for easy deployment.

## Features
- REST API built with FastAPI
- Modular: API, services, LLM orchestration, DB, and logging layers
- Docker support for containerized deployment
- LLM orchestration with schema validation
- SQLAlchemy ORM + Alembic for DB migrations
- GCS integration for file uploads
- Cloud-ready (Cloud Run, Cloud Build support)
- Using [jsmindmao](https://github.com/hizzgdev/jsmind) render mindmap. 
---

## Requirements
- Docker (Recommended)
- Python 3.10+ (for non-Docker users)
- A `.env` file with all required environment variables (see `.env.template`)
---

## Quickstart (with Docker)
```
# 1. Clone the repo
git clone https://github.com/20100190/mindmap
cd mindmap

# 2. Copy and configure the environment file
cp .env.template .env
# Now edit `.env` and fill in your secrets and config

# 3. Build and run the Docker container
docker compose up -d

# 4. This app uses ssl certificate you might want to generate your own or skip by changing
`nginx.conf`

File structure
mindmap/
├── .dockerignore
├── .env.template
├── .gitignore
├── Dockerfile
├── README.md
├── alembic/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 01e22a9cf936_adding_chat_log.py
│       ├── 9884d162d6a5_add_update_col.py
│       └── b1822018177d_create_query_logs_table.py
├── alembic.ini
├── api/
│   ├── dependencies.py
│   └── v1/
│       ├── __init__.py
│       ├── chat.py
│       ├── health.py
│       └── query.py
├── chat_log_cache/
│   ├── __init__.py
│   └── chat_log.py
├── cloudbuild.yaml
├── config.py*
├── correlation_context.py
├── db/
│   ├── __init__.py
│   ├── models.py
│   └── session.py
├── docker-compose.yml*
├── llm/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── orchestrator.py
│   ├── prompts.py
│   ├── schema.py
│   └── tools.py
├── logs_management/
│   ├── __init__.py
│   ├── log_manager.py
│   └── log_manager1.py
├── main.py
├── nginx.conf*
├── requirements.txt
├── services/
│   ├── __init__.py
│   └── query_service.py
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── script.js
├── templates/
│   ├── chat.html
│   ├── chat1.html
│   └── chat2.html
├── tree.txt
└── util/
    ├── __init__.py
    ├── gcs_util.py
    └── process_json_mindmap.py
```
