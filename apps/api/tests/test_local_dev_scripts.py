import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_demo_flow_smoke_script_exists_and_is_portable():
    script = ROOT / "scripts" / "smoke-demo-flow.sh"

    assert script.exists()
    assert "jq" not in script.read_text()

    result = subprocess.run(
        ["bash", "-n", str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
