#!/usr/bin/env python3
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add the project root to the Python path
    # This allows running the script from anywhere and ensures 'backend' is a package
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    # Use the module-based path for uvicorn
    # This tells uvicorn to treat 'backend' as a package and 'main' as a module within it.
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["backend"])