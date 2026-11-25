import sys
from pathlib import Path

# Add project root to sys.path so modules like analyzer and app are discoverable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mangum import Mangum
from app import app

# Mangum serverless ASGI handler for Netlify / AWS Lambda
handler = Mangum(app, lifespan="off")
