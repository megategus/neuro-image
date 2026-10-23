# Brain Condition Atlas — Design

Date: 2026-10-23
Status: draft for approval

## 1. Intent

A browser-based teaching tool for **medical students** that shows where in the
brain published meta-analyses place five basic emotions, anxiety, and episodic
memory retrieval, and lets students **compare conditions against each other**.

The lesson the tool exists to teach: brain function is distributed across
networks, not packed into single "centres", and every map is a statistical
result with a method and a threshold, not a photograph of activity. Medical
students arrive with a lesion-to-function localisationist habit; the tool
should correct it, not reinforce it.

"Correct to the existing data" is the governing constraint: every pixel shown
must trace back to a published, cited map, displayed in a way its authors'
method supports.

## 2. Goals

- G1. Show published meta-analytic maps for: anger, disgust, fear, happiness,
  sadness, anxiety, episodic memory retrieval.
- G2. Interactive 3D + orthogonal-slice view of each map on the MNI152 brain,
  including subcortical structures (amygdala, hippocampus).
- G3. Compare the five emotions against each other on one shared colour scale
  (valid: same study, same model).
- G4. Compare across studies (emotion vs anxiety, emotion vs retrieval) at the
  **network level**: each condition's profile across Yeo-7 resting-state
  networks (incl. the default mode network) plus subcortical regions.
- G5. Every map carries its citation, DOI, method, what its values mean, the
  threshold and whether that threshold is statistical or display-only,
  licence, and a short plain-language "what this does not show" caveat.

## 3. Non-goals

- Computing our own meta-analyses (NiMARE/Neurosynth). Variant A was chosen:
  published maps only.
- Processing raw subject data (OpenNeuro, fMRIPrep, EEG/MEG).
- A backend server, user accounts, uploads.
- Researcher features (bulk download, arbitrary map upload, statistics).

## 4. Anti-goals (failure even if it works)

- Labels like "fear centre" or any one-region-one-emotion framing.
- A shared colour bar across maps from different methods (BSPP intensity, ALE,
  SDM effect sizes are different quantities).
- Percentile/rank normalisation that makes weak evidence look as "active" as
  strong evidence.
- Calling a display threshold "significant". The Wager 2015 maps have **no
  significance threshold** (see §6.1).
- A cortical-surface-only view, which would hide the amygdala and hippocampus.

## 5. Constraints

- Static site, no server compute; hosted free (GitHub Pages).
- All scientific decisions live in one offline, reviewable Python pipeline.
- Licences respected and displayed (Wager maps via CANlab repo are GPL-3.0;
  paper is CC-BY).
- NeuroVault, PLOS and PMC were unreachable from the design environment;
  NeuroVault-hosted files are therefore **unverified** and must be verified on
  the developer's machine before use (§9).

## 6. Data sources

### 6.1 Five emotions — VERIFIED

- Wager, Kang, Johnson, Nichols, Satpute, Barrett (2015). A Bayesian model of
  category-specific emotional brain responses. *PLoS Comput Biol* 11:e1004066.
  doi:10.1371/journal.pcbi.1004066. 148 studies.
- Files: `canlab/Neuroimaging_Pattern_Masks`,
  `CANlab_Meta_analysis_maps/2015_Wager_Kang_etal_Emotion_Meta_BSPP/Wager_Kang_PlosCB_emometa_2015_{anger,disgust,fear,happy,sad}.nii.gz`
  (raw.githubusercontent.com works).
- Verified properties: 91×109×91, 2 mm, float32, MNI152 (affine origin
  90/−126/−72, LAS), unthresholded, all values ≥0 within a 212,401-voxel brain
  mask. Peaks: fear R amygdala (22,−4,−12); anger (16,−8,−18); happy R IFG/insula
  (60,12,8); sad (−48,−4,42); disgust occipital (−12,−100,−8).
- Value meaning (paper, verbatim): "spatial posterior expected number of
  activation… centers"; figures "thresholded for display at a voxel-wise
  intensity of 0.001". At 0.001 the maps cover 34–55% of the brain. **Display
  threshold only; no significance test exists for these voxels.**
- Licence: repo GPL-3.0; article CC-BY.

### 6.2 Anxiety — UNVERIFIED

- NeuroVault collection 6012: coordinate-based (SDM) meta-analysis of induced
  (18 articles, N=693, mostly threat-of-shock) and pathological anxiety
  (121 articles). Use the **induced anxiety in healthy participants** map
  (anxiety as a state, contrasted with fear), not the disorder maps.
- **Target (Claude's call):** the pooled induced-anxiety map, healthy
  participants, increases (positive side). Not by-paradigm, jackknife or
  heterogeneity maps. Same unusable rule as §6.3.
- Presented as a contrast to fear (sustained anticipation of uncertain threat),
  **not** as a sixth basic emotion.

### 6.3 Episodic memory retrieval — UNVERIFIED

- Primary: NeuroVault collection 12234, "Default network activation during
  episodic and semantic memory retrieval: a selective meta-analytic
  comparison" — chosen because it ties retrieval to the DMN.
- Fallbacks, in order: 21947 (subjective vs objective recollection, 65 studies,
  ALE), 20036 (source vs item retrieval, 66 studies).
- **Acceptance rule (Claude's call):** the map used must be a retrieval-vs-
  control/baseline (main effect or pooled) map showing *where retrieval
  happens*. Between-type contrasts (episodic > semantic, source > item) are
  not acceptable as "the" retrieval map; they may be shown only as secondary,
  clearly labelled extras. A source is "unusable" if it has no such map, is not
  in MNI space, or is pre-thresholded at an unstated cut.

### 6.4 Reference atlas for network profiles

- Yeo/Buckner 7-network parcellation (cortex; Buckner 2011 cerebellum and Choi
  2012 striatum extensions if obtainable), the same framework Wager 2015 used.
- Subcortical regions: amygdala, hippocampus, thalamus, brainstem/hypothalamus
  — builder picks a published MNI atlas (e.g. Harvard–Oxford subcortical) and
  records it.
- Background template: MNI152 at matching resolution.

## 7. Approaches considered

1. **Static React + Vite + NiiVue site; offline Python pipeline** — CHOSEN.
   Pipeline downloads, verifies, thresholds (only where the source defines a
   threshold), computes network profiles, and writes NIfTI + JSON. Browser only
   displays. Trade-off: two languages and a build step. Chosen because every
   scientific decision is in one reviewable file, the site cannot compute
   anything wrong, and React is the stack the user is learning.
2. Pure Python nilearn HTML pages — fast, but no free overlay combination,
   network-profile view or teaching UI. Rejected (fine as a throwaway spike).
3. Streamlit — needs a server for something that never computes on request.
   Rejected. FastAPI backend dropped for the same reason.

## 8. Design decisions (as decided)

### 8.1 Comparison rules

- **Within the five emotions:** continuous maps on one shared colour scale
  (same model, same units). Default display cut at the authors' 0.001,
  labelled "display threshold chosen by the authors — not a significance
  test". Unthresholded view available.
- **Across studies:** no shared voxel colour scale. Comparison is a
  network-level profile per condition (§8.2), shown next to the brain view.
  Each map is still viewable individually on the brain with its own colour bar
  and its own labelled threshold.

### 8.2 Network profile (builder's call on details; constraints fixed)

- For each condition, report its distribution across the reference regions
  (Yeo-7 + subcortical).
- Continuous maps (emotions): share of total map intensity falling in each
  region (Wager 2015 used mean intensity per region; either is acceptable if
  labelled).
- Thresholded maps (anxiety, retrieval): share of suprathreshold voxels in each
  region, using the threshold the source paper/collection defines.
- **Threshold rule (Claude's call):** if the source states a threshold for the
  file, apply it and label it "statistical". If the file is unthresholded and
  no threshold is stated, treat it as continuous (intensity-share profile,
  labelled "unthresholded"). Never invent a threshold. If pre-thresholded at
  an unstated cut, reject and use the fallback.
- **Negative values (Claude's call):** profiles use the positive side only
  (increases). Negatives, where present, are shown on the brain in a separate
  cool colour scale, labelled "decreases". Emotion maps have no negatives *by
  method* (a point-process model only counts reported peaks); the info panel
  says so, so students don't read absence of decreases as a finding.
- Because these are different underlying quantities, the profile view states
  that it compares **where** each condition's evidence lies, not how strong it
  is. A view normalised by region size ("relative to region volume") is
  offered so large networks don't dominate.

### 8.3 Views

- Main: NiiVue volume view — orthogonal slices + 3D render on MNI152.
  Subcortical structures must be visible. Cortical surface view optional,
  secondary.
- Condition picker; for emotions, multi-select overlay on shared scale.
- Network profile panel (bar/radar-style chart; builder's call) for any
  selected set of conditions, emotions and cross-study alike.
- Info panel per map: citation + DOI, n studies, method, value meaning,
  threshold + type (statistical / display-only), licence, caveat text.
- Region labels toggle (atlas-based names on hover/click, never function
  labels).

### 8.4 Architecture

```
pipeline/ (Python)  -> site/public/data/
  fetch      sources.yaml (URL, DOI, licence, expected checksum)
  verify     shape, space/affine, dtype, value range, header vs expectation
  prepare    resample to common grid, apply source-defined threshold
  profile    network profiles -> profiles.json
  metadata   maps.json (citation, method, threshold type, caveat, licence)
site/ (React + Vite + TypeScript + NiiVue) — reads only the files above
```

One command regenerates all data. Pipeline has tests for: verification
checks, threshold application, profile sums (shares sum to 1), and metadata
completeness (no map without citation/threshold type/licence).

## 9. Risks and open items

- R1. NeuroVault files (anxiety, retrieval) unverified: format, space,
  thresholded vs not, what values mean. First build step is a verification
  spike on the developer's machine; if a primary choice is unusable, use the
  listed fallback and record why.
- R2. Licence of NeuroVault collections to be recorded per collection (often
  CC0; verify).
- R3. Teaching text (caveats, "what this does not show") must be reviewed by
  the user (medical background) before publishing.

## 10. Calls made by Claude (user to check)

- Retrieval acceptance rule (§6.3), anxiety target map (§6.2), threshold rule
  and negative-value handling (§8.2).
- Repository licensed **GPL-3.0** in full, so redistributing the GPL Wager maps
  and derived files is unambiguous. Bundled atlases/templates must be
  GPL-compatible; record each licence in metadata.
- Target devices: laptop/desktop browsers first (lecture projector and
  student laptops); layout responsive, but 3D on phones is best-effort.

## 11. Left to the builder

- Chart type for profiles; colour maps (sequential for intensity, distinct
  hues for overlays; colour-blind safe).
- Exact subcortical atlas and resampling method (nearest for masks, linear for
  continuous maps), recorded in metadata.
- Python packaging (uv/pip), Node tooling, CI for GitHub Pages.
- UI layout and styling.
