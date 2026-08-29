"""
pytest conftest — adds the backend root to sys.path so imports like
`from agents.graph_agent.service import ...` resolve correctly.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
