# KATAMI SKY — A Serialized Illustrated Memoir

Production: https://www.katamisky.com/ · GitHub Pages · `main`, repository root.

The memoir currently has three published installments: one Prologue installment
and two installments in Chapter 1 — Before Me. The 323 approved paragraphs are
locked by integrity checks. Finalized editorial pages run continuously from 1–20.
The childhood homepage background, small repositioned book, and stacked KATAMI / SKY
cover title are approved. Do not redesign them during routine publication.

## Publish and verify

Start with [AUTHOR-PUBLISHING-QUICKSTART.md](AUTHOR-PUBLISHING-QUICKSTART.md), then
[STORY-PUBLISHING.md](STORY-PUBLISHING.md) for metadata, prose, pagination and approval rules.
The author can supply an approved manuscript and publication instruction; the maintainer
uses the existing authoring helper and build workflow. No site restructuring is required.
This is a maintainer-assisted workflow, not a browser CMS.

```sh
python3 scripts/verify.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory .qa/public
```

Python 3 and Node.js are needed for the complete checks. The production builder uses
Python's standard library. Generated HTML is committed alongside approved source.
On Windows use `python` or `py` if `python3` is unavailable. Browser/mobile review
and live-host checks remain separate from these automated tests.

The suite checks static HTML, links/assets, editorial locks, publishing safeguards,
draft isolation, permanent URLs, continuous page numbers and consent-controlled analytics.
It also builds an isolated 120-installment fixture to exercise future growth.
The analytics and page-reader JavaScript tests use mocked browser interfaces: they do
not establish real Google receipt or physical-device behavior.

## Production and privacy

`CNAME` stays `www.katamisky.com`. GitHub Pages uses its existing Jekyll root publishing
path and `_config.yml` exclusions. Do not add `.nojekyll`, change providers, or deploy
`.qa/draft-preview`. Public generated output is `.qa/public`; development source is
excluded from the hosted site but is still visible in this public Git repository.
Never commit sensitive drafts, credentials, identity maps or confidential family material.

Reading position stays in localStorage under `katamisky_reader_progress`. Optional GA4
uses `G-7ZGG7KGK9H` and loads only after affirmative analytics consent on the canonical
production origin. Decline and withdrawal remain available on the Privacy page.
Google receipt and cookie withdrawal were previously owner-verified; see the current
[audit record](docs/V1-AUDIT-2026-10-28.md) for verified results and the completed Version 1 closure.
No newsletter service, signup form, advertising or session replay is installed.
The existing contact email's delivery has not been independently verified.

## Recovery and current status

[OPERATIONS-AND-RECOVERY.md](docs/OPERATIONS-AND-RECOVERY.md) records the production
baseline, backup branch, restoration procedure, and safe forward-only rollback.
[V1-AUDIT-2026-10-28.md](docs/V1-AUDIT-2026-10-28.md) is the current readiness record.
Older foundation/implementation documents are historical, not the current status.

Playwright and axe-core in `package.json` are optional development dependencies only.
They are not shipped to readers. `tests/browser.cjs` is a legacy browser harness and
requires its isolated fixtures; do not treat a mocked test or build as mobile visual QA.
