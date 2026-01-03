from pathlib import Path

root = Path(__file__).resolve().parent
file_path = root / "_docs" / "dummytext.txt"

print(file_path.stem)