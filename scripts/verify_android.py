"""Verify native Android version properties only in a disposable copy."""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import verify_examples


def read_only(binary, work, *args):
    before = verify_examples.snapshot(work)
    result = verify_examples.command([str(binary), *args], work)
    assert verify_examples.snapshot(work) == before, f"{args[0]} wrote files"
    return json.loads(result.stdout)


def verify(binary):
    folder = verify_examples.ROOT / "examples/android"
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp) / "fixture"
        shutil.copytree(folder / "fixture", work)
        expected = json.loads((folder / "expected-status.json").read_text())
        assert read_only(binary, work, "status") == expected
        report = read_only(binary, work, "doctor")
        assert report["passed"], report
        before = verify_examples.snapshot(work)
        assert "VERSION" not in before
        result = verify_examples.command([str(binary), "version"], work)
        assert json.loads(result.stdout) == expected
        properties_path = folder / "expected-gradle.properties"
        expected_properties = properties_path.read_bytes()
        assert expected_properties == before["gradle.properties"].replace(
            b"appVersionName=0.10.0", b"appVersionName=0.11.0", 1
        ).replace(b"appVersionCode=20", b"appVersionCode=21", 1)

        after = verify_examples.snapshot(work)
        note = ".changenote/sample.md"
        assert set(after) == (set(before) - {note}) | {
            "CHANGELOG.md",
            ".changenote/releases.json",
        }
        for path, original in before.items():
            if path == note:
                continue
            if path == "gradle.properties":
                assert after[path] == expected_properties
            else:
                assert after[path] == original, path
        message = expected[0]["notes"][0]
        assert after["CHANGELOG.md"].decode() == (
            f"## 0.11.0\n\n### Minor Changes\n\n- {message}\n\n"
        )
        batch = json.loads(after[".changenote/releases.json"])
        assert batch == [
            {key: value for key, value in expected[0].items() if key != "notes"}
        ]
        assert read_only(binary, work, "status") == []
        result = verify_examples.command([str(binary), "version"], work)
        assert json.loads(result.stdout) == []
        assert verify_examples.snapshot(work) == after, (
            "Empty release changed fixture files"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cli", required=True, help="CLI with Gradle properties support"
    )
    args = parser.parse_args()
    executable = shutil.which(args.cli)
    if executable is None:
        parser.error("CLI executable was not found")
    binary = Path(executable).resolve()
    before = verify_examples.snapshot(verify_examples.ROOT)
    verify(binary)
    assert verify_examples.snapshot(verify_examples.ROOT) == before, (
        "Verifier changed the example repository"
    )
    print(
        "Verified Android version 0.10.0 to 0.11.0 and code 20 to 21 "
        "in a temporary copy; source files are unchanged."
    )


if __name__ == "__main__":
    main()
