"""Stable CLI entry point; can be invoked from any working directory."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from ziwei_kb.cli import main
if __name__=='__main__':raise SystemExit(main())
