"""Entry point for the ntsb-server console script.

This re-exports the FastAPI app and run_server from the internal app.server.main
module so that users only need the installable ntsb_api package.
"""

from app.server.main import app, get_app, run_server

__all__ = ["app", "get_app", "run_server"]
