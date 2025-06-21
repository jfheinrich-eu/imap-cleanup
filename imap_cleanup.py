import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from imap_cleanup.cli import main

if __name__ == "__main__":
    main()
