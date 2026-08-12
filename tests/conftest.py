import sys
import os

# Add the project root to sys.path so that `from src.heatshield import ...` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
