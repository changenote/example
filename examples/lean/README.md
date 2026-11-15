# Lean 4 package releases

This fixture uses the native top-level `version` in `lakefile.toml` as its
only package version source. No separate `VERSION` file is needed.

The package starts at `1.2.3`. A sample minor note plans `1.3.0` with
tag `v1.3.0`. The fixture includes a small Lean library, a pinned
`lean-toolchain`, and a dependency manifest with no dependencies.
The note is sample release input, not a change to an active package.

The [configuration](fixture/.changenote/config.json) selects
`"version_file": "lakefile.toml"` with no additional version outputs.
The fixture requires a CLI build with `lakefile.toml` support.
The older CLI source pin in this repository's CI does not include that support.
Keep this check separate until a reviewed compatible revision is available.

## Inspect the release plan

With sibling `changenote` and `example` checkouts, run from the `example` root:

```sh
cargo build --locked --manifest-path ../changenote/Cargo.toml -p changenote
cli="$(cd ../changenote && pwd)/target/debug/changenote"
work=$(mktemp -d)
cp -R examples/lean/fixture/. "$work/"
"$cli" --root "$work" status
```

Compare the result with [expected-status.json](expected-status.json).
`status` does not change files.

## Verify release writes

Run the separate verifier with the same local build:

```sh
uv run --no-project python scripts/verify_lean.py \
  --cli ../changenote/target/debug/changenote
```

The verifier requires Python 3.11 or later and a compatible CLI; it needs
no Lean runtime or network access.
It copies the fixture to a temporary directory and checks:

- Read-only `status` and `doctor` results.
- The release version, changelog, saved batch, and consumed sample note.
- The TOML update against [expected-lakefile.toml](expected-lakefile.toml).
  - Only the top-level version changes; comments and other fields stay unchanged.
- Unchanged Lean sources, `lean-toolchain`, and `lake-manifest.json`.
- No separate `VERSION` file, an empty second release, and unchanged source files.

Only the temporary copy receives `version` writes.
The verifier does not create tags, publish artifacts, run workflows,
or change active packages.

## Build the sample library

The fixture pins Lean 4.35.0. With that toolchain installed through elan,
build only a temporary copy:

```sh
work=$(mktemp -d)
cp -R examples/lean/fixture/. "$work/"
(cd "$work" && lake build)
```

If the pinned toolchain is not installed, elan can download it.
The library has no external dependencies.
The release verifier does not run this build.

## Version-source limits

- `lakefile.toml` needs an explicit stable SemVer `version` string.
  Lake's implicit `0.0.0` default is not a changenote version source.
- `lean-toolchain` selects the compiler, not the package release version.
- `lake-manifest.json` records dependencies. Its `version` identifies the
  manifest format, not the package release.
- The single-package `v<version>` tags match Lake's default `versionTags`.
  For monorepos, select compatible tag prefixes and Lake tag patterns separately.

This example does not verify Reservoir indexing or hosted publication.
See the [Lean 4 release guide](https://github.com/changenote/changenote/blob/main/docs/lean.md)
for configuration and tag details.
