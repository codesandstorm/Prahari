from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ml.provisional_research import run


if __name__ == "__main__":
    result = run(ROOT)
    print(result)
