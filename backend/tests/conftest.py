import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ["DB_PATH"] = str(Path(_tmp) / "test.db")
os.environ["MEMORY_BACKEND"] = "local"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["BANK_PREFIX"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
