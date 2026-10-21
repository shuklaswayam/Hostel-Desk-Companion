import os
import sys
import urllib.parse

# Ensure project root is available on sys.path in Vercel Serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathFixMiddleware:
    """
    Vercel rewrites forward the original path via the __vercel_path query parameter.
    This middleware restores the original requested path into PATH_INFO and strips
    the helper parameter so Flask's URL routing and request.args function transparently.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        params = urllib.parse.parse_qs(qs)
        if "__vercel_path" in params:
            raw_path = params["__vercel_path"][0]
            unquoted = urllib.parse.unquote(raw_path).strip()
            if not unquoted or unquoted in ("/", "//"):
                environ["PATH_INFO"] = "/"
            else:
                environ["PATH_INFO"] = "/" + unquoted.lstrip("/")

            # Reconstruct clean QUERY_STRING without __vercel_path
            remaining_pairs = []
            for k, vs in params.items():
                if k != "__vercel_path":
                    for v in vs:
                        remaining_pairs.append(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(v)}")
            environ["QUERY_STRING"] = "&".join(remaining_pairs)
        elif environ.get("PATH_INFO") in ("/api/index.py", "/api/index"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
application = app
