import shutil
from pathlib import Path

import pytest

FIXTURES_PATH = (Path(__file__).parent / "fixtures").absolute()
TEST_STORE_PATH = Path(".test-store")


@pytest.fixture(scope="module")
def fixtures_path():
    return FIXTURES_PATH


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_store():
    if TEST_STORE_PATH.exists():
        shutil.rmtree(TEST_STORE_PATH)
    yield
    if TEST_STORE_PATH.exists():
        shutil.rmtree(TEST_STORE_PATH)
