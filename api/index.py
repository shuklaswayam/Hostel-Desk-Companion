import os
import sys

# Ensure project root is available on sys.path in Vercel Serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathFixMiddleware:
    """
    Vercel serverless rewrites route requests to /api/index (or /api/index.py).
    This middleware restores the original requested URI from HTTP_X_MATCHED_PATH
    or HTTP_X_FORWARDED_URI so that Flask routes match correctly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_ORIGINAL_URL")
        )
        if matched_path:
            # If query params are attached to matched_path, split them cleanly
            if "?" in matched_path:
                path_part, query_part = matched_path.split("?", 1)
                environ["PATH_INFO"] = path_part
                if not environ.get("QUERY_STRING"):
                    environ["QUERY_STRING"] = query_part
            else:
                environ["PATH_INFO"] = matched_path
        elif environ.get("PATH_INFO") in ("/api/index.py", "/api/index", "/api", "/api/"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
application = app
