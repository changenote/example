# pnpm and Bun releases

These fixtures use `package.json` versions and a shared workspace lockfile.
Each fixture starts `app` and `library` at `1.2.3` in a fixed version group.
One minor note for `library` plans both packages at `1.3.0`.
The `app` dependency stays `workspace:*`; changenote does not rewrite dependency requirements.

| Fixture | Existing lockfile | Expected result |
| --- | --- | --- |
| [pnpm](pnpm/fixture/) | `pnpm-lock.yaml` | Manifests update; the lockfile stays unchanged because pnpm does not store package versions. |
| [Bun](bun/fixture/) | `bun.lock` | Manifests and both workspace versions in the text lockfile update. |

Both fixtures contain lifecycle scripts that write `lifecycle-ran` if executed.
The pnpm fixture also contains a `.pnpmfile.cjs` hook that fails if executed.
Verification must leave these scripts and hooks unexecuted and must not create `node_modules`.
All dependencies are local workspace links, so these tests need no registry access or populated dependency cache.

## Verify with a local CLI build

Use pnpm 12.21.0, Bun 1.4.4, uv, and a CLI build with pnpm and Bun support.
Other package-manager versions must accept the flags below and read the fixture lockfile formats.
The repository's older pinned CI CLI does not include this support; this verifier is a separate opt-in check.

With sibling `changenote` and `example` checkouts, run from the `example` root:

```sh
cargo build --locked --manifest-path ../changenote/Cargo.toml -p changenote
uv run --no-project python scripts/verify_package_managers.py --cli ../changenote/target/debug/changenote
```

The verifier requires both package managers; it does not silently skip missing tools.
It copies each fixture to a temporary directory, checks `status` and `doctor`, then runs `version` only in that copy.
It checks manifest bytes, changelogs, the saved batch, consumed notes, and an empty second release.
It also runs these frozen/offline validation commands in the copies:

```sh
pnpm install --lockfile-only --ignore-scripts --ignore-pnpmfile --offline --frozen-lockfile
bun install --lockfile-only --ignore-scripts --offline --frozen-lockfile
```

The verifier checks that the source repository remains unchanged.
It does not run tags, publication, GitHub workflows, or active-package versioning.
These fixtures do not prove Action staging, cache preparation, or hosted publication support.

Keep one Node.js lockfile per owning directory. Mixed lockfiles fail instead of selecting a tool by priority.
Binary `bun.lockb` files are not supported; migrate to text `bun.lock` before versioning.
