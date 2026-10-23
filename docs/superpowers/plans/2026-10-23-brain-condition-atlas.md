# Brain Condition Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A static teaching website that shows published meta-analytic brain maps (five emotions, anxiety, memory retrieval) in 3D, compares them honestly, and walks medical students through guided comparisons.

**Architecture:** An offline Python pipeline (`pipeline/`) fetches, verifies, prepares and profiles the maps and writes NIfTI + JSON into `site/public/data/`. A React + Vite + TypeScript site (`site/`) built on NiiVue reads only those files. The site never computes science; the pipeline does all of it, under test.

**Tech Stack:** Python 3.11+ with uv, nibabel, numpy, nilearn 0.14.x, PyYAML, pytest. Node 22, Vite, React 18, TypeScript, @niivue/niivue 0.69.x, Vitest + Testing Library. GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-10-23-brain-condition-atlas-design.md`

## Global Constraints

- Published maps only; no meta-analysis is computed by us (spec §3).
- Never share a colour scale across maps from different studies; only the five Wager 2015 emotions share one (spec §8.1).
- Never invent a threshold. Threshold types: `statistical`, `display-only`, `none` (spec §8.2).
- Wager maps: default display cut `0.001`, label verbatim: "display threshold chosen by the authors — not a significance test".
- Never label a region with a function ("fear centre"); region labels come from the atlas only.
- Profiles use the positive side only; negatives are shown as "decreases" in a separate cool colour scale.
- Every map in `maps.json` has: citation, DOI, n_studies, method, value_meaning, threshold, threshold_type, licence, caveat. A build without them fails.
- Repository licence: GPL-3.0. Every bundled third-party file's licence is recorded in `maps.json`/`atlas.json`.
- Lesson text is a draft until the user sets `"reviewed": true`; the deploy workflow refuses to publish unreviewed lessons.
- Main view is volumetric (slices + 3D render); amygdala and hippocampus must be visible.
- Target: laptop/desktop browsers; phones best-effort.

## Review Focus

- A source map on a different grid (e.g. 1 mm or 3 mm NeuroVault upload) must be resampled onto the 2 mm MNI grid, not displayed misaligned — test in Task 3.
- A source that is `unverified` or unreachable must not break the build; the site shows "not yet available" for it — tests in Tasks 1 and 6.
- Selecting an emotion together with retrieval or anxiety must never put them on one colour bar — test in Task 7.
- No WebGL2 (old projector PC) must show a readable message while info and profile panels still work — test in Task 8.
- A lesson that references an unknown map id, or a site built with unreviewed lessons for deploy, must fail loudly — tests in Tasks 5 and 10.

---

## File Structure

```
LICENSE                                   GPL-3.0 text
pipeline/
  pyproject.toml                          uv project, package atlas_pipeline
  sources.yaml                            every source map: url, DOI, licence, status, threshold info
  src/atlas_pipeline/
    sources.py                            load/validate sources.yaml -> Source
    fetch.py                              download + sha256 cache
    verify.py                             header/space/value checks -> VerificationReport
    inspect_cli.py                        `inspect` command: report on an unverified file (user runs locally)
    prepare.py                            resample, threshold rule, sign split -> PreparedMap
    atlas.py                              reference atlas (Yeo-7 + subcortical) -> ReferenceAtlas
    profile.py                            network profiles
    metadata.py                           maps.json, atlas.json, lessons validation
    build.py                              `build` command: whole pipeline -> site/public/data
    __main__.py                           CLI entry: build | inspect
  lessons/lessons.json                    lesson content (draft text, reviewed flag)
  tests/                                  one test file per module; fixtures make synthetic NIfTI, no network
site/
  package.json, vite.config.ts, tsconfig.json, index.html
  src/
    data/types.ts                         TS types mirroring maps.json/profiles.json/lessons.json
    data/load.ts                          fetch + parse data files
    data/scales.ts                        colour-scale grouping rules
    viewer/BrainViewer.tsx                NiiVue wrapper
    panels/InfoPanel.tsx                  per-map citation/threshold/caveat
    panels/ProfileChart.tsx               network profile chart
    lessons/LessonPlayer.tsx              guided comparisons
    App.tsx, main.tsx
  src/**/*.test.ts(x)
.github/workflows/deploy.yml
```

---

### Task 1: Pipeline project, sources registry, fetch with cache

**Files:**
- Create: `LICENSE`, `pipeline/pyproject.toml`, `pipeline/sources.yaml`, `pipeline/src/atlas_pipeline/{__init__,sources,fetch}.py`
- Test: `pipeline/tests/test_sources.py`, `pipeline/tests/test_fetch.py`, `pipeline/tests/conftest.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Source: id: str; label: str; group: Literal["emotion","anxiety","retrieval"]; study_id: str; url: str; sha256: str | None; status: Literal["verified","unverified"]; citation: str; doi: str; n_studies: int | None; method: str; value_meaning: str; threshold: float | None; threshold_type: Literal["statistical","display-only","none"]; licence: str; caveat: str`
  - `load_sources(path: Path) -> list[Source]` (raises `ValueError` naming the source id and missing field)
  - `fetch(source: Source, cache_dir: Path) -> Path` (raises `FetchError`; verifies sha256 when set)
- `study_id` is the colour-scale grouping key: all five Wager maps share `wager2015`.

- [ ] **Step 1: Write `sources.yaml`** with the five Wager entries (ids `anger, disgust, fear, happiness, sadness`; URLs `https://raw.githubusercontent.com/canlab/Neuroimaging_Pattern_Masks/master/CANlab_Meta_analysis_maps/2015_Wager_Kang_etal_Emotion_Meta_BSPP/Wager_Kang_PlosCB_emometa_2015_{anger,disgust,fear,happy,sad}.nii.gz`; status `verified`; DOI `10.1371/journal.pcbi.1004066`; n_studies 148; method "Bayesian spatial point process (BSPP) coordinate-based meta-analysis"; value_meaning "posterior expected number of activation centres"; threshold 0.001; threshold_type `display-only`; licence "GPL-3.0 (CANlab repository); article CC-BY 4.0"). Add `anxiety` (NeuroVault collection 6012, pooled induced anxiety, healthy participants) and `retrieval` (NeuroVault collection 12234) with `status: unverified`, `url` set to the collection page, other fields filled where known, `null` otherwise. Caveat text is drafted in Task 10; use `"TODO-caveat"` placeholders that Task 5's completeness check will reject for deploy.
- [ ] **Step 2: Write failing tests**
  - `test_load_sources_reads_all_seven`: 7 sources; `{s.study_id for s in emotions} == {"wager2015"}`.
  - `test_load_sources_rejects_missing_doi`: yaml without `doi` → `ValueError` whose message contains the source id.
  - `test_fetch_uses_cache`: second call with a file already in cache does no network call (monkeypatch `urllib.request.urlopen` to raise).
  - `test_fetch_rejects_checksum_mismatch`: cached file with wrong sha256 → `FetchError`.
  - `test_unverified_source_not_fetched_by_default`: `fetch` on `status="unverified"` raises `FetchError("unverified")`.
- [ ] **Step 3: Run** `cd pipeline && uv run pytest tests/test_sources.py tests/test_fetch.py -v` — expect FAIL (import errors).
- [ ] **Step 4: Implement** `load_sources` and `fetch` (urllib, honour `HTTPS_PROXY` implicitly, write to temp then rename).
- [ ] **Step 5: Run** the same command — expect PASS. Then `uv run python -c "from atlas_pipeline.fetch import fetch; ..."` fetching `fear` for real; record the five sha256 values into `sources.yaml`.
- [ ] **Step 6: Commit** `git add LICENSE pipeline && git commit -m "pipeline: sources registry and cached fetch"`

### Task 2: Verification and the `inspect` command for unverified sources

**Files:**
- Create: `pipeline/src/atlas_pipeline/{verify,inspect_cli,__main__}.py`
- Test: `pipeline/tests/test_verify.py`

**Interfaces:**
- Consumes: `Source`, `fetch`.
- Produces:
  - `@dataclass class VerificationReport: ok: bool; shape: tuple[int,...]; zooms: tuple[float,...]; is_mni: bool; has_negative: bool; is_thresholded: bool; min: float; max: float; problems: list[str]`
  - `verify(img: nib.Nifti1Image) -> VerificationReport`
  - CLI: `uv run python -m atlas_pipeline inspect <path-or-url>` prints the report as JSON.
- Rules: 3D only (4D → problem "4D image: choose a volume"); MNI check = affine maps voxel centre to within 3 mm of MNI152 bounds and axes are RAS/LAS; `is_thresholded` = more than 30% of in-brain voxels exactly zero while non-zero values have a minimum absolute value > 0 (report the minimum, the human decides).

- [ ] **Step 1: Write failing tests** with synthetic images from `conftest.py` (`make_img(shape, affine, data)`):
  - `test_wager_like_map_ok`: 91×109×91, 2 mm MNI affine `[[-2,0,0,90],[0,2,0,-126],[0,0,2,-72]]`, values ≥0 → `ok`, `has_negative is False`.
  - `test_detects_negative_values`: → `has_negative is True`.
  - `test_rejects_4d`: → `ok is False`, problem mentions "4D".
  - `test_rejects_non_mni_affine`: identity affine → `is_mni is False`, `ok is False`.
  - `test_flags_prethresholded`: 60% zeros, non-zero min 3.1 → `is_thresholded is True`, `min == 3.1`.
- [ ] **Step 2: Run** `uv run pytest tests/test_verify.py -v` — expect FAIL.
- [ ] **Step 3: Implement** `verify` and the `inspect` subcommand (argparse in `__main__.py`).
- [ ] **Step 4: Run** — expect PASS. Then run `inspect` on the cached real `fear` map; expect `ok: true, has_negative: false`.
- [ ] **Step 5: Commit** `git commit -am "pipeline: map verification and inspect command"`
- [ ] **Step 6: USER HANDOFF (blocks anxiety/retrieval only):** NeuroVault is unreachable from the build environment. Ask the user to run, on their machine, `uv run python -m atlas_pipeline inspect <NeuroVault image URL>` for candidate images in collections 6012 and 12234 (then fallbacks 21947, 20036), apply the spec's acceptance rules (§6.2, §6.3), and paste the reports. Update `sources.yaml` (url = direct image file URL, sha256, threshold, threshold_type, status `verified`) from their reports. Continue with Tasks 3+ meanwhile; unverified sources are skipped.

### Task 3: Prepare maps (resample, threshold rule, sign split)

**Files:**
- Create: `pipeline/src/atlas_pipeline/prepare.py`
- Test: `pipeline/tests/test_prepare.py`

**Interfaces:**
- Consumes: `Source`, `VerificationReport`.
- Produces:
  - `@dataclass class PreparedMap: source: Source; positive: nib.Nifti1Image; negative: nib.Nifti1Image | None; display_min: float; display_max: float`
  - `prepare(source: Source, img: nib.Nifti1Image, target: nib.Nifti1Image) -> PreparedMap`
- Rules: resample continuous data with `nilearn.image.resample_to_img(..., interpolation="continuous")` onto `target` (MNI152 2 mm from `nilearn.datasets.load_mni152_template(resolution=2)`); `positive` = values > 0; `negative` = absolute value of values < 0, `None` if there are none; if `threshold_type == "statistical"`, values with `abs < threshold` become 0 in both; `display-only` and `none` keep all values (display cut is a viewer setting); `display_min = threshold or 0`, `display_max` = 99.9th percentile of positive non-zero values. Output dtype float32.

- [ ] **Step 1: Write failing tests**
  - `test_resamples_3mm_onto_2mm_grid`: 3 mm input → output shape `(91,109,91)` and affine equal to target's; a blob centred at MNI (22,−4,−12) still has its maximum within 4 mm of that coordinate.
  - `test_statistical_threshold_zeroes_subthreshold`: threshold 3.1, values 2.0 and 4.0 → only 4.0 survives.
  - `test_display_only_keeps_all_values`: Wager-like source, value 0.0005 survives.
  - `test_sign_split`: values {−2, 3} → `positive.max()==3`, `negative.max()==2`.
  - `test_no_negatives_gives_none`.
- [ ] **Step 2: Run** `uv run pytest tests/test_prepare.py -v` — FAIL.
- [ ] **Step 3: Implement** `prepare`.
- [ ] **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** `git commit -am "pipeline: prepare maps onto common grid"`

### Task 4: Reference atlas and network profiles

**Files:**
- Create: `pipeline/src/atlas_pipeline/{atlas,profile}.py`
- Test: `pipeline/tests/test_atlas.py`, `pipeline/tests/test_profile.py`

**Interfaces:**
- Consumes: `PreparedMap`.
- Produces:
  - `@dataclass class ReferenceAtlas: img: nib.Nifti1Image; labels: dict[int, str]; sources: list[dict]` (each dict: name, citation, licence, bundled: bool)
  - `build_reference_atlas(target: nib.Nifti1Image, cache_dir: Path) -> ReferenceAtlas`
  - `@dataclass class Profile: map_id: str; quantity: Literal["intensity_share","voxel_share"]; share: dict[str, float]; size_normalised: dict[str, float]; unassigned: float`
  - `compute_profile(pm: PreparedMap, atlas: ReferenceAtlas) -> Profile`
- Atlas: labels 1–7 from Yeo 2011 7-network liberal mask (`nilearn.datasets.fetch_atlas_yeo_2011`), names `Visual, Somatomotor, Dorsal attention, Ventral attention/salience, Limbic, Frontoparietal control, Default mode`; subcortical labels 8–11 `Amygdala, Hippocampus, Thalamus, Brainstem` from Harvard–Oxford subcortical maxprob thr25 2 mm (`fetch_atlas_harvard_oxford("sub-maxprob-thr25-2mm")`, left+right merged), overriding Yeo where they overlap. Resample with `interpolation="nearest"`. Record each atlas's licence; set `bundled=False` for any whose licence is not GPL-compatible (Harvard–Oxford is FSL-licensed: profiles use it, the site does not ship the file).
- Profile: `quantity = "voxel_share"` when `threshold_type == "statistical"`, else `"intensity_share"`. Share per region = region's sum of `positive` values (or count of non-zero voxels) ÷ total in-brain; `unassigned` = remainder outside any label; `size_normalised[r] = share[r] / (region voxels / labelled voxels)`.

- [ ] **Step 1: Write failing tests** with a synthetic 3-label atlas:
  - `test_shares_plus_unassigned_sum_to_one` (abs tol 1e-6).
  - `test_statistical_map_uses_voxel_share`.
  - `test_display_only_map_uses_intensity_share`.
  - `test_size_normalised_equal_density_is_one`: uniform map → every region's `size_normalised ≈ 1.0`.
  - `test_atlas_has_eleven_named_labels` (network test, mark `@pytest.mark.network`, skipped offline).
- [ ] **Step 2: Run** `uv run pytest tests/test_atlas.py tests/test_profile.py -v` — FAIL.
- [ ] **Step 3: Implement** both modules.
- [ ] **Step 4: Run** — PASS. Sanity check on the real fear map: `Amygdala` `size_normalised > 1`. Expected from the verified peak; if not, stop and report instead of proceeding.
- [ ] **Step 5: Commit** `git commit -am "pipeline: reference atlas and network profiles"`

### Task 5: Metadata, lessons validation, `build` command

**Files:**
- Create: `pipeline/src/atlas_pipeline/{metadata,build}.py`, `pipeline/lessons/lessons.json` (structure only; placeholder text)
- Test: `pipeline/tests/test_metadata.py`, `pipeline/tests/test_build.py`

**Interfaces:**
- Consumes: everything above.
- Produces (files in `site/public/data/`):
  - `maps/<id>_pos.nii.gz`, `maps/<id>_neg.nii.gz` (if any), `template.nii.gz`, `atlas_labels.nii.gz` (only if every atlas source `bundled`)
  - `maps.json`: `{"maps": [{id,label,group,study_id,citation,doi,n_studies,method,value_meaning,threshold,threshold_type,threshold_label,licence,caveat,display_min,display_max,has_negative,files:{pos,neg}}], "unavailable": [{id,label,reason}]}`
  - `profiles.json`: `{"regions": [names...], "profiles": [Profile as dict]}`
  - `atlas.json`: `{"labels": {...}, "sources": [...]}`
  - `lessons.json`: copied after validation
  - `lessons.json` schema: `{"reviewed": bool, "lessons": [{id, title, map_ids: [str], view: "overlay"|"profile"|"both", body: [str], notice: str, claims: [{text, source_doi}]}]}`
- `validate_lessons(lessons: dict, map_ids: set[str]) -> list[str]` (problems).
- `check_completeness(maps: list[dict], for_deploy: bool) -> list[str]`: missing fields always fail; `"TODO-caveat"` and `reviewed: false` fail only when `for_deploy`.
- `threshold_label`: `display-only` → the exact Global Constraints text; `statistical` → `"statistical threshold reported by the authors: <value>"`; `none` → `"unthresholded — all values shown"`.
- CLI: `uv run python -m atlas_pipeline build [--deploy] --out ../site/public/data`; unverified sources go to `unavailable` with reason `"source not yet verified"`; exits non-zero on any problem.

- [ ] **Step 1: Write failing tests**
  - `test_display_only_label_text_is_verbatim`.
  - `test_unknown_map_id_in_lesson_fails`.
  - `test_lesson_claim_without_doi_fails`.
  - `test_deploy_fails_when_unreviewed`; `test_local_build_allows_unreviewed`.
  - `test_unverified_source_listed_unavailable` (build with a fake fetch, no network): `maps.json["unavailable"][0]["id"] == "anxiety"` and exit code 0 without `--deploy`.
  - `test_atlas_file_not_written_when_not_bundled`.
- [ ] **Step 2: Run** `uv run pytest -v` — new tests FAIL.
- [ ] **Step 3: Implement** `metadata.py`, `build.py`, wire into `__main__.py`.
- [ ] **Step 4: Run** full suite — PASS. Run real `build` (no `--deploy`); expect 5 maps + 2 unavailable.
- [ ] **Step 5: Commit** (`site/public/data/` is committed; it is small, ~5 MB) `git add -A && git commit -m "pipeline: metadata, lesson validation, build command"`

### Task 6: Site scaffold and typed data loading

**Files:**
- Create: `site/` via `npm create vite@latest site -- --template react-ts`; add `@niivue/niivue@0.69`, `vitest`, `@testing-library/react`, `jsdom`; `site/src/data/{types,load}.ts`
- Test: `site/src/data/load.test.ts`

**Interfaces:**
- Consumes: JSON shapes from Task 5.
- Produces: TS types `MapMeta`, `UnavailableMap`, `Profile`, `Lesson`, `LessonsFile`; `loadAll(base: string): Promise<{maps: MapMeta[]; unavailable: UnavailableMap[]; profiles: Profile[]; regions: string[]; lessons: LessonsFile; atlasLabels: boolean}>`.
- Vite `base: "./"` so it works under the GitHub Pages sub-path.

- [ ] **Step 1: Write failing tests** (mock `fetch`): `loadAll` returns 5 maps from a fixture; a fixture with `unavailable` entries returns them; a missing `profiles.json` rejects with an error naming the file.
- [ ] **Step 2: Run** `cd site && npx vitest run` — FAIL.
- [ ] **Step 3: Implement** types and `loadAll`.
- [ ] **Step 4: Run** — PASS. `npm run build` succeeds.
- [ ] **Step 5: Commit** `git add site && git commit -m "site: scaffold and typed data loading"`

### Task 7: Colour-scale grouping rules

**Files:**
- Create: `site/src/data/scales.ts`
- Test: `site/src/data/scales.test.ts`

**Interfaces:**
- Produces: `type ScaleGroup = {studyId: string; mapIds: string[]; min: number; max: number}`; `groupScales(selected: MapMeta[]): ScaleGroup[]` (one group per `study_id`; a group's min/max span its members' `display_min/display_max`); `canOverlay(selected: MapMeta[]): boolean` (true only if all share one `study_id`).

- [ ] **Step 1: Write failing tests**
  - `test fear+sadness -> one group, shared range`.
  - `test fear+retrieval -> two groups` and `canOverlay` false.
  - `test single map -> one group equal to its own range`.
- [ ] **Step 2: Run** `npx vitest run src/data/scales.test.ts` — FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** `git commit -am "site: colour-scale grouping rules"`

### Task 8: Brain viewer, info panel, profile chart, app shell

**Files:**
- Create: `site/src/viewer/BrainViewer.tsx`, `site/src/panels/{InfoPanel,ProfileChart}.tsx`, `site/src/App.tsx`
- Test: `site/src/panels/InfoPanel.test.tsx`, `site/src/panels/ProfileChart.test.tsx`, `site/src/viewer/BrainViewer.test.tsx`

**Interfaces:**
- Consumes: `loadAll`, `groupScales`, `canOverlay`.
- Produces: `<BrainViewer maps={MapMeta[]} cut={number|null} showLabels={boolean} />`, `<InfoPanel map={MapMeta} />`, `<ProfileChart profiles={Profile[]} regions={string[]} mode={"share"|"size_normalised"} />`, `<App />` with condition picker, cut slider ("show unthresholded" toggle), region-labels toggle (hidden if `atlasLabels` false), profile mode toggle.
- Viewer: NiiVue multiplanar + 3D render (`nv.setSliceType(nv.sliceTypeMultiplanar)` with render tile), template as background, positive overlays in warm colormap, negatives in cool colormap labelled "decreases". If `canOverlay` is false, render one viewer per scale group side by side, each with its own colour bar; never one viewer with mixed-study overlays. Default cut for Wager maps = 0.001.
- WebGL2 check: if `canvas.getContext("webgl2")` is null, render the text "3D view needs WebGL2, which this browser does not provide. The map details and network profiles below still work." instead of the canvas.
- Info panel shows every `maps.json` field, the `threshold_label` verbatim, and "No decreases can appear in this map by method" when `study_id === "wager2015"`.
- Profile chart: grouped horizontal bars (one bar per selected map per region), a note line: "Compares where each condition's evidence lies, not how strong it is." Unavailable maps appear in the picker disabled, with their reason.

- [ ] **Step 1: Write failing tests**
  - InfoPanel renders the DOI link and the verbatim display-only label for a Wager fixture.
  - InfoPanel shows the "No decreases" note only for `wager2015`.
  - ProfileChart renders the comparison note and one bar per (map, region).
  - BrainViewer with `getContext` mocked to return null renders the WebGL2 message.
  - BrainViewer given fear + retrieval renders two viewer containers (`data-testid="viewer-group"`).
- [ ] **Step 2: Run** `npx vitest run` — FAIL.
- [ ] **Step 3: Implement** components and App.
- [ ] **Step 4: Run** — PASS. `npm run dev`, open in Playwright (Chromium at `/opt/pw-browsers`), screenshot fear on slices; confirm the amygdala blob is visible near MNI (22,−4,−12).
- [ ] **Step 5: Commit** `git commit -am "site: viewer, info panel, profile chart"`

### Task 9: Guided lessons player

**Files:**
- Create: `site/src/lessons/LessonPlayer.tsx`; modify `site/src/App.tsx`
- Test: `site/src/lessons/LessonPlayer.test.tsx`

**Interfaces:**
- Consumes: `LessonsFile`, `MapMeta[]`, the components from Task 8.
- Produces: `<LessonPlayer lessons={LessonsFile} onLoadMaps={(ids: string[], view) => void} onExit={() => void} />` with next/previous, body paragraphs, a highlighted "Notice" box, a claims list with DOI links, and an "Explore freely" button. A lesson whose maps are unavailable shows "This lesson needs data not yet available" and is skippable. While `reviewed` is false, a banner reads "Draft — not yet medically reviewed".

- [ ] **Step 1: Write failing tests**: renders lesson 1 title; Next moves to lesson 2 and calls `onLoadMaps` with its `map_ids`; draft banner present when `reviewed:false`, absent when true; unavailable-map lesson shows the message.
- [ ] **Step 2: Run** `npx vitest run src/lessons` — FAIL.
- [ ] **Step 3: Implement**, wire into App as the landing view.
- [ ] **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** `git commit -am "site: guided lessons player"`

### Task 10: Draft lesson and caveat text (for user's medical review)

**Files:**
- Modify: `pipeline/lessons/lessons.json`, `pipeline/sources.yaml` (replace `TODO-caveat`)
- Create: `docs/lessons-review.md` (all text in one readable file for the user, with every claim and its source)

**Interfaces:**
- Consumes: Task 5 schema.

- [ ] **Step 1: Draft** the five lessons from spec G6 and the seven caveats. Rules: each `claim` cites the DOI of a map shown in that lesson or Lindquist 2012 (doi:10.1017/S0140525X11000446); no function labels on regions; numbers only from `profiles.json` actually produced by the build; anxiety framed as a contrast with fear, not a basic emotion. Lessons 3–5 depend on unverified maps; draft them anyway and mark them in `docs/lessons-review.md`.
- [ ] **Step 2: Run** `uv run python -m atlas_pipeline build --out ../site/public/data` — PASS (local), and `--deploy` — expect FAIL on `reviewed: false` only.
- [ ] **Step 3: Commit** `git commit -am "content: draft lessons and caveats for medical review"`
- [ ] **Step 4: USER HANDOFF:** ask the user to review `docs/lessons-review.md`; apply their edits; they set `"reviewed": true` themselves (or explicitly tell Claude to).

### Task 11: GitHub Pages deployment

**Files:**
- Create: `.github/workflows/deploy.yml`, `README.md` (replace)

**Interfaces:**
- Consumes: `build --deploy`, `npm run build`.
- Workflow on push to `main`: set up uv + Node 22, `uv run pytest`, `uv run python -m atlas_pipeline build --deploy --out ../site/public/data` (uses committed cache-free fetch; network allowed in Actions), `npx vitest run`, `npm run build`, deploy `site/dist` with `actions/deploy-pages`.
- README: what the tool is, the data sources with DOIs and licences, how to run `build` and `inspect`, the medical-review gate.

- [ ] **Step 1: Write** the workflow and README.
- [ ] **Step 2: Verify locally** the same commands in order; expect all pass except the `--deploy` step while lessons are unreviewed (expected, and the reason deploy is gated).
- [ ] **Step 3: Commit** `git commit -am "ci: GitHub Pages deploy gated on medical review"`
