"""
E2E test fixtures for Playwright testing.
"""
import pytest
import subprocess
import time
import requests
from pathlib import Path


STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"


def wait_for_streamlit(url: str, timeout: int = 30) -> bool:
    """Wait for Streamlit server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)  # Always sleep to avoid busy loop
    return False


@pytest.fixture(scope="session")
def streamlit_server():
    """Start Streamlit server for E2E tests."""
    # Get the app.py path
    app_path = Path(__file__).parent.parent.parent / "app.py"

    # Start Streamlit subprocess (don't capture pipes to avoid deadlock)
    process = subprocess.Popen(
        ["streamlit", "run", str(app_path), "--server.port", str(STREAMLIT_PORT)]
    )

    # Wait for server to be ready
    if not wait_for_streamlit(STREAMLIT_URL):
        process.kill()
        process.wait()
        pytest.fail("Streamlit server failed to start")

    yield STREAMLIT_URL

    # Cleanup with graceful shutdown
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
