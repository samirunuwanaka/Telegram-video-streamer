"""
PC Application Entry Point
Starts PC Receiver Engine and REST/MJPEG API Server.
"""

from pc.pc_commands import run_pc_server

def main():
    """
    Main entry point for PC side.
    """
    run_pc_server()

if __name__ == "__main__":
    main()
