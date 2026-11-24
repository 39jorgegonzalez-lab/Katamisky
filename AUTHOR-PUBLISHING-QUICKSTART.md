# Publishing a New Henry Installment

**Write privately first. This GitHub repository is public—even unpublished source.**
Never put private identities, sensitive drafts, correspondence or evidence here.

1. **Finish the text privately.** Edit outside the public repository.
2. **Approve the text and titles.** Choose the chapter, installment title and permanent meaningful slug.
3. **Create the starter.** Run `python3 scripts/new_installment.py`. Add only approved prose; remove unused template blocks.
4. **Add an optional approved image.** Give it an accurate caption, description and provenance. Never invent missing facts.
5. **Preview.** Set `authorApproved` to `true` but keep `status` as `draft`. Run `python3 scripts/build.py --preview-drafts`. Review the local preview, including phone widths. Approval does not publish it.
6. **Approve publication separately.** Only when ready, change `status` to `published` and confirm the real publication date.
7. **Build and test.** Run `python3 scripts/verify.py`. Review the public preview. Navigation and archive update automatically.
8. **Publish.** Review changes, commit and push to main with authorized access. Wait for GitHub Pages success.
9. **Check the live page.** Hard-refresh KATAMISKY.com; test links, reading layout and a real phone. A local preview is not proof it is live.

Use [STORY-PUBLISHING.md](STORY-PUBLISHING.md) for exact preview commands and editorial details.
Never change a published URL. Visible page numbers are separate from permanent addresses.
No newsletter service is connected. Three installments are published; preserve their approved prose and permanent URLs.

**Page-density review:** Every new installment inherits the 28–31 rendered desktop-line target. The maintainer runs the private browser review with `python3 scripts/page_density.py --prepare`, adjusts only whole-paragraph page breaks, and records the measured result before verification. Literary exceptions are welcome when explained; mobile line counts vary naturally. You do not need to review code or alter prose to satisfy a numeric quota. See “Page density” in `STORY-PUBLISHING.md`.
