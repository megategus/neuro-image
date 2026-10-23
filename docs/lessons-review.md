# Lesson and caveat text: medical review

**For the reviewer.** Everything below is a draft written by Claude. It is not a medical review. Please check three things: (1) every sentence is medically and scientifically correct for a medical-student audience; (2) no sentence calls a region the centre of a function or suggests that one region does one job; (3) every factual sentence matches the source given next to it. Sentences marked **NEEDS SOURCE** are general background with no verified source yet. Each must be checked against the anxiety or retrieval map and its paper once those are verified, or cut. Edit the text in `pipeline/lessons/lessons.json` (lessons) and `pipeline/sources.yaml` (the `caveat:` field of each map). When you are satisfied, set `"reviewed": true` at the top of `pipeline/lessons/lessons.json` and rebuild (`cd pipeline && uv run python -m atlas_pipeline build --out ../site/public/data`). Until you do, the deploy build refuses to publish.

Source key:
- **W2015**: Wager, Kang, Johnson, Nichols, Satpute, Barrett (2015) *PLoS Comput Biol* 11:e1004066, doi:10.1371/journal.pcbi.1004066. Quotes are verbatim from the full text. Line breaks are joined, and the PDF's own typos ("amgydala") are kept.
- **L2012**: Lindquist, Wager, Kober, Bliss-Moreau, Barrett (2012) *Behav Brain Sci* 35:121–143, doi:10.1017/S0140525X11000446. No full text was available, so only its well-known headline finding is used.
- **profiles.json**: `site/public/data/profiles.json`, the network profiles this build produced. *Share* is the fraction of the map's total positive intensity that falls in a region (the "Share of evidence" view). *Size-normalised* is that region's share of intensity divided by its share of atlas voxels, counting labelled atlas regions only, so 1 = average density (the "Relative to region size" view). About 43–48% of each emotion map's intensity falls outside the atlas regions (`unassigned`).
- **spec**: `docs/superpowers/specs/2026-10-23-brain-condition-atlas-design.md` (project design decisions, not science).
- **UI**: an instruction about this site's controls, not a factual claim.

---

## Lesson 1: Reading a meta-analytic map

- **id:** `reading-maps` · **map_ids:** `fear` · **view:** overlay (brain only)
- **Status:** map verified.

### Body

1. "This is not a picture of a brain at work. It is a statistical summary of 148 published PET and fMRI studies of five emotions (Wager et al., 2015), built from the peak coordinates those studies reported."
   - W2015: "Our analysis included 148 PET and fMRI studies published from 1993 to 2011 (377 maps, 2159 participants) that attempted to specifically cultivate one of the five most commonly studied categories of emotion". Also: "At Level 1 is the individual study data, in the form of peak coordinate locations."
2. "Each voxel holds the model's "posterior expected number of activation centres": added up over a region, it estimates how many consistently reported activation sites fall there when a study targets fear. It is not a signal strength, a percentage or a p-value."
   - W2015: "the intensity function map representing the spatial posterior expected number of activation or population centers in each area across the brain given the emotion category". Fig. 1 legend: "their integral over any portion of the brain reflects the expected number of activation centers in that area for all studies with a particular emotion."
   - "Not a signal strength, a percentage or a p-value" is Claude's paraphrase of what that definition rules out.
3. "The default cut of 0.001 is the value the authors used to draw their figures. It is a display choice, not a significance test: no voxel in this map has been tested and found "significant"."
   - W2015, Fig. 1 legend: "The maps are thresholded for display at a voxel-wise intensity of 0.001 or above."
   - spec §4 and §6.1: "Display threshold only; no significance test exists for these voxels."
4. "At that cut each of the five emotion maps colours roughly a third to a half of the brain (34–55%), so colour alone says little. Look at where values are highest, and at how the picture changes as you move the cut."
   - spec §6.1 verified property: "At 0.001 the maps cover 34–55% of the brain."
   - Re-measured for this review from the built maps, as voxels ≥0.001 out of the 212,401-voxel brain mask: anger 50.3%, disgust 34.4%, fear 54.5%, happiness 40.3%, sadness 33.8%. These figures come from our own measurement, not from the paper.
5. "The studies compared an emotion condition with a neutral or less intense one, and the model uses only the reported peaks of increases. Decreases therefore cannot appear on this map; their absence is not a finding."
   - W2015: "Foci are nested within study activation maps, maps of group comparisons between an emotion- or affect-related condition and a less intense or affectively neutral comparison condition."
   - spec §8.2: "Emotion maps have no negatives *by method* (a point-process model only counts reported peaks)". The paper does not say in so many words that only increase peaks were used. Claude inferred it from the quote above and from all map values being ≥0 (see Questions).

### Notice

"Move the Display cut slider up from 0.001, then tick "show unthresholded". The data never change, only how much of them you choose to see. Which regions stay coloured longest?"
- UI.

### Claims (shown with DOI links under the lesson)

- "The five emotion maps come from a Bayesian meta-analysis of 148 studies; each map shows the expected number of activation centres per voxel and was thresholded at 0.001 for display only." doi:10.1371/journal.pcbi.1004066 (quotes as in body items 1–3).

---

## Lesson 2: Five emotions, one brain

- **id:** `five-emotions` · **map_ids:** `anger, disgust, fear, happiness, sadness` · **view:** both
- **Status:** maps verified.

### Body

1. "All five maps come from the same model and use the same units, so here, and only here, they share one colour scale."
   - spec §8.1 (project rule). Same model and units: W2015, one BSPP model for all five categories.
2. "Start with the overlap. The authors report that regions such as the amygdala, insula, anterior cingulate cortex and brainstem were likely to be active in all five emotion categories."
   - W2015: "Notably, limbic and paralimbic regions such as the amgydala, ventral striatum, orbitofrontal cortex (OFC), anterior cingulate cortex (ACC), brainstem, and insula were likely to be active in all emotion categories, though with different and meaningful distributions within each region".
3. "The network profile shows the same thing: every emotion puts some of its map intensity into each of the seven cortical networks, and the amygdala stands out for all five, not just fear. Relative to its size, it holds about 8 to 18 times the average density of the labelled regions ("Relative to region size" view)."
   - profiles.json, *share*: the smallest cortical-network share for any emotion is happiness / Dorsal attention = 0.023 (2.3%). No share is zero.
   - profiles.json, *size_normalised*, Amygdala: sadness 8.13, happiness 9.57, disgust 11.36, anger 12.93, fear 17.69. For every emotion this is the highest of all 11 regions.
   - W2015 supports the same point: "Even the zones most differentially engaged in terms of average intensity, such as the amgydala (Fig. 2B), showed appreciable intensity in all five emotion categories (see also Fig. 1), consistent with previous meta-analyses."
4. "What separates the emotions is the pattern across networks. No emotion mapped onto a single cortical network; anger and fear leaned towards the dorsal attention, frontoparietal and default mode networks, while disgust, sadness and happiness leaned towards the ventral attention (salience) and somatomotor networks."
   - W2015: "Second, no emotion category mapped to any single cortical network, but emotion categories could be distinguished by significant differences in their profiles across networks".
   - W2015: "We found that in the cortex, anger and fear categories are very similar, and preferentially activate 'dorsal attention,' fronto-parietal,' and 'default mode' networks (as defined by resting-state connectivity). Happiness, sadness, and disgust categories belong to another, distinct group, with preferential activity in somatomotor and 'ventral attention' (or 'salience') networks."
   - Note: the paper's network values are *mean intensity per network* over its own 49 regions. Our profile bars use a different measure (share and size-normalised share), so the bars need not reproduce this grouping exactly. The sentence is attributed to the authors, not to our chart.
5. "An earlier meta-analytic review reached the same headline: no consistent one-region-per-emotion mapping (Lindquist et al., 2012)."
   - L2012 headline finding, as provided. No full text available.

### Notice

"Show fear alone, then add the other four. Is there any coloured region that belongs to fear and to nothing else? Then switch the profile to "Relative to region size" and compare the amygdala bars across all five emotions."
- UI.

### Claims

- "Emotion categories were not contained within any one region or system, but were represented as configurations across multiple brain networks." doi:10.1371/journal.pcbi.1004066
  - W2015 abstract: "The results indicate that emotion categories are not contained within any one region or system, but are represented as configurations across multiple brain networks."
- "Limbic and paralimbic regions such as the amygdala, insula, anterior cingulate cortex and brainstem were likely to be active in all five emotion categories." doi:10.1371/journal.pcbi.1004066 (quote: body item 2)
- "No emotion category mapped to any single cortical network; anger and fear shared one cortical profile, and disgust, sadness and happiness another." doi:10.1371/journal.pcbi.1004066 (quotes: body item 4)
- "A meta-analytic review found no consistent mapping of each emotion to a single brain region." doi:10.1017/S0140525X11000446 (L2012 headline)

---

## Lesson 3: Fear vs anxiety (anxiety map NOT yet verified)

- **id:** `fear-vs-anxiety` · **map_ids:** `fear, anxiety` · **view:** both
- **Status:** anxiety map (NeuroVault 6012) unverified; its paper and DOI are unknown. Until it is verified, the site shows "This lesson needs data not yet available" and hides this text.

### Body

1. "Anxiety appears here not as a sixth basic emotion but as a contrast with fear."
   - spec §6.2: "Presented as a contrast to fear (sustained anticipation of uncertain threat), **not** as a sixth basic emotion." (project framing)
2. "In the usual research framing, fear is the response to a threat that is present and identifiable; anxiety is a more sustained apprehension about a threat that is uncertain or not yet here, such as waiting for a shock that may or may not come."
   - **NEEDS SOURCE.** To be checked against the verified map and paper. The spec says the 6012 induced-anxiety studies were "mostly threat-of-shock", which is unverified.
3. "The two maps come from different studies with different methods, so they never share a colour scale. Compare them through their network profiles, which show where each map's evidence lies, not how strong it is."
   - spec §8.1 and §8.2 (project rule; the chart shows the same note).
4. "Even the fear map alone spreads well beyond the amygdala: about 6% of its total intensity lies in the amygdala, against about 12% in the default mode network and 13% in the visual network ("Share of evidence" view)."
   - profiles.json, fear, *share*: Amygdala 0.0578, Default mode 0.1155, Visual 0.1317.
5. "Look for parts of the two profiles that are shared and parts that differ, rather than for one region that separates the two states."
   - An instruction, not a claim. It deliberately predicts no result for anxiety.

### Notice

"In the "Relative to region size" view, compare the amygdala bar for fear and anxiety, then the seven cortical networks. Where do the two profiles agree, and where do they part?"
- UI. The questions do not presuppose an answer.

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
3. "The default mode network is a set of regions that are typically more active at rest than during many outward-focused tasks. It is not a memory network: the emotion meta-analysis notes it is also engaged in semantic memory, thinking about other people, imagining the future and emotion."
   - First sentence: **NEEDS SOURCE** (general background).
   - Second sentence: W2015: "It is consistently engaged during conceptual processes such as semantic memory [63], person perception [64,65], and prospection about future events [66], as well as in emotion [36,67], valuation, and conceptually driven autonomic and neuroendocrine responses".
4. "The hippocampus is small, so in the "Share of evidence" view its bar looks short even when its evidence is dense. The "Relative to region size" view corrects for size."
   - Describes how the profile measures work (spec §8.2; `pipeline/src/atlas_pipeline/profile.py`). The fear profile shows the effect: Hippocampus share 0.030 but size-normalised 4.43.
5. "Like every map here, this one is a statistical result with its own method and threshold; read the info panel before reading the colours."
   - spec §1 (project framing).

### Notice

"Compare the default mode bar with the other six networks, then check the hippocampus in the "Relative to region size" view. Is the evidence for retrieval confined to either?"
- UI. The question does not presuppose an answer.

### Claims (in lessons.json)

- "The default mode network is consistently engaged during conceptual processes such as semantic memory, person perception and prospection about future events, as well as in emotion." doi:10.1371/journal.pcbi.1004066 (quote: body item 3)

### Pending claims (NOT in lessons.json)

- "Episodic memory retrieval engages the hippocampus and default mode network regions (posterior cingulate/precuneus, medial prefrontal cortex, lateral parietal cortex)." **NEEDS SOURCE**: the verified retrieval paper.
- Any number about the retrieval profile (for example its default mode share). Leave these out until the map is built; the numbers must come from profiles.json.

---

## Lesson 5: Fear vs retrieval (retrieval map NOT yet verified)

- **id:** `fear-vs-retrieval` · **map_ids:** `fear, retrieval` · **view:** both
- **Status:** depends on the unverified retrieval map. Hidden on the site until it is verified.

### Body

1. "The amygdala and the hippocampus lie side by side in the medial temporal lobe. Being neighbours does not mean doing the same thing, and neither structure does only one thing."
   - Anatomy: standard neuroanatomy (please confirm).
   - "Neither structure does only one thing" is supported for the emotion side by W2015: the amygdala showed "appreciable intensity in all five emotion categories", and "regions typically labeled as 'cognitive' or 'perceptual' were also engaged ... including ... hippocampus". For the memory side it is **NEEDS SOURCE**.
2. "The fear map already reaches the hippocampus: relative to its size, the hippocampus holds about 4 times the average density of the labelled regions in the fear profile, second only to the amygdala at about 18 ("Relative to region size" view)."
   - profiles.json, fear, *size_normalised*: Amygdala 17.69, Hippocampus 4.43. The next highest is Thalamus at 2.11.
   - W2015: "whereas cortical networks discriminated the fear and anger categories from the other emotions, hippocampal and cerebellar/brainstem profiles discriminated fear from anger".
3. "Fear also places about 12% of its map intensity in the default mode network ("Share of evidence" view), a network that is generally reported to be engaged during memory retrieval as well."
   - profiles.json, fear, *share*: Default mode 0.1155.
   - "Generally reported to be engaged during memory retrieval": **NEEDS SOURCE** (the verified retrieval paper).
4. "The two maps come from different studies and methods, so compare their profiles, not their colours; the profiles show where the evidence lies, not how strong it is."
   - spec §8.1 and §8.2 (project rule).
5. "Ask whether the two conditions differ in which regions they use at all, or in how their evidence is weighted across the same networks."
   - An instruction, not a claim.

### Notice

"In the "Relative to region size" view, compare the amygdala and hippocampus bars for fear and for retrieval, then the default mode bar. Which differences are about structures, and which about weighting?"
- UI. Note that the site does not label subcortical regions on the brain (atlas licence), so the notice points to the profile bars instead.

### Claims (in lessons.json)

- "The hippocampus was among the regions engaged across emotion categories, and hippocampal profiles helped distinguish fear from anger." doi:10.1371/journal.pcbi.1004066
  - W2015: "In addition, regions typically labeled as 'cognitive' or 'perceptual' were also engaged and potentially differentially engaged across categories, including ventromedial, dorsomedial, and ventrolateral prefrontal cortices (vmPFC, dmPFC, and vlPFC), posterior cingulate (PCC), hippocampus, and medial temporal lobes, and occipital regions." Plus the fear/anger quote under body item 2.
- "The default mode network is consistently engaged during conceptual processes such as semantic memory, person perception and prospection about future events, as well as in emotion." doi:10.1371/journal.pcbi.1004066

### Pending claims (NOT in lessons.json)

- "The default mode network is engaged during episodic memory retrieval." **NEEDS SOURCE**: the verified retrieval paper.
- "Fear and retrieval differ mainly in how evidence is weighted across shared networks / in the structures involved." **NEEDS SOURCE**. Only add this if the verified retrieval profile shows it.

---

## Caveats (the `caveat:` field in `pipeline/sources.yaml`, shown in each map's info panel)

The five Wager maps share one core sentence:

> "Shows where studies of {emotion} tended to report activation increases, as estimated by a statistical model; the coloured regions are not specific to {emotion}, decreases cannot appear by method, and the 0.001 cut is a display choice, not a significance test."

Sources for the core sentence:
- "Increases": W2015's comparison-condition quote (Lesson 1, body item 5).
- "Not specific": W2015 Introduction: "the regions most reliably activated—e.g., the anterior cingulate, anterior insula, amygdala, and orbitofrontal cortex—are activated in multiple categories of emotions [12], and during many other sensory, perceptual and cognitive events [11,13]. Thus, activation of these regions is not specific to one emotion category or even emotion more generally."
- "Decreases": spec §8.2.
- "0.001 display": W2015 Fig. 1 legend.

| Map | Caveat | Extra source |
|---|---|---|
| anger | core sentence only | — |
| disgust | core + "Regions that are hard to image, such as the brainstem and ventromedial prefrontal cortex, are probably under-represented." | W2015 Limitations: "Some regions—particularly the brainstem—are likely to be much more important ... than is apparent in our findings"; "the ventromedial prefrontal cortex ... are subject to signal loss and distortion, and are likely to be under-represented." (This applies to all five maps; it was put on disgust only to vary the text. See Questions.) |
| fear | core + "The authors note that amygdala values for negative emotions may be inflated by the field's long focus on fear." | W2015 Limitations: "This is particularly true for the amygdala (e.g., the activation intensity for negative emotions may be over-represented in the amygdala given the theoretical focus on fear and related negative states)." |
| happiness | core + "It pools varied in-scanner tasks (faces, pictures, films, recall), not happiness as experienced in everyday life." | W2015: "The studies were relatively heterogeneous in their methods for eliciting emotion (the most common were visual, auditory, imagery, and memory recall), and in the stimuli used (faces, pictures, films, words, and others)." The "not everyday life" part is Claude's framing. |
| sadness | core + "In-scanner sadness tasks are typically low-arousal, so the map may not represent intense grief." | W2015: "sadness can be high-arousal, but in-scanner sadness manipulations are typically low-arousal". "Intense grief" is Claude's example. |
| anxiety | "Anxiety is shown as a contrast with fear (sustained apprehension about uncertain threat), not as a basic emotion; this map does not show anxiety disorders or a region specific to anxiety. Its values come from a different method than the emotion maps, so the two cannot be compared colour for colour." | **NEEDS SOURCE / generic.** The framing is from spec §6.2. "Not anxiety disorders" assumes the map finally chosen is the induced-anxiety-in-healthy-participants map (spec target, unverified). "Different method" assumes SDM (spec, unverified). Re-check both once the map is verified. |
| retrieval | "Shows where studies of remembering past events reported increases relative to their control tasks; it does not show where memories are stored, and the regions it highlights are not specific to memory. Its method differs from the emotion maps, so compare it with them only through the network profile." | **NEEDS SOURCE / generic.** "Increases relative to control" assumes the spec §6.3 acceptance rule (a retrieval-vs-control/baseline map) is met. "Not specific to memory" is general background. Re-check once the map is verified. |

---

## Questions for the reviewer

1. **"Decreases cannot appear by method" (Lesson 1, item 5, and all five Wager caveats).** The paper says the foci came from emotion-vs-neutral/less-intense comparison maps, and every map value is ≥0. The paper does not say that deactivation foci were excluded. Is "cannot show decreases" fair, or should it be softened to "this map does not show decreases"?
2. **"Not specific to {emotion}" in the caveats.** The paper's point is that *single regions* are not specific, while the *whole pattern* does help predict the category (66% mean accuracy). Does the caveat need "single regions are not specific…" so students don't read it as "the maps cannot tell emotions apart"?
3. **The 34–55% coverage figure (Lesson 1, item 4)** is a project measurement, not a number from the paper. Keep it?
4. **The visual network share for fear (13%)** may partly reflect stimuli. The paper reports 90% of fear studies used visual images. Should Lesson 3 mention this, or leave the visual figure out?
5. **The amygdala is the densest region for all five emotions** in our size-normalised profile, and densest of all for fear (17.7). The paper warns that amygdala values for negative emotions may be inflated by reporting bias. Is the Lesson 2 framing ("stands out for all five, not just fear") the right lesson to draw, and does it need that warning next to it?
6. **About 43–48% of each emotion map's intensity is "unassigned"** (outside our 11 atlas regions: for example cerebellum, basal ganglia, white matter). The chart shows this row, but no lesson explains it. Add one sentence to Lesson 2?
7. **Wager's network grouping vs our bars.** Lesson 2, item 4 attributes the anger/fear vs disgust/sadness/happiness grouping to the authors, who used mean intensity over their own regions. Our share bars may not show the grouping clearly. Should the sentence say so, or be dropped?
8. **The under-representation caveat** (brainstem, vmPFC) applies to all five maps but sits on disgust only. Move it into the core sentence (longer) or leave it?
9. **Lessons 3–5:** every NEEDS SOURCE sentence must be confirmed or replaced once the anxiety and retrieval maps and their papers are verified. Do you want them kept as placeholders, or cut to the bare instructions until then? They are hidden on the site while the maps are unavailable.
10. **Anatomy wording** (Lesson 5, item 1): is "lie side by side in the medial temporal lobe" precise enough for your students, or would you prefer "the amygdala lies just anterior/superior to the hippocampal head"?
