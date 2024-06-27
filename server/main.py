import uvicorn
from threading import Thread
import asyncio
import os
from helper import Helper
from rest import app as rest_api
from security import background_tasks
from database import db
from dotenv import load_dotenv
from oceanlink import OceanLinkServer
from splashclasses import SplashCommands


load_dotenv()

# Inicialize OceanLink server
ol = OceanLinkServer()
ol.set_message("Splash Media Server")
ol.set_true_ip_header(os.getenv("REAL_IP_HEADER"))

helper = Helper(ol)

# Start commands
SplashCommands(ol, helper)

rest_api.ol = ol
rest_api.helper = helper

Thread(target=background_tasks, daemon=True).start()

async def main():
    db.connect() # Connect the db!
    # Start API server
    Thread(target=uvicorn.run, args=(rest_api,), kwargs={
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", 3001)),
        "root_path": os.getenv("API_ROOT", ""),
    }, daemon=True).start()

    # Start Oceanlink server
    await rest_api.ol.run(host=os.getenv("OL_HOST", "0.0.0.0"), port=int(os.getenv("OL_PORT", 3000)))

if __name__ == "__main__":
    asyncio.run(main())