import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


CALC_API_DIR = Path(__file__).resolve().parents[1]


def run_settings_subprocess(script, calc_env):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("CALC_")
    }
    env.update(calc_env)
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=CALC_API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("calc_env", "missing_name"),
    [
        ({"CALC_ALLOWED_HOSTS": "example.test"}, "CALC_SECRET_KEY"),
        ({"CALC_SECRET_KEY": "subprocess-test-secret"}, "CALC_ALLOWED_HOSTS"),
    ],
)
def test_production_settings_fail_closed(calc_env, missing_name):
    result = run_settings_subprocess(
        """
from django.core.exceptions import ImproperlyConfigured

try:
    import calcapi.settings
except ImproperlyConfigured as exc:
    print(exc)
else:
    raise SystemExit("settings loaded without required production values")
""",
        {"CALC_DEBUG": "0", **calc_env},
    )

    assert result.returncode == 0
    assert missing_name in result.stdout


def test_allowed_hosts_ignore_empty_entries():
    result = run_settings_subprocess(
        """
import json
import calcapi.settings as module

print(json.dumps(module.ALLOWED_HOSTS))
""",
        {
            "CALC_DEBUG": "0",
            "CALC_SECRET_KEY": "subprocess-test-secret",
            "CALC_ALLOWED_HOSTS": " example.test, api.example.test,,",
        },
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == ["example.test", "api.example.test"]
