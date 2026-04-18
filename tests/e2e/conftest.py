"""
E2E test fixtures for Playwright testing.
"""
import subprocess
import time
from pathlib import Path

import pytest
import requests

try:
    from playwright.sync_api import sync_playwright, Page
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False


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
        time.sleep(1)
    return False


@pytest.fixture(scope='session')
def streamlit_server():
    """Start Streamlit server for E2E tests."""
    app_path = Path(__file__).parent.parent.parent / 'app.py'

    process = subprocess.Popen(
        ['streamlit', 'run', str(app_path), '--server.port', str(STREAMLIT_PORT),
         '--server.headless', 'true']
    )

    if not wait_for_streamlit(STREAMLIT_URL):
        process.kill()
        process.wait()
        pytest.fail('Streamlit server failed to start')

    yield STREAMLIT_URL

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope='session')
def playwright_instance():
    if not _PLAYWRIGHT_AVAILABLE:
        pytest.skip('playwright not installed')
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope='session')
def browser(playwright_instance):
    b = playwright_instance.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture
def browser_page(browser, streamlit_server):
    """Playwright Page pre-navigated to the running Streamlit app."""
    page = browser.new_page()
    page.goto(streamlit_server, wait_until='networkidle')
    yield page
    page.close()
