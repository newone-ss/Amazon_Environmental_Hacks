"""
Bhujal backend package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Backward compatibility module aliases
try:
    from backend import agent, scoring

    sys.modules.setdefault("agent", agent)
    sys.modules.setdefault("scoring", scoring)
except ImportError:
    pass
