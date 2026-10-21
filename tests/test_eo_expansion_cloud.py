import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "expansion_cloud", ROOT / "infrastructure/eo_expansion/cloud_worker.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_seed_refresh_is_idempotent_and_updates_existing_inventory():
    import sys
    import threading
    import types
    from types import SimpleNamespace

    # The refresh's SDK exception import is isolated; no network or credential.
    class NotFound(Exception):
        pass

    fake = types.ModuleType("azure.core.exceptions")
    fake.ResourceNotFoundError = NotFound
    previous = sys.modules.get("azure.core.exceptions")
    sys.modules["azure.core.exceptions"] = fake
    try:

        class Container:
            def get_blob_client(self, name):
                return SimpleNamespace(
                    get_blob_properties=lambda: SimpleNamespace(size=7, metadata={"sha256": "x"})
                )

        archive = SimpleNamespace(
            index={},
            used=0,
            lock=threading.Lock(),
            container=Container(),
            name=lambda p: "expansion-v1/" + p,
        )
        M.refresh_pair(archive, "images/a.tif")
        assert archive.used == 14 and len(archive.index) == 2
        M.refresh_pair(archive, "images/a.tif")
        assert archive.used == 14
    finally:
        if previous is None:
            sys.modules.pop("azure.core.exceptions", None)
        else:
            sys.modules["azure.core.exceptions"] = previous
