# Brain condition atlas

An interactive, browser-based teaching tool that shows published meta-analytic brain maps (emotions, anxiety, memory retrieval) as slices and a 3D render, with a per-network profile of each map and short lessons on how to read them. It is built for medical students and their teachers (lecture projector or laptop), and is meant to teach what such maps do and do not say.

## Honest-display principles

- **Published maps only.** We show maps that authors published; we compute no meta-analysis of our own.
- **Shared scale only within one study.** The five Wager 2015 emotion maps share one colour scale; maps from different studies never do.
- **Thresholds are never invented.** Each map says whether its cut is `statistical`, `display-only` or `none`, with the authors' own wording.
- **Cross-study comparison is by network.** Maps from different studies are compared through the share of each map in atlas-defined networks, not voxel by voxel.
- **No function labels.** Regions are named by the atlas only; nothing is called the "centre" of a function.

## Data sources

| Map | Source | DOI | Licence |
|---|---|---|---|
| Anger, disgust, fear, happiness, sadness | Wager et al. 2015, *PLoS Comput Biol* 11:e1004066 (CANlab Neuroimaging_Pattern_Masks) | [10.1371/journal.pcbi.1004066](https://doi.org/10.1371/journal.pcbi.1004066) | GPL-3.0 (CANlab repository); article CC-BY 4.0 |
| Anxiety | NeuroVault collection 6012 | pending verification | pending verification |
| Episodic memory retrieval | NeuroVault collection 12234 | pending verification | pending verification |
| Network atlas | Yeo 7 networks (CBIG) | | MIT |
| Subcortical regions | Harvard–Oxford (used to compute profiles only, not shipped) | | FSL licence |
| Background template | MNI152 (nilearn) | | permissive |

Anxiety and retrieval are `unverified` in `pipeline/sources.yaml`. They do not break the build; the site shows "not yet available" for them until verified.

## Run locally

Requirements: [uv](https://docs.astral.sh/uv/) (Python 3.11+) and Node 22.

```sh
cd pipeline
uv run pytest -m "not network"
uv run python -m atlas_pipeline build --out ../site/public/data

cd ../site
npm ci
npm run dev        # development server
npm test           # unit tests
npm run build      # production build in site/dist
```

## Verify a new source with `inspect`

For NeuroVault 6012 (anxiety) and 12234 (retrieval), pick the candidate image, then check it:

```sh
cd pipeline
uv run python -m atlas_pipeline inspect <path-or-url-to-nifti>
```

Then fill in that entry in `pipeline/sources.yaml` (URL, sha256, citation, DOI, n_studies, method, value_meaning, threshold, threshold_type, licence) and set `status: verified`. Acceptance rules (spec sections 6.2 and 6.3):

- Anxiety: the pooled induced-anxiety map in healthy participants, positive side (increases). Not by-paradigm, jackknife or heterogeneity maps, and not the disorder maps.
- Retrieval: a retrieval-versus-baseline (main effect or pooled) map showing where retrieval happens. Fallback collections in order: 21947, then 20036. Between-type contrasts (episodic > semantic, source > item) are not acceptable as the main map.
- Unusable if there is no such map, it is not in MNI space, or it is pre-thresholded at an unstated cut.
- Record the threshold and its type exactly as the authors state them; never choose one.

## Medical-review gate

Lesson and caveat text are drafts. The deploy build refuses to publish until a reviewer signs off:

1. Review and edit the text in `docs/lessons-review.md`.
2. Apply the edits to `pipeline/lessons/lessons.json` (and the `caveat:` fields in `pipeline/sources.yaml`).
3. Set `"reviewed": true` at the top of `pipeline/lessons/lessons.json`.
4. Rebuild: `cd pipeline && uv run python -m atlas_pipeline build --deploy --out ../site/public/data`.

`build --deploy` also fails on leftover TODO text.

## Publish on GitHub Pages

In the repository, go to Settings, then Pages, and set Source to **GitHub Actions**. Pushes to `main` run `.github/workflows/deploy.yml` (tests, the deploy-gated build, then publish). `.github/workflows/ci.yml` runs the tests on every branch and pull request without deploying.

## Licence

GPL-3.0 (see `LICENSE`). Bundled third-party data keeps its own licence, recorded per file in `site/public/data/maps.json` and `atlas.json`: Wager maps GPL-3.0 (article CC-BY 4.0), Yeo atlas MIT, MNI template permissive.
