# Yang 2026: mLLMCelltype, multi-LLM consensus for cell type annotation

**Reference:** Yang C, Zhang X, Chen J. (2026). *Large language model consensus substantially improves the cell type annotation accuracy for scRNA-seq data.* Communications Biology. DOI: 10.1038/s42003-026-10420-8 (received 18 Aug 2025; accepted 27 May 2026)
**Resource:** [Article](https://doi.org/10.1038/s42003-026-10420-8). Open-source package and web server; links are in the paper's code availability section.
**Open access:** yes, CC BY-NC-ND 4.0. The unedited PDF can be shared as-is; don't redistribute modified versions.
**Version note:** drafted from the unedited "Article in Press" manuscript. **Its figures are blank placeholders**, so every number here comes from the text. Check against the final published version.
**Species / tissue:** 49 benchmark datasets across diverse tissues, species, and sequencing technologies (e.g., Tabula Sapiens, Human Lung Cell Atlas, a developmental thymus atlas, GTEx, HuBMAP, and a lifespan human immune atlas). No tumor-specific evaluation is described in the main text.
**Taxonomy level:** Not tied to a level. A **method lessons** paper, including an explicit method for **hierarchical (level-by-level) annotation**.

## Why it's in the knowledge base
1. **A tested way to annotate a hierarchy with an LLM.** When annotating a finer level, the LLM is told the cluster's parent label and given markers comparing the cluster with its **sibling clusters** (clusters sharing the same parent), not just with all other cells. That maps directly onto Project B's Level 1 → Level 2 design.
2. **Disagreement as a confidence signal, with defined thresholds.** It flags clusters for expert review using two simple agreement measures.
3. **A documented trap:** high agreement can be misleading when the input is poor.

## What it does
Six LLMs (GPT-4o, Claude 3.5 Sonnet, Claude 3.5 Haiku, Gemini 1.5 Pro, Gemini 2.0 Flash, Qwen2.5-Max) each annotate every cluster from its top marker genes and tissue context. Clusters without agreement go to **deliberation**: each model sees the others' answers and reasoning and can revise. A separate "consensus checker" LLM (Claude 3.5 Sonnet by default) decides after each round whether agreement is reached. Defaults: up to 3 rounds, then up to 2 tie-breaker rounds; a persistent tie returns a composite label such as "celltype1/celltype2."

Scoring used the same full (1) / partial (0.5) / mismatch (0) Cell Ontology scheme as Hou & Ji 2024, with names standardized through the EBI Ontology Lookup Service.

## Key results
- **Accuracy:** 77.2% mean accuracy across 49 datasets, vs. 61.5% for GPTCelltype (a single-LLM approach). This is cell-weighted; per cluster it was 74.8%. 91.1% of 1,224 cluster labels were fully or partly correct (58.4% full, 32.7% partial).
- **On the hierarchy-aware metric,** hierarchical F1 was 0.88 vs. 0.75 for GPTCelltype.
- **More models helped most on hard clusters.** On Tabula Sapiens, accuracy rose from 59.3% with one LLM to 75.8% with six. For clusters where the best single LLM was below 60% accurate, six models improved accuracy by 38%.
- **Deliberation reduced hallucinations** across rounds. Hallucination was defined as a label contradicted by the markers (e.g., T cell without CD3D), inconsistent with the Cell Ontology (e.g., both B and T cell), or implausible for the tissue.
- **Robust to misleading markers:** when 30% of marker genes were replaced with another cell type's markers, accuracy fell about 30%, vs. about 50% for GPTCelltype.
- **Generalized beyond the models' training data:** 76.6% accuracy on an immune atlas published after the models' training cutoffs.
- **Beat reference-based scANVI** on 5 of 7 popV benchmark datasets (mean 71.6% vs. 56.7%), especially where the reference lacked cell types present in the query.
- **Hierarchical strategy:** on the Human Lung Cell Atlas, adding parent context and sibling-cluster markers improved fine-level accuracy by 4.8 percentage points. It reached 89% accuracy at Level 3 with 98% consistency with the parent level.

## Confidence signals the agent can reuse
- **Consensus proportion:** the share of models agreeing with the majority label. **Flagged for review at or below 66.7%** (4 of 6).
- **Shannon entropy** of the models' answers: 0 means full agreement. **Flagged above 1.**
- Higher consensus was strongly associated with fewer hallucinated labels.
- **Caveat: high consensus isn't always high confidence.** With heavily degraded marker lists (40–50% noise), all models fell back to broad, safe labels (e.g., "T cell" instead of "CD8+ effector memory T cell"), producing **spuriously high agreement**. The authors recommend reading consensus together with data-quality checks. An unexpectedly broad label with high agreement may signal poor input, not confidence.
- These scores aren't formally calibrated probabilities (stated by the authors).

## How many marker genes?
The authors found the number needed depends on how fine the distinction is (Supplementary Fig. 6):
- **simple lineage distinctions: plateau at 8–15 markers**
- **intermediate subtypes: 15–25**
- **complex developmental states: 20–35**, with diminishing returns beyond 30.

Their default is 30. This reconciles the earlier conflict: Hou & Ji's best was 10 (single prompt, mostly broad types), CASSIA's was ~50 (multi-step reasoning, many fine types).

## Lessons for the agent's decisions (Project B interpretation, not stated in the paper)
- **At Level 2, give the agent the Level 1 label and sibling-cluster markers.** For example, when splitting T cells, include markers comparing each T-cell cluster with the other T-cell clusters, plus "parent: T cell." This is the paper's strongest design lesson for a two-level taxonomy.
- **Use fewer markers for Level 1 (~10–15) and more for Level 2 (~15–25).**
- **Treat disagreement as a reason to flag,** using thresholds like consensus ≤ 66.7% or entropy > 1 as starting points. In a single-model agent, the same idea applies to repeated runs (see CASSIA's consensus score).
- **Don't treat agreement on a broad label as proof of quality.** If the agent keeps retreating to a Level 1 label on a cluster, check the input data (QC, doublets, marker quality) before accepting it.
- **Expect the agent can't name genuinely novel cell types;** it can only flag clusters that fit nothing known.

## Limits and caveats
- **No tumor-specific evaluation in the main text,** and no malignant-cell analysis.
- **Figures are missing from this version;** some results can't be verified until the final article.
- **Shared training data means shared blind spots.** Models from different providers can still agree confidently on a wrong label ("groupthink"); diversity reduces but doesn't remove this risk.
- **Agreement isn't accuracy:** labels are compared with original authors' annotations. In continuous datasets (bone marrow, thymus development), the framework preferred broader labels that score lower against fine-grained references but may be more defensible.
- **Cost:** API costs of roughly $0.50–$1.50 per 1,000 cells for six models; the authors suggest a 3- or 4-model setup for routine use.
- **Model versions are already dated** (2024–early 2025 models). The design lessons should outlast the numbers.
- **The authors excluded CellTypist and scGPT** as baselines because their training data overlaps the benchmarks, a useful reminder when comparing tools.

## Relevance to Project B
A **core design reference alongside CASSIA.** CASSIA shows how to check one model's answer with separate roles; this paper shows how to use disagreement as a review signal, and gives the most directly applicable method for annotating level by level, with parent context and sibling-cluster markers. Its warning that high agreement on a broad label can hide poor data is an important addition to the agent's abstention rules.

---
**Review status:** Unreviewed · Drafted by Claude from the unedited Article in Press PDF (figures not available; pp. 1–24 read) · Value: high (hierarchical design + consensus thresholds) · Student check: pending (David Graham)
