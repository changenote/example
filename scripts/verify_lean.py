"""Verify the Lean 4 TOML release example only in a disposable copy."""

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
    folder = verify_examples.ROOT / "examples/lean"
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
        release = expected[0]
        version = release["version"]
        expected_manifest = folder / "expected-lakefile.toml"
        expected_content = expected_manifest.read_bytes()
        assert expected_content == before["lakefile.toml"].replace(
            b'version = "1.2.3"', b'version = "1.3.0"', 1
        )

        after = verify_examples.snapshot(work)
        note = ".changenote/sample.md"
        assert set(after) == (set(before) - {note}) | {
            "CHANGELOG.md",
            ".changenote/releases.json",
        }
        for path, original in before.items():
            if path != note:
                content = expected_content if path == "lakefile.toml" else original
                assert after[path] == content, path

        heading = release["bump"].capitalize()
        message = release["notes"][0]
        assert after["CHANGELOG.md"].decode() == (
            f"## {version}\n\n### {heading} Changes\n\n- {message}\n\n"
        )
        batch = json.loads(after[".changenote/releases.json"])
        assert batch == [
            {key: value for key, value in release.items() if key != "notes"}
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
        "--cli", required=True, help="CLI executable with lakefile.toml support"
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
        "Verified the Lean 4 TOML release in a temporary copy; "
        "source files, toolchain pins, and dependency manifests are unchanged."
    )


if __name__ == "__main__":
    main()
