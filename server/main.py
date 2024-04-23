import uvicorn
from threading import Thread
import asyncio
import os
from helper import Helper
from rest import app as rest_api
from cloudlink import CloudlinkServer

cl = CloudlinkServer()
helper = Helper(cl)
rest_api.cl = cl
rest_api.helper = helper

async def main():
    rest_api.db.connect()  # Await the connection
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