import sys
import os

# Add CampusFind to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CampusFind'))

# Import and run the app
from app import app

if __name__ == '__main__':
    app.run()
