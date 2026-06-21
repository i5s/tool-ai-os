import sys, subprocess
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from cli.main import main

if __name__ == "__main__":
    main()
