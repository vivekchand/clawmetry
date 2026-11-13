# Setup file previews

## Problem and evidence

The Setup browser treats image bytes as UTF-8 source. The reported screenshot
shows `imagegen/assets/imagegen.png` as replacement characters. People reviewing
their agent's setup cannot inspect that asset or tell whether the file is broken.

## Required behavior

- A complete, supported local image appears as an image with its name and size.
- The viewer can save that image's original bytes.
- Text files remain readable source, with truncation stated visibly.
- Binary files, corrupt images and oversized images have a clear fallback;
  their decoded bytes never appear as text.
- Hosted Setup keeps its encrypted, runtime-scoped inventory. When an image's
  original bytes are absent from the existing synced text snapshot, it explains
  that the image must be opened on the agent machine instead of showing source
  or corrupt characters.
- Existing entitlement checks, registered roots and node/key invalidation apply.
- Browsing adds no polling or background requests.

## Scope and alternatives

This fixes preview behavior in Setup and the existing Memory/Skills browser.
It adds no file writes, arbitrary filesystem browser, document execution, image
editing, dependency, or bulk image sync. Hiding every image would remove useful
local inspection. Shipping arbitrary assets in cloud snapshots would expand
the data and bandwidth contract, so it remains outside this bug fix.

## Design and risks

`clawmetry/runtime_memory.py` supplies bounded image data in an additive JSON
field and leaves binary text empty. `clawmetry/static/js/setup.js` renders only
an explicit image MIME allowlist inside an image element; SVG contents are
never inserted as markup. `clawmetry/static/js/app.js` shares the preview for
non-text runtime files. `clawmetry/static/css/dashboard.css` bounds the two panes.

Risks are corrupt or unsupported browser image formats, older node payloads,
truncated files, selection races and active file contents. Fallbacks, bounded
reads, escaping, data-URL validation and regression tests cover those cases.
The synced text schema and daemon cadence do not change. Revert the feature PR
to undo the viewer changes; there is no migration or stored-data rewrite.

## Verification

Tests exercise image byte preservation, text/binary classification, truncation,
root traversal, escaped markup, rejected URLs, damaged-image fallback, cloud
image fallback, shared viewers and stale selections. Run the same guards on
the unmodified baseline to prove they catch the reported behavior. Release
verification must inspect the published wheel and served assets and open the
real Setup tab after deployment.
