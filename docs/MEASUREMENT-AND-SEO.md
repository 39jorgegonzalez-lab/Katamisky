# Technical foundation and measurement

The literature is locked. SEO works around it. Never rewrite prose, merge
paragraphs, extract new descriptions, or invent dates or historical facts.

## Publishing and metadata

Python's standard-library builder generates committed static HTML. GitHub Pages
publishes `main` from the repository root; `CNAME` is `www.katamisky.com`.
Run `python3 scripts/verify.py` (Python 3 and Node required). Never publish `.qa/`
previews or editor sources; preserve `_config.yml` exclusions.

Every installment inherits its self-canonical, unique title and approved metadata
description, Open Graph/Twitter cards, Article and breadcrumb JSON-LD, archive,
sitemap, navigation and optional measurement. WebSite and Person identify the
site and its public author Henry. No organization, rating, historical image,
birth date or modification date is invented. Use the real publication `date`.
Optional `dateModified` is only for a verified editorial change, never a rebuild.

The Prologue's historical URL contains `chapter-01`; keep it stable. Hierarchy
comes from metadata: Prologue → Chapter 1 — Before Me. Book-page hashes are
positions within an installment, not separate indexable pages. Query variants
canonicalize to the clean URL. Each installment retains its own canonical.

The 1200×630 fallback social card is original typography using existing site
typefaces, colors and byline, not a historical photograph. The committed PNG is
used by normal builds. `scripts/build_social.py` can recreate it with Pillow,
fontTools and Brotli. Optional approved `socialImage` metadata needs `path`,
`alt`, `width`, `height`; use an existing local PNG/JPEG/WebP in `/assets/images/`.
Preserve distinctions between Narrative Illustration, Memory Vignette and
Authentic Artifact. Never invent captions or represent reconstruction as evidence.

The archive automatically paginates after 50 installments, preserving reading
order and chapter grouping. Extra pages use `/archive/page/2/` etc., distinct
metadata, self-canonicals, sitemap entries and crawlable Previous/Next links.
No redundant `/archive/page/1/` exists. Chapter indexes provide a second route.
Sitemap generation excludes drafts; robots permits public crawling and names the
sitemap. Neither robots nor a public repository protects private source material.
Content-hashed CSS and the entire reader import chain refresh on publication
without changing bookmark URLs or the existing saved-position data format.

## GA4 — consent-controlled activation

On 2026-10-01 the owner supplied production Measurement ID `G-7ZGG7KGK9H`
for `https://www.katamisky.com` and confirmed **Enhanced measurement OFF**.
`content/site-settings.json` enables this ID using the existing integration.
The public Measurement ID is not an API secret. No second implementation or
Google Tag Manager container is installed. Keep Google signals, advertising
personalization and user-provided data collection off in the Google property.

**GA4 ACTIVATION — COMPLETE**

Owner production verification accepted on 2026-10-01 (America/Bogota), following
deployment of activation commit `15f149f4ca84b706ae9607f6f7922185d30cf4d3`.
The owner confirmed:

- Before consent: no `gtag.js` request, no Google Analytics `collect` request,
  and no `_ga` cookies. Declining preserved this no-collection state.
- After Allow analytics: `gtag.js` loaded with HTTP 200, a `collect` request
  completed with HTTP 204, and `_ga` and `_ga_7ZGG7KGK9H` cookies were created.
- Actual production receipt in Google Analytics Realtime: 1 active user,
  1 view, and `/privacy/`.
- After withdrawal through Decline analytics: the `_ga` cookies disappeared.
  After clearing the Network log and navigating to `/story/`, no new `collect`
  or `gtag` requests occurred. The site remained functional.

This is owner-observed production evidence, not a claim of direct agent access
to GA4. It satisfies the previously pending owner-verification requirement.
The prior complete build, 23 analytics checks, production DOM/navigation checks,
and verification of all 215 locked manuscript paragraphs remain accepted.
Realtime receipt of individual navigation and reading-milestone events is not
separately asserted by this owner confirmation; their existing local test
results remain the recorded evidence. This closure changes documentation only.

Future regression reference (not an outstanding activation requirement):
1. In a fresh private browser window, open developer tools before loading the
   production site. In Network enable Preserve log and filter Google tag and
   Analytics requests. Before consent, and after Decline, expect no Google tag
   request, no Analytics collection, and no `_ga` cookies in Application → Cookies.
2. Allow analytics. Expect one `gtag/js?id=G-7ZGG7KGK9H` request per document,
   one manual `page_view`, and `installment_view` on a memoir installment.
   Inspect collection payloads: `tid` must match the ID; `dl` is a clean canonical
   URL, `dr` is empty, and `dt` contains technical IDs rather than memoir text.
   No query strings, bookmark, form data or manuscript should be present.
3. Test Begin the Story, Next/Previous installment, Continue Reading and Archive.
   Book-page hash changes must add no `page_view` or `installment_view`.
   Read each page with sufficient active time and full coverage to see the four
   milestone events; jumps, rapid scrolling and restored bookmarks give no credit.
4. On Privacy choose Decline analytics. After the withdrawal reload, expect no
   new Google collection or tag request and no site-accessible `_ga` cookies.
   Reading and navigation must still work.
5. In the correct GA4 property open Reports → Realtime → Event count by event
   name. Confirm `page_view`, `installment_view`, navigation events and reading
   milestones from the consented test visit. DebugView is optional and requires
   a debug session; the production code does not enable debug mode for readers.
   A successful network response alone is not property receipt verification.

Basic opt-in blocks the Google tag itself until grant. Decline and Allow use
equivalent controls; choices remain available on Privacy when enabled. Consent
and analytics cookies last up to 180 days. Withdrawal disables new collection,
clears this site's `_ga` cookies and milestone flags, then reloads to unload the
tag. A full storage quota cannot preserve an old grant: withdrawal removes it
before saving denial. If storage cannot be modified at all while an old grant
remains readable, collection stops on the current page without reloading, and
Privacy explains that site data must be cleared to keep it off on return.
It does not undo data already received by Google. No advertising, session
replay, fingerprinting or user-ID features are installed.

`begin_story`, `next_installment`, `previous_installment`, `continue_reading`
measure their respective links. `installment_view` and `archive_visit` measure
destination document views. Refresh creates a legitimate new view, not an
invented click. Activation is idempotent. `send_page_view:false` disables the
config-generated view; one manual view is queued. The Google stream must also
have Enhanced measurement disabled to prevent vendor-generated extras.

Allowed context: `installment_id`, `chapter_id`, `section`, `content_type`,
`navigation_origin`, for the current page where applicable. Page location is
the clean canonical. Page title uses technical IDs, not manuscript headings.
Referrer is blank. No manuscript text, saved bookmark, name, email, query string,
form entry or pointer coordinates are sent. Register these context parameters
as event-scoped custom dimensions if needed for GA4 reports.

`reading_25/50/75/complete` are conservative engagement estimates, not proof of
reading. Each book page needs all ten vertical bands viewed and active viewing
time at least the larger of 8 seconds or a 240-words/minute estimate. Background,
unfocused, over-60-second idle and delayed timer ticks do not count. Completed
pages contribute word-count weight to the installment's thresholds. Only event
names/context leave the browser; text, counts and bands stay in memory.
Consent starts fresh, with no backfill. Saved positions and end jumps give no
credit. Refresh resets coverage credit but retains once-per-tab-session event
flags; rereads and interrupted sessions can therefore be undercounted.

## Search Console — owner action required

GSC Wizard returned `payment_required` for both Search Console property discovery
and GA4 discovery. No property, ownership, indexing or sitemap submission was
verified. Google's own Search Console is available without a paid connector.
The owner can act directly or authorize browser-based continuation.

1. Search Console → property selector → Add property → **Domain** → `katamisky.com`.
   Reuse the existing Domain property if it is already in the owner's account.
2. Copy Google's generated verification TXT value; it was unavailable here.
3. At the authoritative DNS provider add **TXT**, host **@** (root/apex; blank
   if the provider uses blank), value **the exact `google-site-verification=…`
   token from Google**, TTL **Auto/default** (3600 if a number is required).
   Preserve existing TXT records; never guess the token.
4. After propagation click **Verify** in Search Console. Keep that DNS record.
5. Sitemaps → submit `https://www.katamisky.com/sitemap.xml`; confirm successful
   processing. Inspect the homepage and both installment URLs and record actual
   coverage/canonical results. Do not mass-request indexing.

## Hosting and acceptance

All canonicals, OG URLs and sitemap URLs use HTTPS/www. Check repository Settings
→ Pages → **Enforce HTTPS**. A preliminary retrieval served HTTP/www with 200;
confirm the host setting and permanent redirects. A canonical tag or JavaScript
redirect cannot replace a server redirect. Preserve the current custom domain.

Final acceptance requires real GA4 receipt, Search Console ownership/sitemap
processing, verified HTTPS variants, real 375/390/430px/tablet/desktop review,
keyboard navigation and live metadata. Separate source/unit checks from browser
QA and Google receipt. Do not infer Lighthouse scores, Core Web Vitals or rich
result eligibility from static validation.

References: [basic consent](https://developers.google.com/tag-platform/security/concepts/consent-mode),
[manual pageviews](https://developers.google.com/analytics/devguides/collection/ga4/views),
[Article schema](https://developers.google.com/search/docs/appearance/structured-data/article),
[Search Console verification](https://support.google.com/webmasters/answer/9008080).
