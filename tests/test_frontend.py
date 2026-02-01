import subprocess
import sys
import time
import pytest
import httpx

from playwright.sync_api import Page

SERVER_URL = "http://127.0.0.1:8000"


def server_is_up(url=SERVER_URL + "/activities"):
    try:
        r = httpx.get(url, timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def server():
    """Ensure the FastAPI server is running for E2E tests. Start it if needed."""
    started_by_fixture = False
    if not server_is_up():
        # Start uvicorn in background
        proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.app:app", "--port", "8000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started_by_fixture = True
        # wait until server responds
        for _ in range(40):
            if server_is_up():
                break
            time.sleep(0.25)
        else:
            proc.kill()
            pytest.fail("Could not start uvicorn for E2E tests")

    yield

    # Teardown only if we started it
    if started_by_fixture:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def test_signup_adds_participant(page: Page):
    url = SERVER_URL + "/"
    page.goto(url)

    # Wait for UI to load
    page.wait_for_selector("#activities-list")

    email = "e2e_test@example.com"

    # Ensure not already present
    assert page.locator(f'text={email}').count() == 0

    # Fill form and submit
    page.fill("#email", email)
    page.select_option("#activity", value="Basketball Team")
    page.click("button[type=submit]")

    # Wait for the participant to appear in the UI without refresh
    page.wait_for_selector(f'text={email}', timeout=5000)

    assert page.locator(f'text={email}').count() >= 1
