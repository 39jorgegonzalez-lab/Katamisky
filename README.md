# KATAMISKY — A Serialized Illustrated Memoir

Henry’s story comes first. This is a lightweight, static digital-book foundation.
No real memoir installment has been supplied or published. The public pages say so.
There is no sound experience and no sound code or assets.

## Start here

Start with [AUTHOR-PUBLISHING-QUICKSTART.md](AUTHOR-PUBLISHING-QUICKSTART.md).
Use [STORY-PUBLISHING.md](STORY-PUBLISHING.md) for the complete editor workflow.
The authoring frame is `templates/story-installment.html`; its editable prose starter
is `templates/memoir-prose.html`. Metadata and the prose, not a redesigned page, are
all that the next installment needs.

```sh
python3 scripts/verify.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory .qa/public
```

On Windows use `python` or `py` if `python3` is not available. The production builder
uses only Python's standard library. Generated HTML is checked in for GitHub Pages.
The `.qa/public` folder is a disposable, public-only preview; it is not committed.

## Publishing and source separation

Existing host: GitHub Pages, repository `39jorgegonzalez-lab/Katamisky`, `main`, root.
`CNAME` remains exactly `www.katamisky.com`. No domain or hosting-account setting is
changed. The original root publishing behavior used Jekyll; the unshipped prototype's
`.nojekyll` override has been removed. `_config.yml` excludes `templates`, `content`,
`scripts`, `tests`, documentation, package manifests, and private/local work folders.
The already-generated pages and assets are static files; no framework, theme, or
additional Jekyll plugin is required. Verify the actual Pages result after pushing.

The source repository is public. Build exclusions are **not confidentiality**.
Never commit private identities, unapproved private memories, or family reference
sheets here. Keep private drafts/reference material in private storage. `draft`
entries are excluded from the book and progress manifest, but committed source is
still visible on GitHub. `authorApproved: true` is an editorial approval record;
it must not be set for made-up, placeholder, or unapproved text.

## What is ready

- Six public pages: home, Story, Chapter 01, Archive, About, reader privacy.
- Honest no-installments state; no fake Begin Story destination or public samples.
- Published entries generate Previous/Next links, chapter/archive lists, dates,
  latest designation, sitemap entries, and the valid progress-URL manifest.
- Progress stays in localStorage under `katamisky_reader_progress` (version 1).
  Saving requires eight visible seconds plus 12% scroll progress, or a Next click.
  Continue Reading validates the published URL and restores approximate position.
  Retired prototype URLs are invalid; storage failures never block the story.
- Ivory 880px book / 680px prose, mobile layout, white lattice confined to hero.
- Playfair Display 500–700, Source Serif 4 400–600 and italic 400, Inter 400–700.
  IBM Plex Mono 400 is loaded only on documentary pages. All are local Latin WOFF2
  files with SIL licenses. Other language coverage must be added when needed.
- Reusable semantic illustration, vignette, artifact, transcription, dialogue,
  inner-thought, emphasis, environmental-text, and editorial-note treatments.
- Empty related-object data renders nothing. Amazon links preserve `katamisky-20`,
  proper sponsored/nofollow/noopener attributes, and visible disclosure.
- `templates/email-update.html` is a disabled editor specimen. No public signup
  form is rendered, because no provider is connected. No fake success exists.

## Test the future reader without publishing it

```sh
npm install
npx playwright install chromium
python3 tests/prepare_fixture.py
npm run test:browser
python3 tests/publisher.py
```

The test builder creates two explicitly labeled, non-biographical QA fixtures under
`.qa/fixture` only. The production `content/installments.json` stays empty. The
browser test starts its own temporary local servers. It checks the public foundation
and isolated reader separately, including actual browser close/reopen. All test
output stays under `.qa/`; none belongs in production.

Optional `CHROMIUM_PATH` and `AXE_PATH` select existing Chromium/axe installations.
Playwright and axe are development tools; browsers never download them from this site.

## Operational state

The pre-change production rollback point is
`2e0a704846235f6724a1b4045a96303b185ac85f`.
The previous local prototype was `d3ac0fdf1e9166d134d8fbe2b4de11ced3d391cd` and was
never deployed. See `docs/IMPLEMENTATION.md` for current access/deployment status,
QA findings, exact cleanup classification, and remaining limitations.

The pre-existing `hello@katamisky.com` link and `/about.html` URL are retained.
Mailbox delivery has not been verified. No analytics or tracking have been added.

## Author tools and publication states

`python3 scripts/new_installment.py` creates a safe starter and valid metadata, always
draft/unapproved. Only approved publication material belongs in this public repository.
Draft/unapproved is omitted; draft/approved is still omitted from production. Use
`python3 scripts/build.py --preview-drafts` to review approved drafts locally under
`.qa/draft-preview` without changing production pages. Published/approved generates only
after validation; published/unapproved fails. Never deploy the draft-preview directory.

Generated files: root HTML, story/chapter/reader HTML, archive/privacy HTML, sitemap.xml,
robots.txt and assets/js/story-manifest.js. Edit builder/templates/content, not these outputs.
The published-path registry is build-maintained; do not delete entries to bypass URL guards.
Run `python3 scripts/verify.py` after changes; browser review remains a separate gate.

Fetch/check remote main before committing and pushing; reconcile unexpected changes.
Do not force-push. After Pages succeeds, verify the actual public domain, console, fonts,
mobile, links and development-path exclusions. A local export is not a Jekyll/live-host test.
See docs/FINAL-FOUNDATION.md for the final pass and exact file classification.
