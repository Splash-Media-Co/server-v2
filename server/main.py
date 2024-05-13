import uvicorn
from threading import Thread
import asyncio
import os
from helper import Helper
from rest import app as rest_api
from cloudlink import CloudlinkServer
from clcommands import SplashCommands
from security import background_tasks
from database import db
from dotenv import load_dotenv

load_dotenv()

# Inicialize CloudLink server
cl = CloudlinkServer()
cl.remove_command("setid")
cl.remove_command("gmsg")
cl.remove_command("gvar")
cl.set_motd("Splash Media Server")
cl.set_real_ip_header(os.getenv("REAL_IP_HEADER"))

helper = Helper(cl)

# Start commands

SplashCommands(cl, helper)

rest_api.cl = cl
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

    # Start Cloudlink server
    await rest_api.cl.run(host=os.getenv("CL_HOST", "0.0.0.0"), port=int(os.getenv("CL_PORT", 3000)))

if __name__ == "__main__":
    asyncio.run(main())