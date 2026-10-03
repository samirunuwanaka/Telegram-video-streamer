"""
PC Command Execution Handler
"""

import sys
import uvicorn
from pc.config_pc import HOST, PORT


def run_pc_server():
    """
    Launches Uvicorn server hosting the PC API.
    """
    print(f"🖥️ Launching PC API Server on http://{HOST}:{PORT}...")
    uvicorn.run("pc.api_server:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    run_pc_server()
