#!/usr/bin/env python3
import uvicorn
import os
import sys
import multiprocessing

def run_server():
    """Run the FastAPI server with proper configuration"""
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    # Use the module-based path for uvicorn with proper reload configuration
    uvicorn.run(
        "backend.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True, 
        reload_dirs=["backend"],
        # Fix multiprocessing issues on macOS
        workers=1,
        # Use threading instead of multiprocessing for reload
        use_colors=True,
        access_log=True
    )

if __name__ == "__main__":
    # Protect the entry point for multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    run_server()