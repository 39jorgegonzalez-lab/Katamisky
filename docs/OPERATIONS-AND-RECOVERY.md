# KATAMI SKY operations and recovery

Verified baseline on 2026-10-28 (America/Bogota):
`513228b0476cfd63de0e57d0ef5314bf7d28b622`.
GitHub Pages deployment run `38670920227` succeeded for this exact commit.
Repository: `39jorgegonzalez-lab/Katamisky`; branch `main`; root publishing with
Jekyll exclusions; custom domain `www.katamisky.com`.
Remote backup branch: `backup/v1-approved-20261028`, pointing to that baseline.
This is an ordinary backup reference, not an independently protected or off-provider backup.
Do not force-push, delete or repurpose it. Keep GitHub/domain-owner recovery methods current;
account MFA, registrar recovery and billing were not inspected by this audit.

## Verified recovery drill

A complete Git bundle was created and verified, cloned into an isolated directory,
and the full `scripts/verify.py` process run from that restored copy. All 37 exported
public files matched the original build byte-for-byte. `git fsck --full` succeeded.
No production rollback was performed. The temporary drill bundle is not a promised
permanent offsite backup; the remote backup branch and recorded commit retain the baseline.

Repeat in a maintainer-controlled backup location (not public hosting):

```sh
git fetch origin
git bundle create katami-sky-backup.bundle --all
git bundle verify katami-sky-backup.bundle
git clone katami-sky-backup.bundle katami-sky-restore
cd katami-sky-restore
git checkout 513228b0476cfd63de0e57d0ef5314bf7d28b622
python3 scripts/verify.py
```

Store the resulting bundle in an owner-controlled durable backup location if an
independent backup is required. Do not assume a temporary workspace survives.
The site has no server-side reader database. Browser-local reading positions and
consent choices are not stored in this repository and are not recoverable from Git.
Google Analytics data lives in Google and is not backed up by a site source bundle.

## Safe rollback and republishing

1. Fetch current remote `main`; record its exact commit and the last successful Pages run.
2. Identify the specific faulty release. Check for later content before reverting anything.
3. On a new branch from current `main`, use a normal `git revert` of the faulty commit
   (or a narrowly reviewed restoration commit). Do not reset/force-push production history.
4. Preserve all approved manuscripts, permanent URLs and later releases. Run the full
   verification command and inspect the desktop/mobile preview.
5. Integrate through a normal fast-forward/non-force push or reviewed merge to `main`.
6. Wait for the matching GitHub Pages run to succeed. Check the HTTPS homepage,
   affected readers/assets, and source-path exclusions on the public domain.

A total source restore can use the baseline checkout above. Reattaching hosting still
requires owner permissions: verify Pages source `main` / root, CNAME, custom-domain DNS,
certificate and Enforce HTTPS in GitHub settings. Do not change provider arrangements
as part of recovery. A Git clone alone does not recover account ownership or DNS.

## Routine publication

Follow the quickstart and STORY-PUBLISHING.md. Keep source drafts private. Finalize
paragraph-boundary `pageBreaks`; append the approved installment in reading order.
The builder generates chapter/archive counts, links, metadata, sitemap, reading manifest
and continuous page numbers. Do not hand-edit generated HTML or old page offsets.
Run `python3 scripts/verify.py`, review a browser preview, obtain the owner's publishing
instruction, and release source plus generated output together. Never deploy fixtures.
