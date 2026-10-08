# Recipe import provenance

The initial import copies the tracked tree of each commit below without modifying
recipe files. Original repositories retain their complete Git histories, issues,
and release metadata; those histories are not merged into this repository. This is
a snapshot import, not a GitHub repository transfer.

| Recipe directory | Original repository | Imported commit | Tracked files |
| --- | --- | --- | ---: |
| `nunez-elizalde-2022-bids` | [sdiebolt/nunez-elizalde-2022-bids](https://github.com/sdiebolt/nunez-elizalde-2022-bids) | [`e72ce8dbd6acd4279ba43f8c6ef50c406520d856`](https://github.com/sdiebolt/nunez-elizalde-2022-bids/commit/e72ce8dbd6acd4279ba43f8c6ef50c406520d856) | 123 |
| `landemard-2026-bids` | [confusius-tools/landemard-2026-bids](https://github.com/confusius-tools/landemard-2026-bids) | [`2bcbdad4d9679224fb886e629956685f7154ca58`](https://github.com/confusius-tools/landemard-2026-bids/commit/2bcbdad4d9679224fb886e629956685f7154ca58) | 10 |
| `cybis-pereira-2026-bids` | [confusius-tools/cybis-pereira-2026-bids](https://github.com/confusius-tools/cybis-pereira-2026-bids) | [`cd69a324c3761cc415174c65d9616a23cf10b6ab`](https://github.com/confusius-tools/cybis-pereira-2026-bids/commit/cd69a324c3761cc415174c65d9616a23cf10b6ab) | 11 |
| `pereira-2025-bids` | [confusius-tools/pereira-2026-bids](https://github.com/confusius-tools/pereira-2026-bids) | [`3f983699fcf83f038c9c0e98a411ea9c1b85c958`](https://github.com/confusius-tools/pereira-2026-bids/commit/3f983699fcf83f038c9c0e98a411ea9c1b85c958) | 11 |
| `pepe-mariani-2026-bids` | [confusius-tools/pepe-mariani-2026-bids](https://github.com/confusius-tools/pepe-mariani-2026-bids) | [`1557facd6b1844b9d090f9f7e651ba731d15747c`](https://github.com/confusius-tools/pepe-mariani-2026-bids/commit/1557facd6b1844b9d090f9f7e651ba731d15747c) | 10 |
| `pepe-mariani-2026-template` | [confusius-tools/pepe-mariani-2026-template](https://github.com/confusius-tools/pepe-mariani-2026-template) | [`7fcea0fb32962dea10716fcf24a7aa613169b3bb`](https://github.com/confusius-tools/pepe-mariani-2026-template/commit/7fcea0fb32962dea10716fcf24a7aa613169b3bb) | 10 |
| `huang-2025-template` | [confusius-tools/huang-2025-template](https://github.com/confusius-tools/huang-2025-template) | [`8ad89da5039ba529911ed7fcb473e99f861525c4`](https://github.com/confusius-tools/huang-2025-template/commit/8ad89da5039ba529911ed7fcb473e99f861525c4) | 9 |

## Naming

Local recipe identifiers are retained even where the GitHub owner or repository
name differs. In particular, Nunez-Elizalde remains sourced from `sdiebolt`, and the
Pereira 2025 recipe is imported from a remote named `pereira-2026-bids`. These source
repositories have not been renamed or transferred.

## Excluded local content

The original local checkouts also contain untracked generated dataset directories
named `nunez-elizalde-2022-bids/`, `pereira-2025-bids/`, and
`pepe-mariani-2026-bids/`, respectively. They are not part of the committed recipe
trees and are intentionally not imported. They remain untouched in their original
locations for later release staging and validation.

Virtual environments, ignored files, Git metadata, and downloaded or generated data
are not imported. No original checkout or remote repository is modified by the
snapshot import.

## Retirement

After the S3 releases and migrated downloaders are verified, add relocation notices
to the original READMEs and archive the repositories publicly. Do not delete them or
make them private: their public histories and existing links preserve provenance.
Existing OSF datasets should remain available for older ConfUSIus releases.
