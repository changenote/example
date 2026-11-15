"""Test pnpm and Bun releases only in disposable fixture copies."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from verify_examples import ROOT, command, snapshot


def read_only(binary, work, *args):
    before = snapshot(work)
    result = command([str(binary), *args], work)
    assert snapshot(work) == before, f"{args[0]} changed fixture files"
    return json.loads(result.stdout)


def verify(binary, tool):
    folder = ROOT / "examples/package-managers" / tool
    lock = "pnpm-lock.yaml" if tool == "pnpm" else "bun.lock"
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp) / "fixture"
        shutil.copytree(folder / "fixture", work)
        expected = json.loads((folder / "expected-status.json").read_text())
        assert read_only(binary, work, "status") == expected
        report = read_only(binary, work, "doctor")
        assert report["passed"], report
        assert any(
            check["name"] == f"tool:{tool}" and check["status"] == "pass"
            for check in report["checks"]
        )
        before = snapshot(work)
        result = command([str(binary), "version"], work)
        assert json.loads(result.stdout) == expected
        batch = json.loads((work / ".changenote/releases.json").read_text())
        assert batch == [
            {key: value for key, value in release.items() if key != "notes"}
            for release in expected
        ]
        for package in ("library", "app"):
            manifest_path = f"packages/{package}/package.json"
            manifest = work / manifest_path
            assert manifest.read_bytes() == before[manifest_path].replace(
                b'"1.2.3"', b'"1.3.0"', 1
            )
            entry = (manifest.parent / "CHANGELOG.md").read_text()
            assert "## 1.3.0\n" in entry
            if package == "library":
                assert "Add a sample API." in entry
            else:
                assert "Released with its fixed version group" in entry
        assert not (work / ".changenote/sample.md").exists()
        assert not list(work.rglob("lifecycle-ran"))
        assert not list(work.rglob("node_modules"))
        assert (work / lock).is_file()
        updated_lock = (work / lock).read_bytes()
        if tool == "pnpm":
            # pnpm records importers and dependency links, not package versions.
            assert updated_lock == before[lock]
        else:
            assert updated_lock.count(b'"version": "1.3.0"') == 2
        frozen = [
            tool,
            "install",
            "--lockfile-only",
            "--ignore-scripts",
            "--offline",
            "--frozen-lockfile",
        ]
        if tool == "pnpm":
            frozen.append("--ignore-pnpmfile")
        command(frozen, work)
        assert (work / lock).read_bytes() == updated_lock
        assert not list(work.rglob("lifecycle-ran"))
        assert not list(work.rglob("node_modules"))
        assert read_only(binary, work, "status") == []
        after = snapshot(work)
        assert json.loads(command([str(binary), "version"], work).stdout) == []
        assert snapshot(work) == after, "Empty release changed files"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, help="Compatible changenote executable")
    args = parser.parse_args()
    executable = shutil.which(args.cli)
    if executable is None:
        parser.error("CLI executable was not found")
    for tool in ("pnpm", "bun"):
        if shutil.which(tool) is None:
            parser.error(f"Required tool was not found: {tool}")
    binary = Path(executable).resolve()
    before = snapshot(ROOT)
    for tool in ("pnpm", "bun"):
        verify(binary, tool)
    assert snapshot(ROOT) == before, "Verifier changed the example repository"
    print(
        "Verified pnpm and Bun workspace releases and frozen/offline locks in temporary copies; source files are unchanged."
    )


if __name__ == "__main__":
    main()
