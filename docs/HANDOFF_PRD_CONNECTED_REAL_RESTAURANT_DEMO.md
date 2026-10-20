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

## 12. Focused redeployment and replacement recording — approval required

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

### Authorized sequence if section 12 is approved

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
