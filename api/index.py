import os
import sys

# Ensure project root is available on sys.path in Vercel Serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path_debug = {k: v for k, v in environ.items() if any(term in k.upper() for term in ("PATH", "URI", "URL", "ROUTE", "MATCH"))}
        print(f"[VERCEL ROUTING DEBUG] Original PATH_INFO={environ.get('PATH_INFO')}, Keys: {path_debug}")

        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_ORIGINAL_URL")
            or environ.get("RAW_URI")
        )
        if matched_path and matched_path != "/api/index":
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
