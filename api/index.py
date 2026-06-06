"""Vercel serverless entry point."""
import os
os.environ["VERCEL"] = "1"

import requests

def app(environ, start_response):
    start_response("200 OK", [("Content-Type", "application/json")])
    return [f'{{"status":"ok","requests":"{requests.__version__}"}}'.encode()]
