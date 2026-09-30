# Publishing Henry’s story

**This repository is public. Never put sensitive or unapproved memoir drafts here.**
Write and edit privately outside this repository. Never commit pseudonym keys, private
identity maps, addresses, confidential correspondence, legal notes, private allegations,
credentials, or unpublished evidence. GitHub Pages exclusions are not confidentiality:
committed source remains visible on GitHub, even when its status is `draft`.

## The author’s seven decisions

1. Write privately.
2. Edit and approve the actual text.
3. Choose the approved title and meaningful permanent slug.
4. Choose optional approved artwork or archival material.
5. Add only approved publication material to KATAMISKY source.
6. Build and preview; review mobile, wording, captions and navigation.
7. Explicitly approve publication, publish, and verify the live page.

See [AUTHOR-PUBLISHING-QUICKSTART.md](AUTHOR-PUBLISHING-QUICKSTART.md) for the short checklist.
No first installment exists yet. Neither the starter nor test fixtures are Henry’s story.

## Create the source safely

Run `python3 scripts/new_installment.py`. It asks for chapter ID, approved title,
permanent slug, short description, intended date and source filename. It creates a
copy of `templates/memoir-prose.html` and inserts its metadata without hand-editing JSON.
It refuses duplicate URLs, existing filenames, invalid paths and malformed metadata.
It always starts with `status: "draft"` and `authorApproved: false`; it never publishes.
The starter contains no invented autobiographical material. Replace its fields with
approved text, and remove every unused component. Do not use it to write sensitive drafts.

The approved chapter title belongs in `content/chapters.json`. Installment metadata
lives in `content/installments.json`; entries appear in reading order. The `id` is the
permanent slug: `/story/chapter-01/meaningful-slug/`. Optional `pageNumber` is a positive
integer independent of that URL. Do not use page-number URLs.

For paragraph-only installments, optional `pageBreaks` lists the paragraph numbers
after which a book page ends (for example, `[18, 29, 46, 64]` creates five pages).
These are display boundaries only: the builder preserves every paragraph's text
and punctuation. Touch readers can swipe horizontally; numbered controls sit below
the current page. The permanent installment URL stays the same, with optional
`#page-2` fragments. Printing or disabling JavaScript exposes the complete text.

## Approval is separate from publication

| status | authorApproved | Production build | Local approved-draft preview |
|---|---|---|---|
| draft | false | Omitted | Omitted |
| draft | true | Omitted | Included after content validation |
| published | true | Included after all safeguards | Included |
| published | false | Build refused | Build refused |

Set `authorApproved: true` only after reviewing the actual source, title, description,
chapter title and any illustrations. **Keep status `draft` until the publishing decision.**
An approved draft may remain unpublished indefinitely. Its committed source is still public.

```sh
python3 scripts/build.py --preview-drafts
python3 -m http.server 8765 --bind 127.0.0.1 --directory .qa/draft-preview
```

Open `http://127.0.0.1:8765/`. This isolated preview includes approved drafts and is
labeled NOT PUBLISHED with noindex metadata. It does not change production pages,
metadata, published-path registry or production manifest. It permits intended future
dates for editorial review only. Never upload `.qa/draft-preview` or use it as deployment
output. Unapproved entries never appear. Stop the server before changing preview folders.

## Images and provenance

Use the figure components in `templates/memoir-prose.html`. Their consistent metadata
format uses a visible editorial label, an image with `alt`, and a caption/metadata block:

| Field | Location / rule |
|---|---|
| TYPE | `data-type` on figure: narrative, vignette, artifact or transcription |
| AUTHENTICITY | `data-authenticity` and visible label: reconstruction, authentic or transcription |
| SOURCE | Labeled Source text in `artifact-meta`, only when supplied |
| CAPTION | `literary-caption` or figure caption, author-approved text |
| ALT TEXT | Image `alt`, concise accurate description; empty only for decoration |
| DATE | Labeled date or `time` with a known ISO date; omit if unknown |
| CREDIT | Labeled Credit text, only when supplied |

Unknown provenance stays unknown. Do not invent a date or claim a family-archive source
without evidence. Distinguish “Illustrated reconstruction based on Henry’s recollection”
from an actual archival photograph/document. Label recreated documents as recreated.
Put approved compressed images under `assets/images/story/` or `assets/images/archive/`.
Set actual dimensions and lazy-load below the fold. Actual handwriting needs a readable
transcription. Set `document: true` for `.document-text`; this enables IBM Plex Mono.

Normal dialogue uses Source Serif 4, thoughts its italic, restrained emphasis its semibold,
environmental text Inter. Keep Playfair Display for literary headings. Use original mature
graphite/charcoal/ink qualities, not a named artist imitation. Illustrate the memory, not
the spectacle of injury. Never invent memoir events, documents or photographic evidence.

## Optional related objects and email

Empty `objects: []` renders nothing. Objects are editorial context first: archival objects,
museum/reference links, historical context, modern equivalents and relevant memorabilia
are all valid. Each needs `title`, HTTPS `url`, and an author-supplied `connection`.
Ordinary reference links are not marked sponsored. Set `affiliate: true` for commercial
affiliate links. Amazon URLs must contain `tag=katamisky-20`; these get sponsored/nofollow/
noopener and the Amazon disclosure automatically. Keep all objects after the memoir.

No public email form is rendered. `templates/email-update.html` is an inactive specimen.
Before enabling the latest-installment slot, connect a real provider, verify consent,
unsubscribe and delivery, and update the privacy notice. Never fake signup success.

## Publish and verify

After the explicit publishing decision, set `status: "published"`, leaving approval true.
Use a real publication date no later than today. Then run:

```sh
python3 scripts/verify.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory .qa/public
```

The single command reuses the builder, static checker and publication/workflow tests.
Malformed JSON, missing fields/sources, duplicate URLs (including drafts), unapproved
publication, future dates, unfinished placeholders, unsafe markup, broken local links,
missing images, invalid HTML and disappearing published URLs stop the build. Generated
pages are validated before any production file is written; validation failures leave
existing output intact. This does not provide filesystem transaction recovery after an
operating-system/disk failure: keep the Git rollback point.

The builder automatically updates Previous/Next, Chapter Index, Archive, latest marker,
Begin the Story, sitemap and progress allowlist from published metadata. Do not hand-edit
these generated pages or `assets/js/story-manifest.js`. The shared layout is
`templates/story-installment.html`; prose stays ordinary HTML and works without JavaScript.
Continue Reading uses browser storage only and rejects unpublished/stale paths.

Review 320, 375, 390 and 430px, plus desktop: text size, margins, images, captions, navigation,
buttons, no sideways scrolling. Check keyboard focus and links. For implementation changes,
run the browser regression described in README. Review `git diff` and `git status`; ensure
no private material or `.qa` output is staged. Commit approved source and generated output
together. Fetch remote main, reconcile new work, and push without force.

Wait for GitHub Pages deployment success. Hard-refresh https://www.katamisky.com/ and
follow Begin/Continue, Previous/Next, Chapter Index, Archive and About. Check fonts, assets
and console. Verify `/templates/story-installment.html`, `/content/installments.json`,
`/tests/browser.cjs`, `/scripts/build.py`, `/docs/IMPLEMENTATION.md`, `/package.json`,
`/STORY-PUBLISHING.md`, `/AUTHOR-PUBLISHING-QUICKSTART.md` and `/README.md` return 404.
Jekyll exclusions must be checked on the real host, not inferred from a local export.
Ask the owner to repeat homepage/nav/fonts/margins/buttons/story/chapter/archive/no-sideways-
scroll checks on a real phone. Repeat on the reader once a real installment exists.
Do not claim deployment or live verification when a push fails.

## Permanent URLs and rollback

Never rename/remove a published slug to satisfy a build. `content/published-paths.json`
protects previously published URLs. For an exceptional move, implement and test a retained
old-URL compatibility page/redirect before any registry migration; this requires a reviewed
code change, not deleting a registry entry. Old bookmarks must keep working.

Known original production rollback: `2e0a704846235f6724a1b4045a96303b185ac85f`.
Record current remote HEAD before every release. Revert through a normal reviewed commit;
never force-push over later work. Keep CNAME exactly `www.katamisky.com`.
