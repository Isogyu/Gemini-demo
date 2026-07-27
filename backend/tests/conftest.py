import os
import tempfile

os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(tempfile.mkdtemp(prefix='tax-sim-test-'), 'test.db')}",
)
