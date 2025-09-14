from dotenv import load_dotenv
import os
import gunicorn
load_dotenv(dotenv_path="/Users/usman/Downloads/0.DataScience/portfolio/mindmap/.env")


from fastapi import FastAPI
from api import query
from logs_management import log_manager
import logging

log_manager.setup_logging()


app = FastAPI()

app.include_router(query.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8001))
    # for development, use reload=True
    uvicorn.run(app, host="0.0.0.0", port=port)
    # for production
    # gunicorn.run(app, 
    #              host="0.0.0.0",  # bind to all interfaces
    #              port=port, 
    #              workers=4,  # independent of CPU cores
    #              timeout=120,  # if a request takes longer than this, it will be terminated
    #              threads=4,  # for handling multiple requests concurrently no parallelism
    #              worker_class="uvicorn.workers.UvicornWorker")
