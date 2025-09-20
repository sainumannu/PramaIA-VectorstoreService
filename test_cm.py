"""
Simple module test
"""
import os
import sys

# Add current directory to path for relative imports
sys.path.insert(0, os.path.abspath('.'))

try:
    # Import chroma_manager directly
    print("Importing chroma_manager...")
    import app.core.chroma_manager as cm
    print("Module imported.")
    
    # Check if ChromaManager exists
    print(f"Module dir: {dir(cm)}")
    print(f"Has ChromaManager: {'ChromaManager' in dir(cm)}")
    print(f"Type of ChromaManager: {type(getattr(cm, 'ChromaManager', None))}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
