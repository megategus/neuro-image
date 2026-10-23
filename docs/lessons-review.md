# Lesson and caveat text: medical review

**For the reviewer.** Everything below is a draft written by Claude. It is not a medical review. Please check three things: (1) every sentence is medically and scientifically correct for a medical-student audience; (2) no sentence calls a region the centre of a function or suggests that one region does one job; (3) every factual sentence matches the source given next to it. Sentences marked **NEEDS SOURCE** are general background with no verified source yet. Each must be checked against the anxiety or retrieval map and its paper once those are verified, or cut. Edit the text in `pipeline/lessons/lessons.json` (lessons) and `pipeline/sources.yaml` (the `caveat:` field of each map). Approval is per item, so approving one lesson never approves another:
- **Lessons:** when a lesson is right, set `"reviewed": true` on that lesson in `pipeline/lessons/lessons.json` (every lesson starts at `false`).
- **Caveats:** when a map's caveat is right, set `caveat_reviewed: true` on that source in `pipeline/sources.yaml`.
- Then rebuild (`cd pipeline && uv run python -m atlas_pipeline build --out ../site/public/data`).

The deploy build (`build --deploy`) refuses to publish while any lesson whose maps are all verified, or any verified map's caveat, is still unreviewed. Lessons and caveats that need a still-unverified map (anxiety, retrieval: lessons 3–5) do not block deploy, and the site does not show their text. When such a map is later verified, its lessons and caveat start blocking deploy until you review them; nothing becomes public without your sign-off. Until a lesson is reviewed the site shows "Draft — not yet medically reviewed" above it, and an unreviewed caveat is marked "Caveat not yet medically reviewed" in the info panel.

Source key:
- **W2015**: Wager, Kang, Johnson, Nichols, Satpute, Barrett (2015) *PLoS Comput Biol* 11:e1004066, doi:10.1371/journal.pcbi.1004066. Quotes are verbatim from the full text. Line breaks are joined, and the PDF's own typos ("amgydala") are kept.
- **L2012**: Lindquist, Wager, Kober, Bliss-Moreau, Barrett (2012) *Behav Brain Sci* 35:121–143, doi:10.1017/S0140525X11000446. No full text was available, so only its well-known headline finding is used.
- **profiles.json**: `site/public/data/profiles.json`, the network profiles this build produced.
  - *Share* is the fraction of the map's total positive intensity that falls in a region (the "Share of evidence" view).
  - *Size-normalised* is that region's share of intensity divided by its share of atlas voxels, counting labelled atlas regions only, so 1 = average density (the "Relative to region size" view).
  - The labelled regions are the 7 Yeo cortical networks plus amygdala, hippocampus, thalamus and brainstem. *Unassigned*, the intensity outside them, is 41.9% (disgust) to 48.3% (sadness).
- **spec**: `docs/superpowers/specs/2026-10-23-brain-condition-atlas-design.md` (project design decisions, not science).
- **UI**: an instruction about this site's controls, not a factual claim.

---

## Lesson 1: Reading a meta-analytic map

- **id:** `reading-maps` · **map_ids:** `fear` · **view:** overlay (brain only)
- **Status:** map verified.

### Body

1. "This is not a picture of a brain at work but a statistical summary of 148 published PET and fMRI studies of five emotions (Wager et al., 2015), built from the peak coordinates those studies reported."
   - W2015: "Our analysis included 148 PET and fMRI studies published from 1993 to 2011 (377 maps, 2159 participants) that attempted to specifically cultivate one of the five most commonly studied categories of emotion".
   - W2015: "At Level 1 is the individual study data, in the form of peak coordinate locations."
2. "Each voxel holds the model's expected number of activation (population) centres: summed over a region, it gives the expected number of such centres there for studies of fear, not a signal strength or a p-value."
   - W2015: "the intensity function map representing the spatial posterior expected number of activation or population centers in each area across the brain given the emotion category".
   - W2015, Fig. 1 legend: "their integral over any portion of the brain reflects the expected number of activation centers in that area for all studies with a particular emotion."
   - "Not a signal strength or a p-value" is Claude's paraphrase of what that definition rules out.
3. "The default cut of 0.001 is the value the authors chose for drawing their figures, not a significance test, and at that cut each emotion map colours a third to over half of the brain (34–55%)."
   - W2015, Fig. 1 legend: "The maps are thresholded for display at a voxel-wise intensity of 0.001 or above."
   - spec §6.1: "Display threshold only; no significance test exists for these voxels." / "At 0.001 the maps cover 34–55% of the brain."
   - Re-measured for this review from the built maps, as voxels ≥0.001 out of the 212,401-voxel brain mask: anger 50.3%, disgust 34.4%, fear 54.5%, happiness 40.3%, sadness 33.8%. These figures come from our own measurement, not from the paper.
4. "The model counts reported peaks from emotion-versus-comparison contrasts and has no negative values, so this map cannot show decreases; their absence is not a finding."
   - W2015: "Foci are nested within study activation maps, maps of group comparisons between an emotion- or affect-related condition and a less intense or affectively neutral comparison condition."
   - W2015: "We model the foci (peak activation locations)"
   - No negative values: spec §6.1 verified property, "all values ≥0 within a 212,401-voxel brain mask".
   - "Cannot show decreases" follows from that (spec §8.2). The paper does not discuss decreases.
5. "The studies used varied tasks and stimuli, and regions that are hard to image, such as the brainstem and ventromedial prefrontal cortex, are probably under-represented."
   - W2015: "The studies were relatively heterogeneous in their methods for eliciting emotion (the most common were visual, auditory, imagery, and memory recall), and in the stimuli used (faces, pictures, films, words, and others)."
   - W2015 Limitations: "Some regions—particularly the brainstem—are likely to be much more important for understanding and diagnosing emotion than is apparent in our findings"; "the ventromedial prefrontal cortex (e.g., BA 25 and posterior portions of medial OFC) are subject to signal loss and distortion, and are likely to be under-represented."

### Notice

"Move the Display cut slider up from 0.001, then tick "show unthresholded": which regions stay coloured longest?"
- UI.

### Claims (shown with DOI links under the lesson)

- "The five emotion maps come from a Bayesian meta-analysis of 148 studies; each map shows the expected number of activation centres per voxel and was thresholded at 0.001 for display only." doi:10.1371/journal.pcbi.1004066 (quotes: body items 1–3)
- "The brainstem and ventromedial prefrontal cortex are likely to be under-represented in these results." doi:10.1371/journal.pcbi.1004066 (quote: body item 5)

---

## Lesson 2: Five emotions, one brain

- **id:** `five-emotions` · **map_ids:** `anger, disgust, fear, happiness, sadness` · **view:** both
- **Status:** maps verified.

### Body

1. "All five maps come from the same model and use the same units, so here, and only here, they share one colour scale."
   - spec §8.1 (project rule). One BSPP model for all five categories (W2015).
2. "The authors report that regions such as the amygdala, insula, anterior cingulate cortex and brainstem were likely to be active in all five emotions, though with different and meaningful distributions within each region."
   - W2015: "Notably, limbic and paralimbic regions such as the amgydala, ventral striatum, orbitofrontal cortex (OFC), anterior cingulate cortex (ACC), brainstem, and insula were likely to be active in all emotion categories, though with different and meaningful distributions within each region".
3. "In the "Relative to region size" view the amygdala has the highest value for all five emotions (about 8 to 18 times the average density), but this reflects reported peaks in and around it: a small structure's value is easily swung by a few nearby peaks, which the model's spatial spread carries in from neighbouring tissue, and it does not mean that emotion happens there."
   - profiles.json, *size_normalised*, Amygdala: sadness 8.13, happiness 9.57, disgust 11.36, anger 12.93, fear 17.69. For every emotion this is the highest of the 11 regions.
   - Size-normalising gives the true average density, so the value is not inflated by size. But a small structure's average rests on few voxels, so a few nearby peaks swing it.
   - "Spatial spread": W2015, Fig. 1 legend: the method "models the population density of activation across the brain with a sparse set of multivariate Gaussian distributions at two levels (study center and population center)".
   - "Reflects reported peaks": the value definition (Lesson 1, item 2).
4. "The authors also warn that amygdala values for negative emotions may be over-represented because the field has focused on fear."
   - W2015 Limitations: "our analyses reflect the composition of the studies available in the literature, and are subject to testing and reporting biases on the part of authors. This is particularly true for the amygdala (e.g., the activation intensity for negative emotions may be over-represented in the amygdala given the theoretical focus on fear and related negative states)."
5. "Every emotion places some intensity in all seven cortical networks, and about 42–48% of each map lies outside the labelled regions, for example in white matter, cerebellum and basal ganglia."
   - profiles.json, *share*: the smallest cortical-network share for any emotion is fear / Limbic = 0.0227. None is zero.
   - profiles.json, *unassigned*: 0.419 (disgust) to 0.483 (sadness).
   - The examples follow from the atlas: Yeo-7 covers cortex only, and the subcortical labels cover only amygdala, hippocampus, thalamus and brainstem (`site/public/data/atlas.json`).
6. "No emotion mapped onto a single cortical network, and an earlier review found no consistent one-region-per-emotion mapping (Lindquist et al., 2012)."
   - W2015: "Second, no emotion category mapped to any single cortical network, but emotion categories could be distinguished by significant differences in their profiles across networks".
   - L2012 headline finding.

### Notice

"Show fear alone, then add the other four: is any coloured region fear's alone?"
- UI.

### Claims

- "Emotion categories were not contained within any one region or system, but were represented as configurations across multiple brain networks." doi:10.1371/journal.pcbi.1004066
  - W2015 abstract: "The results indicate that emotion categories are not contained within any one region or system, but are represented as configurations across multiple brain networks."
- "Limbic and paralimbic regions such as the amygdala, insula, anterior cingulate cortex and brainstem were likely to be active in all five emotion categories, though with different and meaningful distributions within each region." doi:10.1371/journal.pcbi.1004066 (quote: body item 2)
- "Amygdala activation intensity for negative emotions may be over-represented, given the field's theoretical focus on fear." doi:10.1371/journal.pcbi.1004066 (quote: body item 4)
- "No emotion category mapped to any single cortical network; categories differed in their profiles across networks." doi:10.1371/journal.pcbi.1004066 (quote: body item 6)
- "A meta-analytic review found no consistent mapping of each emotion to a single brain region." doi:10.1017/S0140525X11000446 (L2012 headline)

Removed in fix round 1: the paper's anger/fear vs disgust/sadness/happiness network grouping. Our profile bars, computed with a different measure, do not show it. For example, fear has the lowest Frontoparietal value of the five (share 0.0316, size-normalised 0.53).

---

## Lesson 3: Fear vs anxiety (anxiety map NOT yet verified)

- **id:** `fear-vs-anxiety` · **map_ids:** `fear, anxiety` · **view:** both
- **Status:** anxiety map (NeuroVault 6012) unverified; its paper and DOI are unknown. Until it is verified, the site shows "This lesson needs data not yet available" and hides this text.

### Body

1. "Anxiety appears here not as a sixth basic emotion but as a contrast with fear."
   - spec §6.2: "Presented as a contrast to fear (sustained anticipation of uncertain threat), **not** as a sixth basic emotion." (project framing)
2. "In the usual research framing, fear is the response to a threat that is present and identifiable; anxiety is a more sustained apprehension about a threat that is uncertain or not yet here, such as waiting for a shock that may or may not come."
   - **NEEDS SOURCE.** To be checked against the verified map and paper. The spec's description of 6012 as "mostly threat-of-shock" is itself unverified.
3. "The two maps come from different studies with different methods, so they never share a colour scale; compare their network profiles, which show where each map's evidence lies, not how strong it is."
   - "Different studies" and the comparison rule: spec §8.1 and §8.2.
   - "Different methods": **NEEDS SOURCE**. The spec says 6012 is an SDM meta-analysis (unverified).
4. "Even the fear map lies mostly outside the amygdala: about 94% of its intensity falls elsewhere ("Share of evidence" view), although relative to its size the amygdala is far denser than, for example, the default mode network (about 18 against about 1, "Relative to region size" view)."
   - profiles.json, fear: Amygdala *share* 0.0578, so 1 − 0.0578 ≈ 0.94.
   - profiles.json, fear *size_normalised*: Amygdala 17.69, Default mode 1.03.
5. "Look for parts of the two profiles that are shared and parts that differ, rather than for one region that separates the two states."
   - An instruction, not a claim. It deliberately predicts no result for anxiety.

### Notice

"In the "Relative to region size" view, where do the fear and anxiety profiles agree, and where do they part?"
- UI. The question does not presuppose an answer.

### Claims (in lessons.json; Wager and Lindquist only)

- "Emotion categories, fear included, were not contained within any one region or system, but were represented as configurations across multiple brain networks." doi:10.1371/journal.pcbi.1004066 (W2015 abstract, quoted under Lesson 2)
- "A meta-analytic review found no consistent mapping of each emotion to a single brain region." doi:10.1017/S0140525X11000446

### Pending claims (NOT in lessons.json; no DOI yet)

- "Anxiety is a sustained response to uncertain or anticipated threat, whereas fear is a response to present, identifiable threat." **NEEDS SOURCE**
- "Induced anxiety in healthy volunteers and fear share parts of their network profiles but differ in others." **NEEDS SOURCE**: only add this once the verified anxiety profile actually shows it.

---

## Lesson 4: Memory retrieval and the default mode network (retrieval map NOT yet verified)

- **id:** `retrieval-dmn` · **map_ids:** `retrieval` · **view:** both
- **Status:** retrieval map (NeuroVault 12234) unverified; its paper and DOI are unknown. Hidden on the site until it is verified.

### Body

1. "Episodic memory retrieval means bringing back a specific past event: what happened, where and when."
   - **NEEDS SOURCE** (textbook definition; check the wording against the verified paper's definition).
2. "Retrieval is generally reported to engage the hippocampus together with regions of the default mode network, such as the posterior cingulate cortex and precuneus, medial prefrontal cortex and lateral parietal cortex."
   - **NEEDS SOURCE.** To be checked against the verified map and paper. The spec gives the collection title as "Default network activation during episodic and semantic memory retrieval: a selective meta-analytic comparison" (unverified).
3. "The default mode network is not only a memory network: the emotion meta-analysis describes it as consistently engaged in semantic memory, person perception, imagining the future and emotion."
   - W2015: "It is consistently engaged during conceptual processes such as semantic memory [63], person perception [64,65], and prospection about future events [66], as well as in emotion [36,67], valuation, and conceptually driven autonomic and neuroendocrine responses".
   - W2015 says this in its Discussion, citing other work; it is not a result of the emotion meta-analysis itself.
   - That the network is also engaged in *episodic* retrieval (implied by "not only") is **NEEDS SOURCE** (the verified retrieval paper).
4. "The hippocampus is small, so judge it in the "Relative to region size" view rather than by the length of its "Share of evidence" bar."
   - Describes how the profile measures work (spec §8.2; `profile.py`). Example: fear Hippocampus *share* 0.030 but *size_normalised* 4.43.
5. "Like every map here, this one is a statistical result with its own method and threshold; read the info panel before reading the colours."
   - spec §1 (project framing).

### Notice

"Is the evidence for retrieval confined to the default mode network or to the hippocampus?"
- UI. The question does not presuppose an answer.

### Claims (in lessons.json)

- "The default mode network is consistently engaged during conceptual processes such as semantic memory, person perception and prospection about future events, as well as in emotion." doi:10.1371/journal.pcbi.1004066 (quote: body item 3)

### Pending claims (NOT in lessons.json)

- "Episodic memory retrieval engages the hippocampus and default mode network regions (posterior cingulate/precuneus, medial prefrontal cortex, lateral parietal cortex)." **NEEDS SOURCE**: the verified retrieval paper.
- Any number about the retrieval profile. Leave these out until the map is built; the numbers must come from profiles.json.

---

## Lesson 5: Fear vs retrieval (retrieval map NOT yet verified)

- **id:** `fear-vs-retrieval` · **map_ids:** `fear, retrieval` · **view:** both
- **Status:** depends on the unverified retrieval map. Hidden on the site until it is verified.

### Body

1. "The amygdala lies just anterior to the hippocampal head in the medial temporal lobe; being neighbours does not mean doing the same thing, and neither structure does only one thing."
   - Anatomy: **NEEDS SOURCE** (standard neuroanatomy; please confirm the wording).
   - "Neither structure does only one thing" is supported on the emotion side by W2015. The amygdala showed "appreciable intensity in all five emotion categories". Also: "regions typically labeled as 'cognitive' or 'perceptual' were also engaged ... including ... hippocampus".
   - For the memory side it is **NEEDS SOURCE**.
2. "The fear map already reaches the hippocampus: relative to its size, the hippocampus holds about 4 times the average density of the labelled regions in the fear profile, second only to the amygdala at about 18 ("Relative to region size" view)."
   - profiles.json, fear, *size_normalised*: Amygdala 17.69, Hippocampus 4.43. The next highest is Thalamus at 2.11.
3. "Fear's density in the default mode network is about average for the labelled regions (about 1 in the "Relative to region size" view); that network is generally reported to be engaged during memory retrieval too."
   - profiles.json, fear: Default mode *size_normalised* 1.03.
   - "Engaged during memory retrieval": **NEEDS SOURCE** (the verified retrieval paper).
4. "The two maps come from different studies and methods, so compare their profiles, not their colours; the profiles show where the evidence lies, not how strong it is."
   - spec §8.1 and §8.2.
   - "Different methods": **NEEDS SOURCE** until the retrieval method is verified.
5. "Ask whether the two conditions differ in which regions they use at all, or in how their evidence is weighted across the same networks."
   - An instruction, not a claim.

### Notice

"In the "Relative to region size" view, compare the amygdala, hippocampus and default mode bars for fear and for retrieval."
- UI. The site does not label subcortical regions on the brain (atlas licence), so the notice points to the profile bars instead.

### Claims (in lessons.json)

- "The hippocampus was among the regions engaged across emotion categories, and hippocampal profiles helped distinguish fear from anger." doi:10.1371/journal.pcbi.1004066
  - W2015: "In addition, regions typically labeled as 'cognitive' or 'perceptual' were also engaged and potentially differentially engaged across categories, including ventromedial, dorsomedial, and ventrolateral prefrontal cortices (vmPFC, dmPFC, and vlPFC), posterior cingulate (PCC), hippocampus, and medial temporal lobes, and occipital regions."
  - W2015: "whereas cortical networks discriminated the fear and anger categories from the other emotions, hippocampal and cerebellar/brainstem profiles discriminated fear from anger".
- "The default mode network is consistently engaged during conceptual processes such as semantic memory, person perception and prospection about future events, as well as in emotion." doi:10.1371/journal.pcbi.1004066

### Pending claims (NOT in lessons.json)

- "The default mode network is engaged during episodic memory retrieval." **NEEDS SOURCE**: the verified retrieval paper.
- "Fear and retrieval differ mainly in how evidence is weighted across shared networks / in the structures involved." **NEEDS SOURCE**. Only add this if the verified retrieval profile shows it.

---

## Caveats (the `caveat:` field in `pipeline/sources.yaml`, shown in each map's info panel)

Every Wager caveat is two sentences. Sentence 1 is the same for all five:

> S1: "Shows where studies of {emotion} tended to report activation peaks, as estimated by a statistical model; no single coloured region is specific to {emotion}; what differs between emotions is the overall pattern."

The standard second sentence (anger, disgust, happiness):

> S2: "The map has no negative values, so it cannot show decreases, and the 0.001 cut is a display choice, not a significance test."

Fear and sadness use their own second sentence (see the table). Their info panels still show the display-threshold label.

Sources for S1 and S2:
- "Not specific" (W2015 Introduction): "the regions most reliably activated—e.g., the anterior cingulate, anterior insula, amygdala, and orbitofrontal cortex—are activated in multiple categories of emotions [12], and during many other sensory, perceptual and cognitive events [11,13]. Thus, activation of these regions is not specific to one emotion category or even emotion more generally."
- "Overall pattern" (W2015 abstract): "emotion categories are not contained within any one region or system, but are represented as configurations across multiple brain networks."
- "No negative values": spec §6.1.
- "0.001 display": W2015 Fig. 1 legend.

The dataset-wide limitations (varied tasks; brainstem and vmPFC under-represented) were moved into Lesson 1, item 5. They apply to all five maps equally.

| Map | Caveat | Extra source |
|---|---|---|
| anger | S1 + S2 | — |
| disgust | S1 + S2 | — |
| fear | S1 + "The map has no negative values, so it cannot show decreases, and the authors warn that amygdala values for negative emotions may be over-represented because the field has focused on fear." | W2015 Limitations: "the activation intensity for negative emotions may be over-represented in the amygdala given the theoretical focus on fear and related negative states". The same warning also appears in Lesson 2, item 4. |
| happiness | S1 + S2 | — |
| sadness | S1 + "The map has no negative values, so it cannot show decreases; in-scanner sadness tasks are typically low-arousal, so it may not represent intense grief." | W2015: "sadness can be high-arousal, but in-scanner sadness manipulations are typically low-arousal". "Intense grief" is Claude's example. |
| anxiety | "Anxiety is shown as a contrast with fear (sustained apprehension about uncertain threat), not as a basic emotion; this map does not show anxiety disorders or a region specific to anxiety. Its values come from a different method than the emotion maps, so the two cannot be compared colour for colour." | **NEEDS SOURCE / generic.** The framing is from spec §6.2. "Not anxiety disorders" assumes the map finally chosen is the induced-anxiety-in-healthy-participants map (spec target, unverified). "Different method" assumes SDM (spec, unverified). Re-check both once the map is verified. |
| retrieval | "Shows where studies of remembering past events reported increases relative to their control tasks; it does not show where memories are stored, and the regions it highlights are not specific to memory. Its method differs from the emotion maps, so compare it with them only through the network profile." | **NEEDS SOURCE / generic.** "Increases relative to control" assumes the spec §6.3 acceptance rule (a retrieval-vs-control/baseline map) is met. "Not specific to memory" is general background. Re-check once the map is verified. |

---

## Questions for the reviewer

1. **"Cannot show decreases"** (Lesson 1, item 4, and the Wager caveats). The paper never discusses decreases. The statement rests on the foci coming from emotion-vs-comparison contrasts and on every map value being ≥0. Is "cannot show decreases" fair?
2. **The 34–55% coverage figure** (Lesson 1, item 3) is a project measurement, not a number from the paper. Keep it?
3. **Visual network.** Fear's profile has a visual-network share of 0.132. The paper reports that 90% of fear studies used visual images ("2% of studies used recall and 90% used visual images to induce fear"). The lessons no longer quote the visual figure. Should the stimulus point be added to the fear caveat?
4. **Amygdala framing** (Lesson 2, items 3–4). Is the explanation of the high size-normalised amygdala value clear and correct for students?
5. **Lessons 3–5:** every NEEDS SOURCE sentence must be confirmed or replaced once the anxiety and retrieval maps and their papers are verified. Keep them as placeholders, or cut them to the bare instructions until then? They are hidden on the site while the maps are unavailable.
6. **Anatomy wording** (Lesson 5, item 1): "just anterior to the hippocampal head". Would you add "and partly superior"?
