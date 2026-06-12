import sys
import subprocess
from pathlib import Path

# Simply delegate to the src.main module
if __name__ == "__main__":
    # Ensure project root is in path
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    
    from src.main import main
    main()
