import sys
from pathlib import Path

# Single source of truth for the `agents` package lives at frontend/agents/ so
# Vercel's Python function (frontend/api/chat.py) can import it directly without
# a hand-duplicated copy. Repo-root pytest needs frontend/ on sys.path to resolve
# the same `import agents...` statements the tests and the deployed function use.
sys.path.insert(0, str(Path(__file__).parent / "frontend"))
