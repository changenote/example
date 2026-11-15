# Android Gradle version properties

This fixture uses the native `gradle.properties` file as its only version
source. No separate `VERSION` file is needed.

The starting properties are:

```properties
appVersionName=0.10.0
appVersionCode=20
```

A sample minor note produces version `0.11.0`, code `21`, and tag `v0.11.0`.
Only the two property values change; comments and other Gradle settings remain
unchanged. The note is sample input, not a change to an active package.

This is a version-metadata fixture, not a complete Android build.
The property names are a supported project convention, not mandatory Android
names. A real app's Gradle build must map them to Android's `versionName`
and `versionCode`.

## Inspect the plan

Use a local CLI build with Android Gradle properties support.
The older CI CLI pin does not include this format and remains unchanged.

With sibling `changenote` and `example` checkouts, run from the `example` root:

```sh
cargo build --locked --manifest-path ../changenote/Cargo.toml -p changenote
cli="$(cd ../changenote && pwd)/target/debug/changenote"
work=$(mktemp -d)
cp -R examples/android/fixture/. "$work/"
"$cli" --root "$work" status
```

Compare the result with [expected-status.json](expected-status.json).
`status` does not change files.

## Verify release writes

```sh
uv run --no-project python scripts/verify_android.py \
  --cli ../changenote/target/debug/changenote
```

This separate verifier needs Python 3.11 or later and a compatible CLI,
but no Java, Gradle, or Android SDK.
It uses a temporary copy to verify:

- Read-only `status` and `doctor` results.
- Both value updates against
  [expected-gradle.properties](expected-gradle.properties).
- Unchanged comments, other settings, and configuration.
- The changelog, saved batch, and consumed sample note.
- No additional `VERSION` file and no changes from an empty second release.
- An unchanged source repository.

It does not run tags, publication, workflows, Gradle builds, or active-package
versioning. Only the disposable copy receives release writes.

## Limits

- Both properties are required exactly once.
- The version name must be literal stable SemVer.
- The code must be a positive canonical decimal integer within Android's
  signed 32-bit range. A release increments it once, for any SemVer bump.
- A code increment that would overflow fails before release writes.
- Inline comments, trailing value whitespace, escapes, and continuations
  are not supported in the configured version source.
  - Whole-line `#` and `!` comments are supported.
  - Backslashes on any non-comment line are rejected, including unrelated keys.
- Google Play's separate code limit and previously published codes are not
  checked. Build overrides and actual APK metadata need separate verification.
- CLI generation and replay must use a compatible version.

See the [Android release guide](https://github.com/changenote/changenote/blob/main/docs/android.md)
for supported separators, code limits, build overrides, and rollout details.
