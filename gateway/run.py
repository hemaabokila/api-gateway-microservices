from app import create_app
from dotenv import load_dotenv
import os


load_dotenv()

port = int(os.getenv("GATEWAY_PORT", 5000))
debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"

app = create_app()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
