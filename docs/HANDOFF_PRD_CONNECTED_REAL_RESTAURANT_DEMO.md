# PRD: Connected real-restaurant demonstration

Status: Gate A implemented and verified locally, including the approved four-source amendment. Gate B publication, deployment and fresh recording are not yet authorized.
Prepared: 20 October 2026, Asia/Kuala_Lumpur.

## Gate A checkpoint — 20 October 2026

The owner approved Gate A, then explicitly chose a separate four-real-source demo generation after the ten-document plan exceeded the chunk cap. Local implementation and focused offline verification are complete. No publication, AWS operation, corpus activation, live application inference or recording has occurred under this approval. See section 9 for results and the concrete Gate B proposal.

The native font dependency (`fonttools` 4.67.0) resolves the inspected font extraction issue. Explicit RM currency evidence was inspected on the restaurant-linked ordering pages; those pages establish currency only, not the dine-in menu prices. The menu originals remain byte-identical to the hashes below.

The offline source preparation reached the existing generation guard and correctly rejected **51 chunks**. Actual counts:

| Sources | Chunks |
|---|---:|
| Original six fixture documents | 14 |
| Natalina original menu | 7 |
| Natalina captured booking-page snapshot | 12 |
| Nero Nero original menu | 6 |
| Nero Nero captured booking-page snapshot | 12 |
| Total | 51 |

The initial ten-document attempt was rejected before producing a manifest. The revised, validated four-source catalog, unchanged PDFs, labelled snapshots, manifest and receipts are isolated under the API's ignored `.generated/real-restaurants-only-20261020-v2/corpus/` directory. Its native-record and complete-policy assertions have passed.

Approved amendment: use a separate active demo generation containing only the four real-source documents (**37 chunks**), preserving the original six fixture files and their existing generation for regression checks and compatible rollback. This supersedes the original ten-document active-generation proposal throughout this PRD. The document cap remains six and the chunk cap remains 48.

Pending: Gate B approval, fresh access/deployment checks, publication/activation, live acceptance/ScreenPolish recording and final MP4. Preserve `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md` and the earlier media deliverable.

## 1. Outcome and audience

Produce a credible LinkedIn portfolio demonstration for technical peers in which one conversation discovers two real Italian restaurants in Kuala Lumpur, compares the same dish at those restaurants, asks a contextual price/policy question, and handles an unsupported question. All source inspections must concern those same restaurants.

The owner confirmed Kuala Lumpur and Italian restaurants. The owner wants a fresh recording using ScreenPolish itself, showing only the chatbot interface, without any audio. Zoom into typing, zoom out after sending and while waiting, then zoom into the result or inspected source. Accelerate waiting where necessary. Let the interactions determine duration. The assistant handles preparation, recording, editing and delivery; the owner posts to LinkedIn.

The previous narrated/diagram-based video is superseded as the intended format. Preserve its files as a separate earlier deliverable. Gate A and the four-source amendment authorize local implementation only; paid requests, corpus publication and deployment require Gate B approval.

## 2. Verified starting point

Repository: `yukangzhen/restaurant-finder`, current local branch `feat/document-multipart-rollout`, HEAD `b76ba9a`. At inspection the only pre-existing untracked file was `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`; preserve it.

The accepted deployment record identifies Runtime/DEFAULT 22, hybrid retrieval, multipart and follow-ups. This is historical evidence, not a fresh AWS readiness check. The local UI returned HTTP 200 at `http://127.0.0.1:8010/` during this assessment. No chatbot request or AWS operation was performed during assessment.

ScreenPolish is already installed at `C:/Users/kinoc/AppData/Local/Programs/ScreenPolish/ScreenPolish.exe`; its packaged metadata reports 0.3.0. Its installed CLI implements recording and export, including `record start --no-system --fps 30`. Existing recordings/settings belong to the owner. No installation, upgrade or recording has been performed for this revision.

### Why uploading documents alone is insufficient

- `CorpusSpec.fictional` currently accepts only `True`. The packaged catalog contains three fictional venues.
- Restaurant IDs use the internal `demo-...` namespace across existing contracts. A namespace migration is unnecessary for this portfolio change; do not equate an internal demo ID with a fictional public identity.
- Jev instructions, the Bedrock router prompt/context and several answer/clarification templates describe every venue as fictional.
- The native menu validator expects a title/price sentence such as `RM32 per serving.` Real menus use price columns, descriptions and page-level charge notes.
- The importer allows 10 PDF pages, rejects any page without extracted text, and the UI citation contract also caps page numbers at 10.
- The corpus allows six documents. Retaining the existing six fixtures and adding two menus plus two booking snapshots requires ten documents, or another explicitly reviewed isolation strategy.
- Approved document context comes from document answers. Web discovery does not automatically establish trusted document targets or ingest returned websites.
- The existing policy validator expects a particular Markdown section heading. Real booking pages have different headings and additional conditions.

## 3. Selected source candidates and actual observations

Approved venues: **Natalina Italian Kitchen** and **Nero Nero Kuala Lumpur**. Gate A approval selected this pair and the coverage-limited D1 query.

### Official source chain

| Venue | Restaurant website | Restaurant-linked menu | Restaurant-linked booking page |
|---|---|---|---|
| Natalina | https://www.natalinakl.com/ | https://www.natalinakl.com/s/NAT_SUMMER_MENU_A4_AUG-2.pdf | https://www.sevenrooms.com/explore/natalina/reservations/create/search/ |
| Nero Nero KL | https://www.neronerokl.com/ | https://www.neronerokl.com/s/NERONERO_KL_MENU_UPDATED_MAR.pdf | https://www.sevenrooms.com/explore/neronerokualalumpur/reservations/create/search/ |

The original menus were downloaded through those website links and visually inspected with Poppler. Natalina's menu is 7 pages / 3,109,056 bytes, SHA256 `9dbf4d8e111c1eff5396bfeb5eb9202c4f6b6909af64a86f8b2b606d28290e01`. Nero Nero's is 11 pages / 2,541,699 bytes, SHA256 `47d768800d2b1ff884349c0de431ebf643c8b254b6fa055f1c2a620a7a7e2471`.

Margherita is present on Natalina PDF page 6 with listed number 48, and Nero Nero PDF page 9 with listed number 39. Both inspected pages state 10% service charge and 6% SST. Do not describe these as tax-inclusive totals, equal-size portions, guaranteed current prices or dietary-safety guarantees. Establish explicit currency provenance during Gate A before enabling monetary arithmetic; the parser must not guess currency or a per-serving unit from a bare number.

Both restaurants' public booking dialogs were opened without selecting a table or submitting a reservation. Their cancellation-charge sections describe a 24-hour notice threshold, a late/no-show charge of RM25 per person, and treatment of date changes after the deadline as late cancellations. The separate deposit paragraph uses a more-than-24-hour refund condition. Preserve those distinctions: no-charge and deposit refund are not interchangeable claims, and per-person fees must never become per-booking fees.

Native pypdf extraction of Natalina raised missing `fontTools` warnings and produced unreliable text. Visual readability does not establish ingestion compatibility. Nero Nero has decorative pages and an 11-page original. Extraction and complete-record support remain implementation work.

Assessment material is isolated in `tmp/real-restaurant-feasibility-20261020/`: original PDFs, hashes/resolved URLs, rendered pages, and read-only booking-dialog snapshots. These are source-research artifacts, not an activated corpus. No restaurant booking or communication was made.

## 4. Proposed connected conversation

### D1 — coverage-aware discovery

`Find two Italian restaurants in Kuala Lumpur that have menus in your document collection.`

This explicit condition matters. An unrestricted web search might return venues with no document coverage. The answer must select Natalina and Nero Nero from verified active document coverage and use the existing external search path to obtain available online information for those identities. Do not pretend the shortlist represents every Italian restaurant in the city or is an objective best-of ranking.

The implementation must join the active catalog to validated search results by venue identity/location. Do not replace actual search with canned recommendations, fabricate ratings, or allow web search to silently replace missing document evidence. If online verification fails, report it honestly; a recording failure consumes that request slot.

### D2 — compare those same venues

`Compare Margherita prices at Natalina and Nero Nero. Show the sources.`

Type the names returned in D1 explicitly. This avoids claiming a new generic search-to-document pronoun resolver. Retrieve the original menus, preserve the complete relevant item descriptions and applicable charge notes, then open each original PDF at its cited page. If verified currency/price basis permits arithmetic, compare listed item amounts only; do not infer serving sizes or the final payable bill. The source numbers differ by 9, but the expected monetary statement is not locked until currency provenance and native extraction pass Gate A.

### D3 — contextual multipart follow-up

`What about both restaurants' prices and cancellation policies?`

Reuse the approved D2 restaurant pair and Margherita item. Retrieve fresh evidence for four tasks, with the existing maximum concurrency of two. Show each price source and each captured booking-policy source. Retain the complete cancellation-charge block, including the notice boundary, per-person charge, no-show rule and post-deadline date-change clause. Do not assert a deposit-refund rule unless its own supporting passage is included and validated.

### D4 — evidence boundary

`According to Natalina's documents, is valet parking available?`

Gate A must verify that the selected corpus does not answer this question. The required result is insufficient evidence without unrelated citations or a web-search substitute. It must not claim that the restaurant has no valet service. If the documents actually answer the question, choose another genuinely unsupported question in the reviewed final script before requesting the live allowance; do not change it silently during recording.

## 5. Minimal implementation scope

### A. Real source identity and provenance

1. Add explicit venue/source provenance so fictional fixtures and real official-source snapshots are distinguished in contracts, fingerprints and display text. Keep internal IDs stable and retain all existing fixture identities.
2. Preserve validation and fingerprints for already published manifests. Introduce a versioned extension if new metadata changes the canonical fingerprint; do not reinterpret an old generation as a new one or rewrite its stored contents.
3. Following the approved amendment, prepare a separate generation of four real-source documents. Retain the original six fixture documents and generation separately. Keep the six-document and 48-chunk ceilings.
4. Keep downloaded menu bytes unchanged. Store exact origin/resolved URL, retrieval time, source hash and document version. Keep research/full third-party source bytes out of Git publication by default; deployment sources remain private corpus assets.
5. Booking pages have no restaurant-issued PDF. Create faithfully labelled Markdown snapshots of their actual visible text, retaining original headings, source URL and capture date. Clearly call these captured booking-page snapshots, not original restaurant-issued documents. Preserve native menu originals and provide source-page links for policy verification.

### B. Native PDF ingestion and record validation

1. Add the narrow dependency needed for reliable native font extraction and update only the relevant dependency/lock inputs. Do not use model-generated transcriptions as original evidence.
2. Raise the PDF/page-reference limit consistently to 12 across importer, citation contract, UI/source reader and relevant checks. Retain the 5-MiB and extracted-character bounds. This covers the inspected 11-page original.
3. Handle decorative/blank pages without renumbering original pages. Do not accept an image-only menu as successfully extracted; required menu records must be recovered from actual native text and checked against rendered originals.
4. Add bounded native menu-record support for the inspected layouts: title, adjacent listed amount, full description and page-level charge context. Keep menu category in identity where names repeat, such as Burrata appearing as both a starter and a pizza.
5. Keep quoted evidence tied to original verified passages. Trusted metadata/normalization may aid lookup but must not be presented as a verbatim restaurant quote. Reject adjacent-row prices, ambiguous category matches, missing conditions and unsupported layouts.
6. Distinguish a listed item amount from explicit per-serving/per-piece units. No currency/portion/tax inference. Retain legacy controlled-format validation and arithmetic unchanged.

### C. Coverage-aware discovery and routing

1. Provide bounded real venue metadata for Kuala Lumpur / Italian cuisine and derive available menu coverage from the active manifest.
2. Add the D1 coverage-aware discovery operation to the normal approved workflow. It may use a dedicated helper/node and the existing restaurant-data search integration; avoid a general new planner or new external provider.
3. Validate the final discovered identities against active coverage. The model must not invent document availability or substitute an unsupported venue. Discovered results and subsequent explicit names must match.
4. Resolve the routing conflict: a discovery request mentioning document coverage must reach discovery rather than being treated as an ambiguous menu question. Keep Jev, the Bedrock fallback, input moderation, tool budgets, final approval and approved-memory rules intact.
5. Supply the same catalog semantics to Jev and Bedrock. Remove hardcoded all-fictional descriptions from real-source answers without changing truthful fixture labels. If a managed Bedrock prompt needs a new immutable version, include it explicitly in the later publication review.
6. Continue admitting D2 by exact registered venue aliases. D3 uses the existing approved document-context mechanism; do not infer trusted document state from free-form search answer prose.

### D. Policy evidence and UI

1. Support the verified booking-section headings in captured snapshots while retaining old fixture headings.
2. Validate the full cancellation-charge block as source evidence. Keep no-show and date-change qualifiers; avoid partial snippets that imply every cancellation is free or that the charge is per booking.
3. Keep original PDF citation opens intact and correctly page-targeted. Policy citations show clearly labelled captured snapshots with original website links and capture date.
4. Keep the visible interface focused on the conversation and source viewer. No new dashboard, narration, architecture graphics, promotional overlays or unrelated feature work.

## 6. Observable acceptance criteria

| ID | Required observation |
|---|---|
| AC1 | D1 returns only the two supported real venues and honestly identifies the coverage-limited shortlist; actual search result provenance is retained. |
| AC2 | D2 uses those exact venues and real original menus; no fictional restaurant is substituted. |
| AC3 | Margherita amount, item boundary, category and description match the visually inspected native records. Currency/basis and all arithmetic are supported, or arithmetic is withheld. |
| AC4 | Charge notes remain available with the answer/source context; no equal-portion or final-bill claim is invented. |
| AC5 | D3 reuses approved targets/item, retrieves four fresh tasks with at most two workers, and retains the full supported cancellation-charge conditions. |
| AC6 | Each cited menu opens the byte-identical original at the correct page; policy snapshots are plainly labelled and trace to the restaurant-linked booking pages. |
| AC7 | Genuine missing evidence produces a non-answer without unrelated citations, a negative amenity claim or web substitution. |
| AC8 | Existing manifest fingerprints, fictional corpus behavior, source-integrity rejection, moderation and context-ownership boundaries remain valid. |
| AC9 | A focused offline verification set covers native layout extraction, decorative pages/page numbering, wrong adjacent price, duplicate dish categories, unsupported currency/unit inference, policy qualifiers, coverage/identity mismatch and the four-turn sequence. Offline runs make no external calls. |
| AC10 | Final recording is fresh ScreenPolish footage only, with readable typing/results zooms, full-interface waiting views, necessary wait acceleration and no audible or embedded audio track. |
| AC11 | No prerecorded/fabricated result substitutes for a failed fresh response; recording and request counts are durable. |

## 7. Execution and authorization gates

### Gate A — approved local work, now verified

Approval selects Natalina/Nero Nero and the D1 coverage-limited query, and authorizes the scoped local implementation, local source preparation, dependency changes and focused offline tests/verification described above. Produce reviewable diffs, a dry-run corpus/chunk plan, source provenance and criterion results. Do not publish Git changes, activate a corpus, modify AWS, start a paid application request or record the application under Gate A. Preserve unrelated files and the existing UI/service.

Stop and report if the native records/currency cannot be verified, the real sources change materially, or the change needs broader OCR, a general table parser, expanded task criteria or increased chunk/provider budgets. The purpose is a convincing demo, not a general restaurant ingestion platform.

### Gate B — prepare after Gate A, then obtain a separate concrete approval

Review exact changed paths, source-generation fingerprint, embedding/chunk counts, any managed prompt version changes, candidate image contents, UI changes and rollback state. Then request a bounded approval covering only the necessary publication/deployment/corpus activation and fresh recording requests. No external mutation is pre-authorized by this PRD.

The proposed later envelope is one reviewed image and Runtime rollout, one staged corpus generation/pointer publication, required prompt synchronization, at most the calculated embedding allowance (never more than 48 attempts without another decision), and four application sends total. The four sends are the recording and acceptance run together, not four rehearsals plus four takes. Failed/uncertain sends consume their slots; no automatic retries. Up to eight source opens and no downloads are planned. Final numbers must be established from Gate A rather than guessed.

Record the existing Runtime image/configuration and active pointer before changes. Keep old generations/images available. Any rollback must restore a compatible image/catalog/prompt/corpus combination; do not restore only one half of that pairing. Review the exact rollback steps before approval. No Docker restart/reset, IAM redesign, resource deletion or credential rewrite is included.

### Gate C — local ScreenPolish production, within the approved recording envelope

1. Inspect the installed application's recording status and preserve existing owner projects. Use 0.3.0 if it passes a short capture/export check on a harmless local page with zero chatbot sends. A required upgrade is a separate decision.
2. Capture only an owned browser's chatbot viewport. Disable microphone, system audio, webcam, music and click/zoom sound effects. Exclude address bars, taskbar and unrelated windows/notifications.
3. Create a new conversation. Submit D1–D4 exactly once in order, opening the associated sources between turns. Stop dependent sends on incorrect, incomplete or uncertain outcomes.
4. Use ScreenPolish's editable zoom segments: focus typing, pull out on send, keep the full chat visible during accelerated waiting, focus the completed result, and focus the selected source when verifying it. Keep source text and answers unaltered. Do not assume automatic click zoom alone follows the desired answer focus.
5. Let the interaction determine duration. Shorten dead time with speed changes; preserve enough full-interface context to understand the wait. Disclose time compression in the accompanying LinkedIn text, not with added video overlays.
6. Export a landscape 1080p MP4. If the exporter leaves an empty audio stream despite audio being disabled, remove that stream with a lossless remux; ScreenPolish remains the recording/editing/export tool.
7. Inspect actual decoded export frames at typing/send/result/source transitions. Verify no missing panels, incorrect focus, private identifiers, audio track or reused earlier answer. Deliver the final silent MP4 and concise posting text. Do not post to LinkedIn.

## 8. Remaining decisions and limits

- Gate A venue selection, local implementation, currency provenance, native extraction and the 37-chunk dry run are complete.
- The first discovery prompt is deliberately limited to venues with available document coverage. General arbitrary web-result ingestion is out of scope.
- No cost/latency, restaurant ranking, live table availability or production-readiness claims are included.
- AWS publication, paid application requests, ScreenPolish capture/export and deployed UI verification remain unperformed for this revision. Offline results do not establish live service readiness.

## 9. Gate A closeout and concrete Gate B review

### Prepared result

- New generation: `f520ceb003e1308ac170d94b98d50e4ee031e998d9306f8d62fa6a8a7b172781`.
- Four sources; 37 chunks; 17,740 extracted chunk characters. The existing ingestion CLI independently reports the same dry-run fingerprint and maximum 37 embedding attempts. No source was activated.
- Original fixture generation remains `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a`; the six fixture files are unchanged.
- Margherita is recovered from the actual native PDFs at Natalina page 6 / listed MYR48 and Nero Nero page 9 / listed MYR39. Both source descriptions and charge notes are preserved. The supported difference is RM9 between listed items; it is not a portion-size or final-bill comparison.
- Each captured cancellation section is 328 canonical characters, retains its full charge conditions, and is kept separate from the deposit/refund section. The Natalina corpus has no valet mention.
- The new manifest schema fingerprints real venue identity, source/currency provenance, reviewed row boundaries and the font decoder. Published schema-1 identities retain their old canonical encoding.
- The known native spelling is added to keyword lookup only; stored source text, selected quotes and original PDF bytes are unchanged. This resolves the inspected split-word extraction without introducing OCR.
- Only reviewed native rows and the complete captured policy block use deterministic selection. Generic document questions still use the existing selector; Jev and the Bedrock fallback still handle ordinary routing. Discovery has a bounded server route because document-coverage mentions otherwise conflict with document-question routing.
- The opt-in `DOCUMENT_REAL_SOURCES_ENABLED` is false by default. CDK accepts only exact boolean forms, and toggling it changes only its runtime environment leaf.
- The source viewer supports page references through 12. Booking snapshots show their capture time, a truthful snapshot label and an original SevenRooms link derived from verified source bytes.
- Private original PDFs, full captured policies and generated corpus evidence remain ignored by Git and are explicitly excluded from the image context. No private source bytes are needed in the runtime image.

### Verification and limits

| Check | Observed result |
|---|---|
| New source/sequence tests | 17 passed, including authored synthetic native PDFs, category ambiguity, split spelling, wrong price, incomplete policy, currency proof, routing/fallback, uncertain-send accounting and parent moderation |
| Existing document regressions | 218 passed |
| Existing router regressions | 9 passed |
| UI regressions | 52 passed on isolated rerun |
| CDK document tests | 57 passed |
| TypeScript compilation | `tsc --noEmit` passed |
| Whitespace review | `git diff --check` passed |
| Actual originals through production graph and hybrid ranking | Four connected turns and a blocked-comparison variant passed offline |

The actual-original sequence used the real extracted chunks and production scope/ranking/validation/approval code, with simulated online search, semantic vectors, embeddings, planner, moderation, memory and unsupported-answer selection. It does not establish live semantic recall, routing accuracy, cloud readiness, latency or cost savings. No AWS clients or live application sends were allowed in those checks.

One full UI run failed the existing 1-ms timeout test before its first background read began; the isolated 52-test rerun passed without changing that test or application timeout. Preserve the transient failure as a validation limitation. The regression suite also deliberately prints failing evaluation-canary results while verifying that those failures are detected; its unittest exit status is the test result.

Criterion status: AC1–AC9 have local implementation/offline evidence only. Their live portions, including actual search and deployed source opens, remain pending. AC10–AC11 are NOT_STARTED. The final demo is not yet complete.

Private receipts under `restaurant-finder-api/.generated/real-restaurants-only-20261020-v2/`: `corpus/report.json`, `corpus/manifest.json`, `corpus/offline-sequence-check.json`, and `reviewed-paths.json`. Preserve research originals under the task's `tmp/real-restaurant-feasibility-20261020/` folder. These are deployment inputs/evidence, not Git publication targets.

### Gate B requested envelope — approval required

Publication makes code/history visible on GitHub and cannot retract copies others obtain. ECR storage/transfer, corpus embeddings, search and the four live turns can incur ordinary charges. Rollback restores service state but cannot undo publication or charges. No LinkedIn posting is included.

Approval would authorize the following steps, in order, without another approval for a conforming change set:

1. **Freeze the reviewed inputs.** Verify HEAD `b76ba9a`, the exact section-9 path list and its current hashes, four source hashes, generation fingerprint and the unchanged owner file. Keep credentials/configuration private. Do not include `HANDOFF_PRD_RUNTIME_WARNINGS.md`, full restaurant sources, generated evidence, earlier media or unrelated changes in Git.
2. **Establish fresh read-only readiness.** Check GitHub access, AWS default-profile identity/account/region, stable stack/Runtime/DEFAULT, the active pointer, pinned prompts, ECR retention and Docker health with bounded commands. Historical READY Runtime 22 and OCI index `sha256:231cff888cf55d92296ac4d9d8ab96b9956b00767743cd96242dca0e091c6eb9` are expectations, not fresh facts. Capture exact fresh rollback configuration. Stop on unexplained drift, expired access, inadequate retention or an unhealthy engine. No restart/reset is authorized.
3. **Check ScreenPolish before spending live slots.** Inspect installed version/status and owner recordings. Make one short silent capture/export of a harmless local page, with no chatbot send. Verify editable typing/result zooms, waiting-speed changes and a 1080p export. Preserve owner projects/settings. Stop if the installed tool cannot meet the format; an upgrade or substitute needs a decision.
4. **Publish the reviewed local change.** Commit/push only the exact paths below to the existing development branch/draft PR. Inspect automatic offline CI; do not dispatch deployment/destruction workflows, merge, force-push or change account credentials. Only a conforming pass proceeds.
5. **Synchronize the one changed router prompt.** Back up the local nine-prompt manifest. Read and compare the eight unchanged definitions before synchronization; stop if another prompt differs. Reuse an already matching immutable ROUTER_PROMPT version or create at most one matching numbered version, then read it back. The existing `sync_prompts` command may enumerate all nine; only the changed router definition may be updated. Preserve old numbered versions and validate the new packaged manifest. Do not guess its version number or disable production manifest checks.
6. **Build/audit/push one ARM64 image.** Stage a clean build context containing the reviewed API sources/dependency lock and sole new prompt manifest. Exclude credentials, other generated evidence, originals, sample fixtures, tests and media. Build once, audit file inventory, architecture, source/dependency hashes and immutable prompt bindings, then make one intended push under a fresh unique tag. No automatic rebuild/re-push, tag overwrite, pruning or Docker recovery. An uncertain upload is reconciled through read-only registry checks before any new decision.
7. **Apply one narrow Runtime update.** Derive the proposal from the freshly captured deployed template. Change only the container URI to the verified candidate and set `DOCUMENT_REAL_SOURCES_ENABLED=true`; preserve hybrid mode, multipart/follow-ups, guardrail pair, IAM, other environment values, resources and outputs. Review the change set: one Runtime modification, no replacement. Execute once and require UPDATE_COMPLETE plus matching READY Runtime/DEFAULT. Do not predict the resulting version.
8. **Publish the private corpus once, pointer last.** The candidate reader supports the old corpus, so update the image before changing the pointer. Recompute and require the exact fingerprint above. Use the existing `ingest_documents --publish` path with the fresh verified bucket/index, `--max-embedding-attempts 37` and this prepared `corpus.json`. Allow at most 37 ingestion embedding attempts and one 37-record vector publication. Verify originals, chunks, vectors and manifest before the conditional active-pointer switch. No deletes or automatic second publication. Failure before pointer switch leaves the old corpus active.
9. **Update the owned local UI.** Reuse the owned localhost UI if it already runs the reviewed source-viewer code; otherwise allow one necessary owned restart. Preserve its credential/configuration values, show no private identifiers, and verify the served code/config without making an inference request. Do not stop unrelated apps.
10. **Record and accept the four fresh turns together.** Create one new conversation and capture D1–D4 exactly once in order with ScreenPolish, using the section-4 wording. Reserve each slot durably before send. Failed or uncertain sends consume a slot; there are no warm-ups, standalone model/guardrail checks, live benchmarks, rehearsals or automatic retries. Expected workflow bounds are two external searches in D1, two query embeddings in D2, four in D3 and one in D4, with the existing provider bounds/fallbacks inside those four turns. The 37-attempt allowance applies to ingestion, not these seven query embeddings.
11. **Inspect sources within eight opens and zero downloads.** Open the two D2 PDFs at pages 6 and 9; D3 opens its two menus and two captured policies (six total). Up to two additional public booking-page opens may verify the snapshots' origin links. Preserve the association with each answer, complete item/charge context, and all cancellation qualifiers. Stop dependent sends on a wrong venue, missing source, failed moderation, incomplete answer or uncertain result. Do not substitute old footage or canned answers.
12. **Inspect bounded evidence.** Use one initial and at most one delayed read of known request/trace groups, at most ten log pages per group total, to reconcile the four reserved sends and task/moderation boundaries. Read-only polling is bounded to 15 minutes per cloud readiness stage. Do not issue extra inference to obtain traces. Report any trace gap instead of inventing evidence.
13. **If acceptance fails, permit one compatible rollback.** Pause the owned demo UI/sends. Restore the retained old pointer while the candidate image still supports schema 1; verify originals/chunks/vectors without embeddings. Only then restore the fresh baseline Runtime template/image/environment and owned UI code, retaining old immutable prompt bindings. Review one no-replacement rollback change set before execution. If pointer restoration fails, do not put an old image against the new schema-2 corpus; stop for a recovery decision. Preserve all generations/images and failure evidence. No post-rollback inference is included.
14. **Finish the local video and deliver.** Keep only chatbot/source-viewer footage. In ScreenPolish, zoom into typing, pull out at send/wait, accelerate dead time and zoom into completed answers/sources. No audio, overlays, narration or title/architecture scenes. Export a new landscape 1080p MP4, verify decoded frames at focus transitions and absence of any audio track, and retain the editable project/raw evidence. A lossless audio-track removal is permitted if required after ScreenPolish export. Deliver the final video and concise LinkedIn posting text disclosing time compression, upstream attribution and the bounded demo scope. The owner posts it. Record results here; a documentation-only closeout may update this same PRD without another image build.

This authorization does not cover additional billable sends, expanded source/task budgets, Docker restarts, IAM/guardrail changes, deletions, broad repository changes, a ScreenPolish upgrade, paid media services or LinkedIn publication. Material deviations return for a focused decision.


### Exact Git publication paths (38)

Only these repository-relative paths are in the publication envelope. Full contents are reviewable locally; the private receipt records their SHA256 values.

```text
docs/HANDOFF_PRD_CONNECTED_REAL_RESTAURANT_DEMO.md
restaurant-finder-api/.dockerignore
restaurant-finder-api/.env.example
restaurant-finder-api/pyproject.toml
restaurant-finder-api/src/application/document_rag/comparison.py
restaurant-finder-api/src/application/document_rag/comparison_workflow.py
restaurant-finder-api/src/application/document_rag/conversation.py
restaurant-finder-api/src/application/document_rag/discovery.py
restaurant-finder-api/src/application/document_rag/ingestion.py
restaurant-finder-api/src/application/document_rag/multipart.py
restaurant-finder-api/src/application/document_rag/multipart_workflow.py
restaurant-finder-api/src/application/document_rag/native_menu.py
restaurant-finder-api/src/application/document_rag/retrieval.py
restaurant-finder-api/src/application/document_rag/single_record.py
restaurant-finder-api/src/application/document_rag/workflow.py
restaurant-finder-api/src/application/orchestrator/streaming.py
restaurant-finder-api/src/application/orchestrator/workflow/edges.py
restaurant-finder-api/src/application/orchestrator/workflow/graph.py
restaurant-finder-api/src/application/orchestrator/workflow/nodes.py
restaurant-finder-api/src/application/orchestrator/workflow/state.py
restaurant-finder-api/src/config.py
restaurant-finder-api/src/deployment/prepare_real_demo.py
restaurant-finder-api/src/domain/document_comparison.py
restaurant-finder-api/src/domain/document_rag.py
restaurant-finder-api/src/domain/prompts.py
restaurant-finder-api/src/domain/real_restaurant_catalog.json
restaurant-finder-api/src/evaluation/document_multipart.py
restaurant-finder-api/src/infrastructure/document_parser.py
restaurant-finder-api/src/infrastructure/jev_router.py
restaurant-finder-api/tests/test_document_citations.py
restaurant-finder-api/tests/test_document_rag_ingestion.py
restaurant-finder-api/tests/test_real_document_sources.py
restaurant-finder-api/uv.lock
restaurant-finder-infra/bin/cdk.ts
restaurant-finder-infra/lib/stacks/agentcore-stack.ts
restaurant-finder-infra/test/document-rag.test.ts
restaurant-finder-ui/source_documents.py
restaurant-finder-ui/tests/test_source_documents.py
```

## 10. Executed Gate B result — 20 October 2026

**The final demo was not produced.** The first live discovery answer failed acceptance; dependent queries stopped and the approved compatible rollback completed. The recording tool itself passed its capability check.

### Completed and verified

- Published the 38 approved paths as commit `c7edf7572c463b9238b9f3b3a5b3adf79a819d4d` to the existing draft PR. Both automatic offline CI runs passed: push `39366245031` and PR `39366247730`.
- ScreenPolish 0.3.0 captured the owned browser window and exported actual 1920×1080, 30-fps footage with no audio stream, manual typing/result zooms, a wide waiting view and a 4× speed region. Source isolation was verified from decoded frames. The user selected Window and clicked Record because the Windows control helper could read accessibility text but could not capture geometry or operate the buttons.
- The initial desktop-source probe failed isolation and was retained privately without publication. The user separately approved the successful window-specific recovery check. The probe's first export used stale in-memory defaults; leaving the editor for Library and reopening the saved project made native export honor its edits. Use that reload procedure for future exports.
- Created ROUTER_PROMPT version 4 and reused the other eight immutable versions. The local backup unexpectedly contained eight entries; comparison with the retained deployed image established all nine deployed bindings and confirmed that only the router changed. No second synchronization was performed.
- Built once and pushed once: `real-docs-c7edf75-20261020035245-arm64`, index `sha256:6bb97db225684e6de86d368f9af58411c1c46a47b5ee7849b04dfb9ce87323f1`. Audited Linux ARM64, UID 1000, 90 expected packaged files, FontTools 4.67.0 and the nine immutable prompts. The agent was not started during that audit. Clean-context preparation first hit Windows' path-length limit before any build; the actual single build used a shorter task-owned path.
- One reviewed CloudFormation modification changed only the Runtime image URI and real-source flag. Runtime/DEFAULT reached READY version 23, with unchanged resource identities, outputs, other environment values and guardrails.
- Activated the four-source generation above: 37 chunks, 31 embedding attempts, 4,380 embedding tokens, six cache hits and one 37-vector publication. Verified all four stored original byte hashes before the conditional pointer switch and again afterward.
- Restarted only the owned UI, preserving its environment and generated appearance configuration. The saved launch alias and recorded base interpreter lacked Chainlit; the existing UI virtual environment had the matching Chainlit 2.12.0 and was used to complete the launch. The launcher result pipe remained open, so the actual listener, source hashes and configuration were independently verified. No dependency installation was required.

### Fresh recording and verified failure

- The fresh native recording targeted only `Restaurant Finder demo recording`, at 1920×1080, with microphone, webcam and system audio disabled. Decoded its initial frame before using a live slot.
- Consumed **one application send: D1**. D2–D4 remain unused. Source opens: zero. Downloads: zero. No rehearsal or retry was sent.
- Actual D1 answer: “The collection has menu-covered venues, but I couldn't verify their official websites through online search. I cannot present them as successfully discovered online.”
- The two captured MCP tool results both succeeded with `google_local` data. Natalina's result contained one restaurant; the other result contained four, including Nero Nero. Every supplied `website` was a Google `/searchviewer/10` place link, with no embedded official-site redirect target, and neither result contained organic `web_sources`.
- The existing Lambda `_parse_local_results` uses `result.get("website", result.get("link", ""))`. Its organic fallback runs only when no local restaurants are returned. Consequently, place results prevented organic search while their Google links could not satisfy the discovery step's official-domain check. **Keep that official-domain check; accepting these links would misrepresent the evidence.** The diagnosis comes from the already captured actual results, not another search.
- Separately, the new recording controller initially mistook the “LLMs can make mistakes” footer for an answer. The actual application response was inspected separately and also failed acceptance. Future recording must exclude the watermark and wait for a real completed assistant message.
- Preserved the failed take and private evidence. No finished demo MP4, replacement result or success claim was produced.
- Initial traces established two discovery tool calls and an approved parent output guardrail. An initial runtime-group result could not be saved because its filename exceeded the Windows path limit; the single delayed log read timed out. Those gaps are retained. No additional read phase or inference was used to fill them.

### Compatible rollback and current state

1. Stopped the recording, closed the owned capture browser and paused only the verified owned UI.
2. Restored fixture generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` while the candidate still supported schema 1. Verified its six originals, chunks and stored vectors. Rollback used zero embedding attempts and zero vector writes.
3. Reviewed and executed one no-replacement Runtime rollback change set. Runtime/DEFAULT reached **READY version 24**, using the previous `single-record-0ec71ad-20261019071344-arm64` image and exact baseline environment/template. The version number increased because rollback creates a new Runtime version.
4. Restored the previous owned UI's `app.py` and source viewer, verified against baseline commit `b76ba9a`, with the original connection/identity configuration. Localhost is healthy. No post-rollback application inference was made.
5. Restored the owner's backed-up ScreenPolish recording defaults and verified ScreenPolish is idle.

Retain the candidate image, four-source generation, prompt version 4 and old versions. Git still contains the published candidate code in the draft PR; cloud rollback does not unpublish that history. The unrelated owner file remains outside the publication envelope. Execution receipts are private under the existing generated Gate B folder. The new recording's native project is under `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_12-18-52/`.

## 11. Focused local recovery — approved and completed

The user approved **“Approve local repair and offline tests”** on 20 October 2026. This sign-off covers the local work below only. Section 12 is a new deployment/recording request and remains unapproved.

### Deliverable and reason

Finish the same four-turn, silent ScreenPolish demo for LinkedIn. Repair the observed official-website search mismatch and the capture controller's completion detection. Add no new product features, architecture layers or benchmark work.

### Local scope and success criteria

Expected product paths:

- `restaurant-finder-infra/mcp/lambda/handler.py`
- `restaurant-finder-api/src/application/document_rag/discovery.py`
- `restaurant-finder-api/tests/test_correctness_repairs.py`
- `restaurant-finder-api/tests/test_real_document_sources.py`
- This PRD for the reviewed outcome and next deployment envelope.

The existing ignored native capture helper may be corrected locally. Do not publish its private paths, profiles, trace payloads, credentials or recordings.

Local completion requires that Google place links cannot be represented as official websites; the two approved discovery searches can obtain genuine organic source URLs within existing provider bounds; the official-domain/city/document-coverage checks remain intact; ordinary restaurant search remains supported; and the controller cannot mistake the footer, empty output or a partial stream for a completed answer. All local evidence must use captured/synthetic fixtures and simulated dependencies, with no new search, model, guardrail or embedding call.

### Local execution steps

1. Preserve the captured response evidence and existing failed take. Extract minimal sanitized fixtures for a successful local result whose only link is `/searchviewer/10`; do not copy session/authentication metadata into tests or Git.
2. Remove the fallback that labels a generic result `link` as a restaurant's official `website`. Preserve usable explicitly supplied business websites, and reject the observed Google place/search-viewer links as official-site evidence. Keep organic pages represented as `web_sources`, not fabricated restaurant records.
3. For the explicit official-website lookup used by D1, use the existing organic SearchAPI path directly, or a bounded fallback when official-site evidence is missing. Choose the smallest conforming implementation after reviewing the current handler. Permit at most one attempt per selected provider path; do not introduce hidden duplicate web attempts in exception handling or enlarge the existing provider budget. Preserve ordinary local-search behavior.
4. Scope each D1 lookup to the catalog venue's validated official domain where appropriate. A `site:` constraint may narrow the query; it must still require an actual returned public URL on that domain. Never substitute the catalog URL for a missing online result or weaken `online_match`.
5. Correct the capture helper to ignore watermark/footer articles and associate the response with the submitted user message. Inspect the installed Chainlit event/DOM contract and wait for an authoritative completion signal before validating the final response and citations. Reserve each send before dispatch; failed or uncertain sends stay consumed. Do not send a live request to debug the controller.
6. Add focused offline regressions for place-link rejection, organic-source success, provider failures without duplicate attempts, unchanged ordinary search behavior, official-domain verification, and footer/partial-response rejection. Reuse the existing test modules and captured DOM/event fixtures; no additional harmless ScreenPolish capture is needed.
7. Produce the exact reviewable diff, offline results and deployment proposal. Stop for the concrete publication/deployment decision required by AGENTS.md and this PRD.

### Authorization boundary and later recording budget

Approval of this local recovery authorizes the scoped code/helper repair and focused offline tests only. **It does not authorize another Git push, Lambda update, image build/push, Runtime update, corpus switch, recording take or billable request.**

After local completion, prepare a separate exact review for the necessary Lambda code publication and Runtime rollout. Prefer reusing prompt version 4 and the retained four-source corpus; no new prompt version, corpus embedding or vector batch should be required if verified compatible. Capture the actual Lambda/Runtime rollback baseline first. Preserve IAM, gateway schema, guardrails, Docker and unrelated services unless a separately reviewed change proves necessary.

A complete replacement take needs four fresh application sends in one new conversation. One earlier send is already consumed, so that would increase the original total allowance from four to **five**. The three unused slots are not permission for diagnostic calls or a changed script. Review the new take, at most eight source opens, zero downloads, native editing/export and one conditional compatible rollback together before asking for that later approval.

Existing decisions remain: Kuala Lumpur, Italian food, Natalina/Nero Nero, four real sources, the approved D1–D4 wording, adaptive wait acceleration, silent interface/source footage, 1080p landscape and owner-only LinkedIn posting. The local recovery is complete; the open decision is section 12.

### Local execution result — 20 October 2026

- `_parse_local_results` now accepts only an explicitly supplied usable business `website`. Generic `link` values are not promoted; Google search/place/map links in `website` are rejected. Restaurant records remain available without a verified website.
- An explicit `official website` query selects the existing organic provider directly, once. Ordinary queries still try local search and, if empty or unavailable, make at most one web attempt. A web failure no longer triggers a second web attempt.
- Discovery validates each catalog website before adding its host as a `site:` constraint. The existing actual-result official-domain, city/cuisine and document-coverage checks remain in place. No result is manufactured from the query or catalog URL.
- The private recorder now correlates the outbound user message, socket and thread with a new assistant message, a final non-streaming update, and Chainlit `task_end`. It excludes watermark articles and reads the message content container, including headings/tables. Final displayed wording must match the final server wording after Markdown-format normalization; unsupported formatting fails closed. It rejects empty, placeholder, partial, unrelated, errored, duplicate and disconnected outcomes. Slot reservation still precedes dispatch. Close now releases its command input as well as the browser.
- Confirmed the installed Chainlit 2.12.0 contract from `socket.py`, `emitter.py`, `message.py` and its shipped frontend source map. Its composer sends an empty `threadId`; the recorder correlates it with the thread already observed in the welcome message on that same socket.
- **82 Python tests passed** across `tests.test_correctness_repairs` and `tests.test_real_document_sources`. An earlier 31-test focused run is a subset, not an additional 31 unique tests. The suite intentionally logs mocked provider/guardrail failures while checking safe handling; its final unittest status was OK.
- **14 private Node event tests and one headless DOM fixture passed.** The DOM test used only authored HTML in `about:blank`, blocked all network requests and observed zero requests. It verified table prices, heading content, footer/control exclusion and completion reconciliation. Syntax checking the repaired recorder passed without starting it.
- `git diff --check` passed. Exactly the five listed tracked paths changed; nothing is staged. The unrelated `HANDOFF_PRD_RUNTIME_WARNINGS.md` remains untracked and its original SHA256 is unchanged.
- The failed native take, private trace evidence and original consumed-send ledger are preserved. No new chatbot/search/model/guardrail/embedding call, recording, Git publication, Docker action or AWS mutation occurred during this recovery.

**Validation limit:** offline evidence proves the repaired control flow with simulated providers/events. SearchAPI's next actual organic results, deployed behavior, live socket capture and the final recording remain unverified. The application is still on the restored baseline; no finished demo MP4 exists.

## 12. Focused redeployment and replacement recording — executed

The user approved **“Approve section 12 rollout and recording.”** Execution and the failed acceptance/compatible rollback are recorded in section 13. Section 14 is a new proposal and remains unapproved.

### Deliverable and completion

Deliver the agreed four-turn silent chatbot/source-viewer MP4 and its editable native ScreenPolish project. Completion requires all four fresh connected turns to pass the existing acceptance criteria, six required source opens to show their actual originals, legible input/result focus transitions, compressed waiting time, landscape 1920×1080 output and no audio stream. No added system features or benchmark work is included.

Publication is externally visible and cannot retract copies. Lambda asset/ECR storage and transfer, AWS inference and SearchAPI can incur ordinary charges. A rollback restores service configuration but cannot undo publication or charges. LinkedIn posting remains the owner's action.

### Exact publication scope (five paths)

```text
docs/HANDOFF_PRD_CONNECTED_REAL_RESTAURANT_DEMO.md
restaurant-finder-api/src/application/document_rag/discovery.py
restaurant-finder-api/tests/test_correctness_repairs.py
restaurant-finder-api/tests/test_real_document_sources.py
restaurant-finder-infra/mcp/lambda/handler.py
```

Keep the current ignored helper/tests, generated receipts, sources, profiles and recordings private. Preserve the unrelated owner file. Publish these five paths only to the existing development branch/draft PR; no merge, force-push or deployment-workflow dispatch.

### Approved sequence

1. **Freeze and check readiness.** Record hashes of the five reviewed paths and repaired private helper/tests. Require current HEAD `c7edf7572c463b9238b9f3b3a5b3adf79a819d4d` before publication and unchanged owner-file hash. Establish fresh read-only GitHub/AWS identity and stable stack/Runtime/DEFAULT, current pointer, nine prompt bindings, Lambda code/configuration, retained old assets/images and Docker health. The last verified baseline was Runtime 24 with the old fixture corpus; recheck rather than assume it remains current. Save fresh rollback templates, Lambda code reference/hash, pointer/ETag and owned UI configuration privately. Stop on drift or access/engine failure. No Docker restart/reset is included.
2. **Publish and require offline CI.** Commit/push only the five paths above to PR 1. Inspect the automatic offline CI results for that exact commit; proceed only on a conforming pass. Preparation of bounded local rollout/recording helpers and private receipts is included; these are not Git publication targets.
3. **Prepare immutable artifacts once.** Reuse the existing nine-prompt manifest, including ROUTER_PROMPT version 4, after verifying all definitions/bindings match; create no prompt versions. Stage the reviewed API source in a clean short-path context, build one Linux ARM64 image, audit inventory/hashes, UID and bindings without starting the agent, and push once under a fresh unique tag. Package one Lambda asset with the reviewed `handler.py` and unchanged `tools_schema.json`/`requirements.txt`, excluding caches and evidence. Upload once to a unique content-addressed key in the existing CDK asset bucket; verify stored bytes/hash before use. Preserve the previous asset. No rebuild, repeated upload/push, tag overwrite, pruning or automatic recovery is included; reconcile uncertain results read-only before requesting any additional mutation.
4. **Review and execute one two-resource change set.** Derive it from the fresh deployed template. The only changed leaves may be the `Code.S3Key` for `restaurantFinderMcpLambda7367777D`, the Runtime container URI, and `DOCUMENT_REAL_SOURCES_ENABLED=true`. Keep the existing code bucket, Lambda handler/runtime/configuration, MCP schema, IAM, outputs, guardrail pair `ih5xpt3qi946:1` and all other environment values unchanged. Require exactly two Modify operations, both without replacement, then execute once. Require UPDATE_COMPLETE, matching Lambda code SHA256 and matching READY Runtime/DEFAULT; do not predict the new Runtime version. Do not invoke the Lambda or agent for readiness.
5. **Reactivate the retained four-source corpus.** Verify generation `f520ceb003e1308ac170d94b98d50e4ee031e998d9306f8d62fa6a8a7b172781`, its four stored original hashes, manifest, 37 chunks and existing vector records against the prepared inputs. Use a conditional pointer switch only after the new Runtime is ready. Allow zero ingestion embeddings and zero vector writes; if retained data is missing or incompatible, stop. Preserve the fixture generation and both images/assets.
6. **Restore the reviewed source viewer.** Permit one necessary restart of only the verified owned localhost UI, using the existing matching UI virtual environment and preserved connection/identity/appearance configuration. Serve the already reviewed UI code from the published candidate. Check code, listener and original-source availability without inference. Create a new private recording directory/profile/ledger and fresh readiness receipt tied to the actual deployed release, real generation and UI. Do not reuse historical PASS receipts or overwrite the failed take/ledger. Keep the known-passing installed ScreenPolish version; no extra capability recording or upgrade.
7. **Record exactly four fresh sends.** Verify the selected owned browser window is the isolated source, with microphone/webcam/system audio Off. If the control helper still cannot select it safely, request the minimum user action to select that window and click Record. Use D1–D4 exactly as approved in section 4, in one fresh conversation. Each new slot is reserved before click; failure, disconnect or uncertainty consumes it and stops dependent sends. There are no rehearsals, diagnostic sends or retries. This authorizes **four additional application sends**, making the overall total five including the earlier failed D1. D1 uses at most two organic searches; D2–D4 retain the existing seven query-embedding bound and configured model/guardrail bounds. The unused original slots do not add to these four.
8. **Inspect actual sources and bounded evidence.** Open the six required documents across D2/D3, including menu pages 6 and 9 and complete policy qualifiers. Permit up to two extra booking-origin opens, for **eight opens maximum and zero downloads**. Stop on incorrect identity, missing evidence, unsafe/unapproved output or incomplete results. For this replacement take only, allow one initial and one delayed read of known trace/request groups, at most ten pages per group total; no inference to obtain traces. Read-only readiness polling is bounded to 15 minutes per stage. Report unresolved evidence gaps.
9. **Permit one conditional compatible rollback.** On failed acceptance or incomplete deployment, pause the owned UI/sends. If the new pointer is active, restore and verify the freshly captured old corpus first, without embeddings/vector writes. Then review and execute one no-replacement change set restoring only the changed Lambda/Runtime leaves from the fresh baseline, and restore the owned UI. If the pointer cannot be restored, do not put the old Runtime against schema 2. Keep all artifacts/failure evidence. No post-rollback inference or second rollout is included.
10. **Edit, export and deliver locally.** Use native ScreenPolish editing/export with manual input/result focus, a wide waiting view, and wait acceleration where useful. Keep only interface/source-viewer footage; no audio, narration, captions, overlays or title/architecture scenes. Reload the saved native project through Library before export to avoid the previously observed stale editor settings. Export a new 1080p landscape MP4, inspect decoded focus/source frames and stream metadata, and retain raw/editable files. Lossless removal of an empty audio track is allowed if required. Deliver the file and concise optional LinkedIn text with upstream attribution and time-compression disclosure; do not post it. A documentation-only closeout in this same PRD/PR is included without another build.

**Not included:** extra application/provider checks, embeddings/vector batches, unrelated fixes, corpus/source rewrites, prompt synchronization, IAM/gateway/guardrail changes, Docker recovery, deletion, paid media tools, merging or LinkedIn publication. Any nonconforming result stops the affected step for a focused recovery decision.

## 13. Section 12 execution result — 20 October 2026

**The complete demo video was not produced.** The fresh opening answer verified one venue; the two-venue acceptance condition failed. Dependent sends stopped and the approved conditional rollback completed.

### Publication and deployment

- Published exactly the five reviewed paths as `089d0a8656bacc1185a23d82dc647dd428beaf46` to the existing draft PR. The single push succeeded; its follow-up `ls-remote` timed out. Read-only GitHub API reconciliation confirmed the exact commit, parent and five paths without another push. Automatic offline CI passed: push `39371635920`, pull request `39371638619`.
- Fresh readiness verified Runtime 24, the old corpus, the actual Lambda asset/hash, all nine immutable prompts, rollback-image retention, GitHub access, Docker and the owned UI. Saved a fresh private rollback baseline. No prompt synchronization or Docker restart occurred.
- Built once, audited and pushed once: `site-fix-089d0a8-20261020045120-arm64`, OCI index `sha256:736deb62613dce489d5126d20fd5632dfa7ec14c10f7caa211005c50c675fde8`, Linux ARM64 child `sha256:057257314711406ffc2bc51c266ac820ceec3f89d4b78b51c0fc4522edda417d`. Audit verified UID 1000, 90 exact files, FontTools 4.67.0 and the unchanged nine-prompt manifest. No agent was started for the audit.
- Uploaded one immutable Lambda asset, SHA256 `5930934e5f4e1f1563bc00b169bbec7bc0550ab39249014ba3105e8d0c96cb33`, containing only the reviewed handler and unchanged schema/requirements. Verified stored bytes before deployment.
- The basic CloudFormation change-set view conservatively listed gateway/role references in addition to the two intended resources. Execution paused. The complete `IncludePropertyValues=True` view resolved references and showed exactly two non-replacing Modify entries and the three approved property leaves; all other template resources were identical. Executed that same change set once, without expanding scope or creating a second one. AWS documents this reference-resolution precision in its [enhanced change-set announcement](https://aws.amazon.com/about-aws/whats-new/2024/04/aws-cloudformation-changesets-enhanced-change-visibility-deployments/).
- Stack reached UPDATE_COMPLETE and Runtime/DEFAULT READY version 25. Verified the new Lambda code hash, image, flag, unchanged other environment values, resource identities, outputs and guardrails.
- Reactivated the retained four-source generation after verifying all four original hashes, 37 chunks and existing vectors/query readiness. Used **zero ingestion embeddings and zero vector writes**.
- Restarted only the owned UI with its matching existing virtual environment and preserved configuration. The venv launcher spawned a child listener; read-only process/source/configuration checks resolved the initial exact-PID assertion without another restart.

### Recording controls and actual acceptance

- Preserved two zero-query takes. The first controller's stdin closed across the user handoff; replaced it with a persistent file queue that reserves command identities and never replays uncertain sends. Automatic approval review rejected a proposed Node inspector attachment because it could expose process/session memory; no debugger was enabled. Recovery used an ordinary fresh owned browser and file queue.
- The second take appeared empty during recording but finalized to valid silent chatbot footage on stop. ScreenPolish's buffering caused the premature failure assumption. An unnecessary preflight theme-menu action also triggered the controller's stop guard before any paid query. Preserved this evidence and reset only the unused capture conversation. No theme change or application request occurred in those two takes.
- The final selected native source was uniquely named `Restaurant Finder FINAL capture`; the user refreshed the Window list and clicked Record because the Windows control helper still could not click the app controls. Used the persistent queue and did not repeat the buffering/menu checks.
- Consumed **one fresh application request: D1**. Actual completed answer began: “Verified 1 of 2 document-covered Italian restaurants in Kuala Lumpur through online search.” It listed Natalina and explicitly said some covered venues could not be verified. The footer/completion repair worked: acceptance evaluated the completed assistant message, not the watermark or a partial stream.
- Captured tool evidence shows Natalina's organic search returned genuine official-domain URLs, including its home, reservations and menu pages. Nero Nero's search returned `SEARCH_PROVIDER_UNAVAILABLE`, no sources, after **30.18 seconds**. This is consistent with the handler's configured 30-second HTTP timeout; the sanitized result does not prove the underlying provider/network exception. No extra search was made to diagnose it.
- Two discovery searches were captured; duplicate parent-span representations are not extra calls. Parent output guardrail decision was `approved`, action `NONE`, with output unchanged. Initial spans/telemetry were saved. The runtime-log group read timed out; preserve that gap. No extra inference was used for traces, and the optional delayed phase was not needed for this diagnosis.
- D2–D4 remain unused. Source opens: zero. Downloads: zero. Stopped and retained the native failed take at `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_13-35-58/`. No finished demo MP4 was exported and no answer was fabricated or reused.

### Verified restored state

1. Closed only the owned capture browser and paused its verified UI.
2. Restored fixture generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` while the candidate still supported schema 1. Verified six originals, 14 chunks and existing vectors/query readiness with zero embeddings/vector writes.
3. Reviewed and executed the sole conditional rollback. Stack UPDATE_COMPLETE; Runtime/DEFAULT **READY version 26**; exact baseline image/environment/template, previous Lambda code hash and pointer verified. Kept guardrails and outputs unchanged.
4. Restored the prior owned UI code/configuration, verified against `b76ba9a`, and checked localhost health without inference. Restored the saved native capture defaults and verified ScreenPolish idle.
5. Retained both candidate images, Lambda assets, real generation, prompt version 4 and all failed/empty recording evidence. The unrelated owner file remains unchanged/untracked. Private section-12 receipts are under the existing generated `r12/` folder. Publication remains in Git; rollback does not retract it.

## 14. Three connected document questions — approved; recording incomplete

The user approved **“Approve section 14 three-question demo.”** The execution envelope below was authorized. Current execution and the focused recording recovery decision are recorded in section 15.

### Outcome and scope

Finish a concise silent LinkedIn demo of the existing document RAG functionality using the remaining three questions. Show real menu comparison, a linked multi-criterion follow-up with inspectable originals, and an explicit insufficient-evidence response. The external live-discovery opening is omitted from this proposed film because its provider failure is blocking recording.

**No further product-code changes, image build/push, Lambda update, prompt synchronization, corpus ingestion or benchmark are proposed.** Reuse the audited `089d0a8` image and retained real corpus above. This changes the approved scene sequence and requires one new Runtime rollout after the completed rollback; wait for sign-off.

### Exact three-turn script and acceptance

Use one new conversation, once each, in this order:

1. `Compare Margherita prices at Natalina and Nero Nero. Show the sources.` Require both real venues, listed MYR prices 48 and 39, RM9 lower for Nero Nero, preserved service/tax qualifiers and two original-menu citations at pages 6 and 9. Do not invent serving-size comparability.
2. `What about both restaurants' prices and cancellation policies?` Require the follow-up to retain both venue identities/item, retrieve fresh evidence, preserve complete cancellation/late/no-show/date-change/per-person qualifiers, and present four citations belonging to this answer.
3. `According to Natalina's documents, is valet parking available?` Require the existing insufficient-evidence response and no invented valet assertion or citations.

Successful delivery requires all three completed/approved answers, six required source opens, readable focus transitions, compressed waiting time, a silent landscape 1920×1080 MP4 and the editable ScreenPolish project. Do not present skipped web discovery as demonstrated, or claim measured latency/cost gains.

### Exact execution envelope if approved

1. **Readiness and retained artifacts.** Recheck the current stable account/region, stack/Runtime/DEFAULT, Lambda, pointer, owned UI, existing image index/ARM64 child and all nine pinned prompts. Save fresh rollback configuration. Last verified Runtime is 26; do not assume it remains current. Stop on drift or unavailable retained data. Docker is not needed for this reuse path.
2. **One Runtime-only update.** Derive a change set from the fresh deployed template. Change only its container URI to the verified `site-fix-089d0a8-20261020045120-arm64` image and set `DOCUMENT_REAL_SOURCES_ENABLED=true`. Require a complete reference-resolved review showing one Modify operation without replacement, unchanged Lambda/IAM/gateway/guardrails/other environment values/outputs, then execute once. Require matching READY Runtime/DEFAULT and UPDATE_COMPLETE; predict no version number.
3. **Reactivate retained data, pointer last.** Verify the exact real generation, four original byte hashes, manifest, 37 chunks and stored vectors/query readiness. Switch the active pointer conditionally only after the candidate is ready. Zero ingestion embeddings, zero vector writes and no source re-uploads. Preserve both generations.
4. **Owned UI and capture preparation.** Permit one necessary owned UI restart, reusing the already reviewed staged source viewer and matching venv with preserved environment/appearance. Adapt only the private persistent-queue recorder to the three-turn numbering and expected citation counts (2/4/0); use UTF-8 explicitly for evidence. Keep send reservation before dispatch and fail closed on uncertain/failed sends. Use a fresh unique owned browser window/profile/ledger. No debugger, stdin-dependent control, theme/menu rehearsal or new capability recording. Ask for the minimum manual Window selection/Record click if the Windows control helper still cannot operate ScreenPolish.
5. **One fresh native take and at most three sends.** Verify the uniquely selected Window through current window metadata/native recording status. Reuse the validated capture setup; media can be finalized on stop. Set microphone/webcam/system audio Off. Send the three questions exactly once; no web-discovery question, warm-up, diagnostic, rehearsal or automatic retry. These are the three unused application slots, not three on top of them: two failed opening sends across sections 9/12 plus these three would make the overall maximum five. Existing configured routing/model/parent-guardrail bounds apply inside these requests; expected document query embeddings remain seven (2+4+1), with no standalone provider/model/guardrail checks.
6. **Originals and bounded evidence.** Open both menus for answer 1, and both menus/two policies for answer 2: six required opens. Allow at most eight including two optional public booking-origin opens, with zero downloads. Keep complete item/charge and policy context visible. Allow one initial and one delayed read of known trace/request groups, ten pages maximum per group total for this new take; no inference for logs. Bound each readiness stage's read-only polling to 15 minutes. Stop dependent sends on wrong facts, missing sources, moderation failure, unavailable service or incomplete response.
7. **One conditional compatible rollback.** On acceptance/deployment failure, pause the owned UI/sends, restore/verify the fresh old pointer first, then review and execute at most one no-replacement Runtime-only rollback to the fresh baseline, and restore the owned UI. Keep Lambda unchanged, retain all artifacts, use no embeddings/vector writes or post-rollback inference. Stop for a recovery decision if compatibility/pointer restoration cannot be verified.
8. **Native edit/export and delivery.** Keep only chatbot/source-viewer footage, zoom into typing, pull out on send/wait and zoom into completed answers/originals. Accelerate/cut idle time as already requested. No audio, narration, captions, overlays or architecture/title scenes. Use native ScreenPolish editing/export; reload the saved project through Library before export. Verify decoded focus/source frames, actual 1920×1080 output and absence of an audio stream; retain raw/editable files. Deliver the MP4 and optional concise attributed LinkedIn copy. The owner posts it.

This proposed approval also covers bounded private helper adaptation and a documentation-only closeout in the same PRD/draft PR. It includes no merge, force-push, product fix, new image/asset, IAM/gateway/guardrail change, Docker action, deletion, paid media service or LinkedIn posting. A nonconforming result returns for a focused decision.

## 15. Section 14 checkpoint and focused capture recovery — approved and executed

The user approved the replacement take by completing the requested Window/Record action and replying **“recording.”** Its outcome and the remaining recovery decision are in section 16.

### Verified execution

- Fresh readiness verified account/identity, stable Runtime 26, baseline template/Lambda/pointer, owned UI, both retained image digests and all nine immutable prompts. Functional product code remains unchanged from `089d0a8`; the unrelated owner file is preserved.
- Reviewed the complete reference-resolved change set: exactly one Runtime Modify, no replacement, exactly the image URI and real-source flag leaves. Executed once; stack UPDATE_COMPLETE and Runtime/DEFAULT READY **version 27**. Lambda hash, resource identities, other environment values, outputs and guardrails are preserved.
- Reactivated the retained real generation after verifying four originals, 37 chunks and existing vectors/query readiness. **Zero ingestion embeddings and zero vector writes.** Restarted only the verified owned UI once, using the retained reviewed source viewer and preserved configuration. No Docker action, product change, image/asset upload, prompt sync or Lambda mutation occurred.
- The user started the correctly isolated Window take at `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_15-38-44/`. The assistant's preflight incorrectly required the saved webcam preference to be empty; ScreenPolish saved `auto`. Microphone and system audio were Off. The assertion stopped preparation before the status receipt was written, and the next controller command consequently stopped on that missing receipt. The send guard blocked the subsequent send: **zero application requests and zero source opens**.
- Stopped and preserved the take, then closed only its owned browser. Actual finalized media is 1920×1078 video, 84.20 seconds, **no audio stream and no webcam file**. The saved `auto` preference was not evidence that a webcam was captured. No finished demo MP4 has been produced.

### Concrete recovery proposal

The original one-take envelope has been used by this zero-query preflight failure. Approve **one replacement native take only**, using the already deployed Runtime 27, active retained corpus and healthy owned UI. A fresh private persistent controller is prepared for the same exact three questions, limits and acceptance; its unique window is **“Restaurant Finder document capture.”** No additional AWS rollout, UI restart, publication of product code, billable request allowance, image/asset, provider check, embedding ingestion or capability recording is requested.

1. Preserve the failed take/ledger; use a new zero-send ledger and owned browser profile. Use the supported native status to confirm the exact Window. Write and validate the status receipt before calling synchronization. Never execute dependent commands after a failed prerequisite. Do not treat saved webcam `auto` as proof of an active webcam; require microphone/system audio Off, request webcam Off in the capture UI, and verify the actual finalized media/project. Media buffering is expected until stop.
2. If the Windows helper still cannot operate the controls, the user selects Capture → Window → **Restaurant Finder document capture**, sets Microphone/Webcam/System audio Off, and clicks Record once. No primary-display shortcut.
3. Execute section 14's three questions once each, using its **same three unused slots**, six required/eight maximum source opens, zero downloads and existing bounded evidence reads. No rehearsals, discovery query, retries or standalone calls. Preserve the already authorized conditional Runtime-only compatible rollback for a genuine acceptance failure.
4. Finish native ScreenPolish focus editing/export, Library reload, decoded-frame checks and silent 1920×1080 delivery under the existing completion criteria. The owner posts to LinkedIn. Close out documentation only in the existing draft PR as already authorized.

This is an additional capture-start decision caused by the assistant's preflight error; it does not expand the application's paid-call budget or authorize another deployment. All three question slots remain unused. Wait for this focused recovery sign-off before starting the replacement recording or submitting a query.

## 16. Correct application answer; recorder mismatch — approved completion recovery

The user approved **“Approve final take and one additional request,”** then started the uniquely selected final Window and replied **“recording.”** Section 17 records completion.

### Evidence and remaining scope

The replacement take at `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_15-42-02/` submitted the first question exactly once. Saved final DOM shows the correct two-venue comparison: RM48/RM39, RM9 lower, portion-size limitation, page 6/page 9 references, and both 10% service/6% SST qualifiers. Captured traces show two query embeddings, answered coverage 2/2, two citations and parent output guardrail **approved**, action **NONE**. The application request completed; the recorder's completion check did not accept its displayed text.

The installed Chainlit component places rendered Markdown and inline file cards under the same `.message-content` parent. The recorder compared that entire parent's `innerText` against the final server answer; this included PDF file-card labels. CSS also uppercases source-link text. The private detector must scope its DOM extraction to the Markdown-content child and normalize casing caused by presentation, while retaining exact whole-answer wording reconciliation, task completion, thread/message correlation and all send guards. Do not remove completion checks or accept a partial answer.

Windows Computer Use separately ended its session because it could not determine the fullscreen browser URL with enough confidence for its policy check. No bypass, debugger or process-memory attachment is permitted. The native recording was stopped and preserved. The existing controller subsequently reached its timeout and marked D1 UNVERIFIED. The current helper cannot hot-reload or resume this failed slot. No source opens or dependent requests were submitted. Do not replay this uncertain/consumed slot or fabricate conversation history.

The application remains on the approved Runtime 27/real corpus/owned reviewed UI. This recorder-only failure is not evidence of a product failure and requires no new rollout, image, ingestion or UI restart. The original successful response and failed controller receipts remain preserved privately.

### Reviewable completion steps

1. Under the already authorized bounded private-helper adaptation, correct the observed DOM scope/casing mismatch, retain authoritative final/task/thread checks, and persist safe protocol/completion status plus DOM snapshots during each pending send so progress is inspectable without desktop browser automation. Add explicit ordinary command-boundary reload/reconciliation for private helper code; never use a debugger or process memory. Validate static syntax before starting. Keep all helper/profile/trace/media files out of Git.
2. Prepare one fresh private conversation/window and native recording using the exact section-14 script and acceptance. Prefer the owned browser's Playwright controller for browser actions. Use only supported ScreenPolish CLI/native Windows controls. If Window selection cannot be automated safely, request only that necessary manual selection/Record action. Do not use primary-display capture or change security settings.
3. **Approval required for three fresh sends using two remaining slots plus one additional billable application request.** The total across all failed/finished attempts becomes at most **six**, not five. No diagnostic/rehearsal/retry calls, standalone checks or new ingestion embeddings. Keep six required/eight maximum source opens and zero downloads for this completed take. Reuse the approved initial log read already performed; at most its one remaining delayed phase, within ten pages/group total, may cover the final take.
4. On three correct completed answers, inspect the originals and produce the actual silent 1920×1080 native ScreenPolish edit with input/wait/result focus, compressed waiting and no added scenes/audio/overlays. Reload through Library before export; verify decoded frames and audio absence. Preserve raw/editable project and deliver locally. Document-only closeout in the same PRD/draft PR remains included. The owner posts LinkedIn.

Only the additional capture and **one** additional billable application request need expanded authorization. Existing Runtime-only conditional compatible rollback remains available for a genuine acceptance/deployment failure; no second rollout or other AWS mutation is proposed. The user has instructed continued work until completion; safe local preparation may continue while this specific cost/capture decision is pending, but it is not permission to silently enlarge the paid-call allowance.

## 17. Completed silent ScreenPolish demo — 20 October 2026

**The finished video is delivered locally.** It contains only actual chatbot and original-source-viewer footage, with input/result/source focus and shortened waiting time. No narration, audio track, captions, title scenes, architecture scenes, overlays, generated answers or LinkedIn posting.

### Final recording and acceptance

- Used the approved existing Runtime/DEFAULT **27**, retained audited `089d0a8` image, four-source generation and reviewed owned UI. No further deployment, build/push, Lambda change, prompt synchronization, ingestion embedding, vector write, UI restart or Docker action was needed.
- Recorded the unique **Restaurant Finder final document demo** Window. Native final take and editable project are retained at `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_16-01-01/`. Microphone/system audio were Off; finalized raw media contains only video and no webcam file.
- Submitted the exact three section-14 questions once each in one fresh conversation. **Three final-take sends; six sends overall across the earlier failed attempts and final take**, within section 16's explicit expanded allowance. No diagnostic sends or application replay.
- Question 1 correctly compares RM48/RM39, preserves the portion-size limitation and both service/tax qualifiers, states RM9 lower, and supplies menu references for pages 6 and 9.
- Question 2 correctly retains both venues/item, answers **four of four parts**, supplies four answer-specific references and preserves the full 24-hour/late-cancellation/no-show/date-change/per-person policy wording. Both menus and both captured booking-policy originals were inspected.
- Question 3 returns exactly **“The active documents do not contain enough evidence to answer that question.”** No valet assertion or citation was invented.
- **Seven source opens, zero downloads.** Six required opens were completed; one additional permitted open revisited Natalina's policy to inspect the complete long date-change line. The viewer's own PDF zoom and source scrolling were used; source contents were not changed.
- Saved trace evidence verifies **seven query embedding attempts**, comparison coverage 2/2, multipart support 4/4, and **three parent output approvals**, each action NONE. There are two `router.classify` spans because the linked follow-up is resolved from conversation context and intentionally bypasses classification. Initial/delayed log phases together used four pages per known group, below the ten-page cap. No additional log-read phase or standalone inference was used.

### Recorder recovery and limits

The private helper now reads the Markdown-content child, excluding inline file cards; normalizes CSS casing and rendered HTML entities; and retains exact whole-answer wording, message/thread correlation, final non-streaming update and task-end requirements. It saves private completion/DOM progress. Ordinary command-boundary module reload and explicit reconciliation avoid resetting a completed conversation. No debugger or process-memory attachment was used.

A missing private module constant was repaired before any final-take query was sent. Question 1 then completed correctly but required in-place reconciliation of `&amp;` versus rendered `&` after its existing recorder timeout. Question 2 completed correctly; a private result-summary variable error was reconciled at the next command boundary. Neither answer was resubmitted, fabricated or replaced. Question 3 passed directly. Local syntax checks and media verification were performed; no product tests or new product code were added in this stage.

Windows Computer Use was later stopped with physical Escape during an optional native export-progress read. No further Computer Use calls were made. The already-running supported native export completed successfully; remaining checks used files and local media tools.

### Native edit, verified deliverables and current state

- Saved **30 native cuts, 24 manual focus regions**, selected typing/wait acceleration, zero frame padding, and 1080p/30-fps landscape output. All audio, click/zoom sounds, webcam, captions and overlays are disabled in the editable project. Reloaded the saved project through native Library before exporting.
- Native export and delivery copy are **1920×1080**, **167.87 seconds**, **143,057,484 bytes**, with **zero audio streams**. Reviewed 20 representative decoded frames covering typing, wide waiting, answers, PDFs, policy scrolls and abstention. The complete video decoded without errors. The delivery copy's SHA256 matches the native export:
  `9ae580355cdbd8d0f248541588f85580a9dd74b93d7abaabc76945f5bfd76465`.
- Finished MP4: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/output/restaurant-finder-silent-demo/restaurant-finder-demo-1080p.mp4`.
- Ready-to-copy attributed LinkedIn text: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/output/restaurant-finder-silent-demo/linkedin-caption.txt`. It credits the upstream repository, identifies this as an extension, discloses shortened waiting and captured source snapshots, and makes no measured latency/cost claim.
- Raw media, original/edited project receipts, request ledgers and trace evidence are retained privately. Closed only the finished owned capture browser and restored the owner's exact backed-up recording defaults. The localhost UI remains available; no acceptance failure required the conditional rollback. The unrelated owner document is preserved outside publication.

All agreed media completion criteria are met. This film demonstrates the document workflow; it does not show live restaurant discovery. Publication of this closeout remains documentation-only in the existing draft PR. LinkedIn posting is the owner's remaining action.

## 18. Owner-requested revision: continuous footage, brief holds, visible actions and PDF policies

### Approval and intended result

The owner reviewed the section-17 film and requested shorter result pauses, PDF cancellation policies, a visible cursor showing clicks/selection/scrolling, and continuous footage without cuts or sudden screen changes. The owner then replied **“Approve”** to the revision plan. This authorizes local preparation of that revision; it does not renew the exhausted application-request allowance or authorize publication/deployment. The existing delivered MP4, raw recordings, projects, source generations and unrelated owner files must be preserved.

The deliverable is another silent landscape 1920×1080 ScreenPolish MP4 for the owner's LinkedIn demonstration. Keep the same three connected questions and actual chatbot/source-viewer footage. No narration, music, captions, titles, architecture scenes or fabricated answers. A capture-only pointer/click indicator is specifically permitted by the new cursor requirement; it must not alter answer text, evidence, source contents or product behavior.

### Open choices

The owner explicitly chose **actual stored and cited PDF sources**, and **at most one minute**. A subsequent structured reply selected the earlier 60–90-second option; retain the more specific explicit 60-second maximum rather than silently extending it. The target is therefore a continuous film no longer than 60 seconds. No viewer-only conversion or alternative source architecture is needed.

### Observable completion criteria

- Brief completed-answer holds, approximately one second; avoid reading-length pauses. Inspect sources briefly with their cited evidence in view.
- Keep the entire fresh capture in chronological order: empty native `cuts`, no removed internal intervals, duplicated frames to simulate actions, screenshots replacing footage, or jumps between takes. Permit the already requested playback acceleration during waits. Do not change application text or conceal an error through editing.
- Smooth zoom into typing, wide view after sending and during waits, then smooth zoom into completed results. Use continuous pointer paths and visible click feedback, real text selection where useful and observable scrollbar interaction. No instantaneous scroll-to-element or direct scroll-offset jumps during the take.
- Policies open as readable PDFs with complete captured text and truthful provenance. A PDF generated from a captured booking page is not a restaurant-issued PDF. Preserve the original URL/capture date and full timing, fee, per-person, no-show and date-change qualifiers. If actual PDF sources are chosen, retrieval, validator, page citations and displayed original must agree.
- Verify actual output dimensions, absence of every audio stream, continuous source-time coverage and representative decoded typing/wait/result/source/cursor frames. Preserve the editable native project and raw take. Flag any unmet duration goal rather than cutting footage to force it.

### Local execution plan (approved scope)

1. Preserve the successful section-17 controller and all delivered/raw media. Build isolated new helpers; keep profiles, logs, private corpus material and media out of Git. Retain the existing authoritative message/task/thread completion checks, send reservation before dispatch, no automatic retries and failure stops before dependent requests.
2. Add a capture-only visible pointer to the owned browser, driven by actual pointer events. Hide the ordinary page cursor to avoid duplication. Use eased mouse paths to actual targets, click feedback, actual drag selection and scrollbar-thumb drags where the observed browser exposes a usable scrollbar. Stop if required geometry is absent; do not bypass the requirement with an invisible programmatic jump. Keep these helpers separate from the product UI.
3. Prepare a single sequential recording command so the script proceeds immediately after authoritative completion. Reduce default holds to approximately one second; write evidence during the run and review it after capture. Existing external per-command analysis gaps caused the almost-20-minute raw take and must not recur. Preserve seven embedding-query expectation (2+4+1), six required/eight maximum source opens and no downloads as proposed future bounds, not current permission to use them.
4. Validate cursor/scroll/selection behavior using a harmless local page and local browser screenshots only. Do not submit a chatbot question, use a paid service or start another ScreenPolish capture under this local preparation approval. Retain a native recording/export capability check as a specifically listed decision for the next gate if it is needed. Syntax validation is allowed; do not expand into unrelated product tests.
5. After the PDF choice is answered, finish the corresponding local implementation. For actual PDF sources, extend provenance truthfully and preserve old immutable generations, ensure complete policy extraction/selection and source citations, and create visually checked PDFs from the full retained snapshots. Measure candidate chunk count and required embeddings before requesting any activation. For viewer-only PDFs, clearly identify a derived presentation and preserve linkage to the cited original; do not silently call it the original.
6. Prepare an exact reviewed diff and measured release/capture envelope. Obtain a separate explicit decision before any Git publication, source upload/activation, Runtime update, ingestion embedding, new application request or fresh native take. Include one fresh take and three requests only if approved, a bounded number of source opens, any necessary owned UI restart, and a compatible rollback plan based on a fresh baseline. No Docker restart, broad process cleanup, upstream-site modification, paid media service or LinkedIn posting is included.

### Known constraints

ScreenPolish 0.3.0 is retained. Its native playback speed maximum is 4×; the prior raw take cannot become a short continuous video at that speed. A fresh streamlined take is necessary. Native Window selection may still require the owner's minimal Window/Record action because the Windows control helper previously could not obtain safe coordinate geometry. Do not use a whole-display shortcut, debugger, process-memory attachment or a custom native-app IPC bypass. If backend wait times prevent the chosen target duration, report that evidence and propose the smallest adjustment rather than silently cutting or spending more requests.

## 19. PDF revision: local readiness and proposed publication/capture gate

### Verified local work — 20 October 2026

- Generated two three-page PDFs from the complete retained booking snapshots. All six rendered pages were visually inspected; no clipped wording, overlaps or broken arrow/apostrophe glyphs were seen. Every nonblank captured line was reconciled against the extracted PDF text after removal of Markdown heading syntax, layout whitespace and the original invisible U+2060 word joiner. The original snapshots remain unchanged. Both complete cancellation blocks and their following amendment heading are on **page 3**.
- Actual generated sources: `output/pdf/policies-r18/natalina-booking-policy.pdf`, SHA256 `353b694eda50ec71eeb3eca4a11ea5c9a92ddc6aa0573c3d34219a092e608d36`; `output/pdf/policies-r18/nero-booking-policy.pdf`, SHA256 `2eb15f9270a7ab7968d6c9243a7e70eb3493a3d903db7dd27c422f81c4c81824`. Paths are relative to this task's workspace, not the repository. Headers/origin metadata and page footers disclose their captured-page origin and that they are not restaurant-issued PDFs.
- Added the distinct `booking_page_pdf` provenance kind without adding default fields or changing old fingerprints. The policy validator requires the complete policy and its following section boundary in one original page chunk, rejects unsupported/duplicate layouts, retains conflict checks and exact quote matching, and permits deterministic selection for this captured source kind. Answer provenance now labels this PDF rendering truthfully. The existing UI already supports hash-verified PDF originals and page citations; no UI-product change is needed.
- Local candidate **`3507eee57d455c55b2f772e45b9588abe52e17ad633d9ec30adba953f899d175`**, four sources, **20 chunks**: Natalina menu 7, policy 3; Nero menu 6, policy 4. Both complete policy selections are supported, have 327 characters of canonical printed wording, and cite page 3. Thirteen menu embedding texts are unchanged, seven policy texts are new. Up to **20** ingestion embeddings are the safe upper bound without assuming the remote cache; seven suffice if all retained menu cache entries remain valid. No embeddings, remote vector writes, uploads or activation occurred.
- Re-preparing the old local corpus still yields exactly **`f520ceb003e1308ac170d94b98d50e4ee031e998d9306f8d62fa6a8a7b172781`**. Preserve it and the fictional generation. Private candidate manifest/evidence are retained under `restaurant-finder-api/.generated/policy-pdf-demo-r18/` with owner/SYSTEM access.
- Harmless local browser inspection passed with zero application requests, external requests and native recordings: visible click ripple, exact real mouse selection of 13 characters, and a real native scrollbar drag to fraction 0.65145. Visually inspected the click/selection/drag images. The capture pointer's rendered coordinates match actual controlled input, including compositor scrollbar drags. Headless inspection initially hid native scrollbars; removing only its `--hide-scrollbars` default resolved that inspection issue. This is not a native Window recording/export check yet.
- New isolated helpers in workspace `tmp/r18/` retain the successful completion checker; add eased actual mouse movement, smooth wheel reveals, native thumb drags, capture-only pointer feedback, a sequential three-question director, and a guarded owned browser session. The session watches supported native CLI status so it can start immediately after the approved Window/Record action instead of waiting for another chat reply. It reserves sends before clicks, saves final protocol/DOM evidence, never resends automatically, and stops dependent actions on failure. Native edit preparation requires `cuts=[]`, full measured start-to-stop chronological coverage, silent 1080p settings and measured typing/result/source zoom regions. It chooses only native 1–4× playback rates to fit at most 60 seconds; it refuses impossible footage rather than inserting cuts.
- Modified Python files parse, JavaScript helpers pass syntax checks, and `git diff --check` passes. No product test suite, CI run or live request was performed in this local stage. The current tracked base is `9fcc90bafffd8949c422e3dfb73ccd0e273dc10d`. The unrelated owner file retains SHA256 `c3f491550280ba5568cea656d1e90378a76547ee5520e462a323469949aebf9f`. Existing finished video/project are unchanged. Supported ScreenPolish status returned idle.

### Execution gate — approved

The owner approved **“Approve section 19, including replacement contingency.”** The following bounded publication, AWS and media-production envelope is authorized. Normal AWS/ECR charges apply. No paid media service is involved. The earlier request allowance remains exhausted; this revision has its own six-request maximum as specified below.

1. **Native cursor/source-isolation check first.** Permit one harmless local Window-only ScreenPolish capture/export, with no chatbot query, to verify one visible pointer, click feedback, selection, scrollbar dragging, smooth zoom and zero audio. Use only the owned browser's local example and supported ScreenPolish CLI/native controls. If safe Window selection still cannot be automated, request that minimum owner selection/Record action. Do not proceed to paid questions if the native check fails; preserve the check. Do not upgrade ScreenPolish, capture the entire desktop or use a debugger/custom IPC bypass.
2. **Readiness and exact publication.** Recheck account 447393541969, us-east-2/default identity, current Runtime/DEFAULT/stack, image, Lambda, guardrail pair, owned UI, existing active pointer and retained old generation. Save a fresh compatible rollback baseline; do not assume Runtime 27 remains current. Publish only these five reviewed paths to the existing draft PR 1 on `feat/document-multipart-rollout`: this PRD, `restaurant-finder-api/src/domain/document_rag.py`, and `restaurant-finder-api/src/application/document_rag/{multipart.py,multipart_workflow.py,workflow.py}`. Keep private sources, helpers, media, credentials and the unrelated owner file out of Git. No merge or force push. Observe the existing automatic CI result; do not add tests or manually dispatch deployment/destruction workflows.
3. **One image/Runtime release.** Build one audited ARM64 image from that frozen product change and push it to the existing ECR repository. Permit one pre-publication rebuild only for a proven local build failure and one same-image transport retry if needed; no Docker restart/reset or unrelated process termination. Verify the ARM64 digest and reviewed complete Runtime-only no-replacement change set before execution. Change only the container image reference; preserve Lambda, IAM, gateway, guardrail pair, other environment, immutable prompts and outputs. No Lambda asset, prompt sync or other infrastructure change.
4. **Candidate activation, pointer last.** Publish the exact four-PDF, 20-chunk candidate, with at most 20 ingestion embeddings and one generation's 20 vector writes. Verify hashes, staged manifest/chunks, filters and query readiness using stored vectors before conditional pointer publication. Preserve both old generations. Reject any candidate/count/hash drift. No public-site research or new document capture. Allow one necessary restart of the verified owned UI only, with preserved configuration and source viewer.
5. **Three-question fresh take, with one bounded replacement contingency.** Use the unchanged section-14 script in one fresh conversation. Permit three primary billable application requests and, **only if a genuine capture/application failure requires a completely fresh replacement, up to three more**: six maximum total for this revision, no rehearsals, warm-ups, standalone checks or automatic retries. Permit one primary and at most one replacement native Window take. Preserve failed/uncertain slots and never replay them in place. Each completed take must have all three correct linked answers, output guardrail approvals, six required source opens and at most eight, and zero downloads. Expected query embeddings are seven per complete take, within the application requests. All policies must be cited as PDFs at page 3 and both menu pages remain 6/9. Keep fixed evidence/selection/parent-output safeguards; do not weaken them to make filming succeed.
6. **Evidence, continuity and one conditional rollback.** Permit one initial and one delayed read of known trace/request groups, ten pages maximum per group total for this revision, no inference for logs. Bound each readiness stage to 15 minutes. On a genuine release/acceptance failure, stop dependent sends; allow at most one compatible Runtime-only rollback using the fresh saved baseline, restoring/verifying the old pointer before returning to code that cannot parse the new kind. Restore only the owned UI if needed. No new embeddings/vector writes or post-rollback inference. A recorder-only issue does not justify an AWS rollback.
7. **Native finish and deliver.** Keep the entire successful take in chronological order, with no internal cuts, substituted screenshots, reordered scenes or hidden failures. Use smooth input/wait/result/source focus and faster native playback as necessary; final MP4 must be silent, landscape 1920×1080 and **no longer than 60 seconds**. Reload the saved native project through Library before export. Verify the actual media duration, all-source-time coverage, no audio streams, full decode and representative action/source/zoom frames. Preserve raw/editable files and the older deliverable, restore any changed owner recording defaults, and close only owned finished browser processes. Update the local delivery/caption and documentation-only closeout within the same PR. The owner posts to LinkedIn.

This gate includes bounded private helper adaptation needed for the observed native/PDF UI and native edit, within the stated product diff and cost limits. It includes no additional product feature, benchmark, new guardrail/model check, publication of source documents to Git, Docker restart/WSL reset, destructive cleanup or LinkedIn posting. If the full footage cannot fit 60 seconds at the native maximum rate, preserve it and report that unmet criterion; do not claim delivery or silently cut it.

## 20. Harmless native-check recovery decision

Section 19 is approved, but its one harmless Window check stopped before completing the scrollbar actions. The controller rejected the selected text after the actual local button click. Saved take `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_17-58-41/` is preserved: 6.53 seconds, 1920×1078 native video, no audio. A decoded frame confirms the owned local example was captured. Cursor/selection/scrollbar acceptance is not complete. **Zero application requests, publication, image builds/pushes, deployment or corpus activation.** The six-request and two-demo-take envelope is unused.

The same real selection action passed a separate non-recording headed-browser inspection at the actual 1536×864 CSS viewport and DPR 1.25, selecting the exact 13 characters. The cause of the native-take difference is unresolved; do not label it a product failure or spend a demo request to diagnose it. The revised harmless helper now brings the owned page to the foreground, allows 1.5 seconds for the capture handoff to settle, saves before/after geometry and actual selection, and finishes the harmless scrollbar actions for inspection even if the selection boundary differs. It does not relax any application completion/evidence/send guard. Supported Windows controls still fail with `coordinate input geometry is unavailable`; accessibility text is readable but screenshots time out.

**Request one replacement harmless Window capture/export only**, titled **Restaurant Finder cursor verification**, with the same local example and zero chatbot/provider/AWS inference. Preserve the failed check and original owner recording defaults. No new deployment, publication, paid-request allowance or extra demo take is requested. The owner may need to select the exact Window and click Record once because the native helper cannot do so. The controller will run the local actions and stop its owned recording automatically; inspect/export the result before section-19 publication or paid questions. If the replacement does not prove the required visible interactions, stop dependent work and report the remaining gap.

The read-only identity check verified the approved account/user. Initial baseline checks also found the owned localhost UI stopped; its retained source/configuration is being checked for the one necessary restart already authorized by section 19. No UI restart has been performed.

The owner approved the replacement by replying **“Approve — recording started.”** The controller is handling the one additional harmless take; the six paid request slots and both demo takes remain unused.

### Replacement check passed; release readiness verified

The replacement at `C:/Users/kinoc/Videos/ScreenPolish/2026-10-20_18-03-23/` completed the click, exact 13-character mouse selection and both native scrollbar drags. Its native ScreenPolish export was visually checked for a single visible cursor at the actual click/selection/drag, plus smooth manual zooms. The separate native zoom-sound switch initially introduced an audio stream; it was disabled and the **same take** was re-exported without any new capture. Final capability export is **1920×1080, 16.83 seconds, zero audio streams**, no cuts, and decodes fully. Native capability gate is PASS; all six application slots and both demo takes remain unused.

Fresh read-only readiness verified Runtime/DEFAULT **27**, unchanged Lambda, all nine pinned prompts, guardrail pair `ih5xpt3qi946:1`, the old active generation, retained rollback image and correct GitHub draft PR. The localhost UI is stopped; its last reviewed stage at `tmp/r12-ui` matches commit `089d0a8` and its complete saved inventory. The single necessary owned restart remains available. Baseline receipts are private. Earlier checker failures used incorrect local reference names/commits; no actual cloud or UI source drift was found.

Build the image using an explicit clean context of committed API source plus the verified immutable prompt manifest, reusing the prior audited build procedure. The new private candidate folder is not covered by the original Docker ignore glob; do not use the working API directory directly as a build context or include candidate sources, browser profiles, baseline environments or capture evidence in the image. No product Dockerfile/ignore change is needed within this frozen release.
