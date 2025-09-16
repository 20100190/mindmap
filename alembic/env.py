from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import load_dotenv

# ✅ Load .env (must be near top)
load_dotenv()

# ✅ Build full sync DB URL (psycopg2 for Alembic)
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# ✅ Set the DB URL dynamically (overrides alembic.ini)
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# ✅ Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ Import your models + Base
from db.models import QueryLog  # 👈 your model
from db.session import Base     # 👈 your declarative_base()

target_metadata = Base.metadata  # 👈 tells Alembic what to look at

# ✅ Offline mode
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # 👈 optional: detects column type changes
    )

    with context.begin_transaction():
        context.run_migrations()

# ✅ Online mode
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# ✅ Trigger
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()