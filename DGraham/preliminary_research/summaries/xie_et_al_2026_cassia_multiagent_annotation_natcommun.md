# Xie 2026: CASSIA, a multi-agent LLM for interpretable cell annotation

**Reference:** Xie E, Cheng L, Shireman J, Cai Y, Liu J, Mohanty C, Dey M, Kendziorski C. (2026). *CASSIA: a multi-agent large language model for automated and interpretable cell annotation.* Nature Communications 17:389. DOI: 10.1038/s41467-025-67084-x (published online 7 Dec 2025; preprint on bioRxiv 2024.12.04.626476)
**Resource:** [Article](https://doi.org/10.1038/s41467-025-67084-x) · R package, Python package, and web interface: www.cassia.bio · www.cassiacell.com
**Open access:** yes (check the license on the article page before redistributing the PDF).
**Species / tissue:** Mostly human and mouse benchmarks (GTEx, Tabula Sapiens, Human Cell Landscape, Mouse Cell Atlas, Azimuth), 970 cell types in total. Also cancer datasets (2 primary tumors, 3 brain metastases), immune datasets (PBMC68k; ProjecTILs T cells), and non-model species (shark, cat, tiger, pangolin).
**Taxonomy level:** Not tied to a level. A **method lessons** paper on how to structure an LLM annotation agent and check its own work.

## Why it's in the knowledge base
CASSIA is a published version of the architecture Project B is building: separate LLM agents that draft a label, check it, score it, and report the reasoning, with low-confidence labels flagged for further work. It shows which of those steps measurably help. It also gives concrete thresholds for deciding when to trust a label.

## The workflow (Fig. 1)
User input is species, tissue, and a ranked marker list per cluster (e.g., from Seurat's FindAllMarkers). Five agents then run in order:

| Agent | What it does |
|---|---|
| Annotator | Step-by-step reasoning: functional markers → cell-type markers → cross-check against known databases → most likely general type → top 3 subtypes |
| Validator | Checks that the markers the Annotator cites are **actually in the input list** and fit the proposed type. Sends failures back to the Annotator, up to 3 times |
| Formatter | Structures the output, including possible mixed populations |
| Quality scorer | Scores each annotation 0–100 from the full conversation history |
| Reporter | Writes a report of the reasoning, validation, and score (example in Fig. 3) |

Optional agents: **Annotation Boost** (re-examines low-scoring labels using full marker statistics), **uncertainty quantification** (repeat runs and measure agreement), **subclustering**, and **RAG** (pulls markers from CellMarker 2.0 and tissue-specific Cell Ontology trees).

## Key results
- **Accuracy:** fully correct labels increased by 12–41% over the next-best method across benchmarks. Fully or partially correct labels increased by 9–20% (Fig. 2a–b). It used the same full/partial/incorrect scoring as Hou & Ji 2024.
- **Comparisons:** beat GPTCelltype (GPT-4 and GPT-4o), ScType, SingleR, CellTypist, and scCATCH (Fig. 2c). Example average accuracies: cancer datasets 0.79 vs. 0.54 for the next best; immune datasets 0.83 vs. 0.56.
- **Works with several LLMs:** on 100 cell types, average accuracy was 0.92 with Claude 3.5, 0.88 with GPT-4o, and 0.82 with Llama 3.2 90B, versus 0.59–0.67 for GPTCelltype (Fig. 2e).
- **Number of marker genes:** performance plateaued at around **50 markers per cluster** (tested 10–100), and CASSIA didn't degrade with 100 (Fig. 2d). This differs from Hou & Ji's single-prompt finding that 10 was best; the multi-step design appears to use longer lists better.
- **Cancer cells (Fig. 4a–b):** default CASSIA detected cancer cells 72.5% of the time on average, vs. 20% for GPTCelltype. Adding one sentence to the prompt, *"You should carefully distinguish between cancer cells and normal cells with reasoning,"* raised detection to 88–100%. Four reworded versions of that prompt gave similar results.
- **Immune cells:** 27% higher average accuracy than the next best on PBMC68k and ProjecTILs. Most methods handled broad types (T vs. B) well; CASSIA also separated naive, memory, and exhausted T-cell subsets (states, out of scope here).
- **Mixed populations (Fig. 6c):** in simulated 50:50 mixtures, CASSIA flagged mixed clusters in 9 of 10 cases with the scoring agent; GPTCelltype flagged 0–3.
- **Annotation Boost:** of 42 low-scoring labels, it fixed 24 of the 27 that were wrong and kept all 15 that were right.

## Confidence signals the agent can reuse
- **Quality score threshold of 75/100.** Labels scoring below 75 were mostly partly correct or wrong. Labels above 90 were strongly associated with correct calls; 75–90 is intermediate (Fig. 5a). On an independent set of 132 labels, 80% of those below 75 were wrong or partly correct, and 97% of correct labels scored above 75. The authors chose the threshold to penalize false alarms more than misses (Methods).
- **Consensus across repeated runs.** The same cluster is annotated 5 times, and a consensus similarity score measures agreement. **Wrong labels had much lower consensus (median ~60) than correct or partly correct ones (median ~90)** (Fig. 5b). Gains from majority voting levelled off after 5–10 runs.
- **Low scores often point to bad data, not just bad labels.** In one dataset, a low-consensus "mature enterocyte" cluster had >60% mitochondrial reads in most cells (Fig. 6a).

## Errors in expert ("gold standard") labels
Of 15 cases where CASSIA was confident (score >90) but disagreed with the reference label, three independent LLMs sided with CASSIA in 11 (Fig. 6b). Two examples relevant to myeloid annotation:
- cells labelled **"monocytes"** showed strong Schwann cell markers (CDH19, SCN7A, PLP1, S100B, MPZ) and little monocyte signal;
- cells labelled **"neutrophils"** showed macrophage markers (C1QA, CD163, MRC1, CD68) and lacked neutrophil markers.

Lesson: disagreement with a reference isn't always the agent's error, which matters when grading the agent against expert labels.

## Lessons for the agent's decisions (Project B interpretation, not stated in the paper)
- **Add a validator step that checks cited markers are in the input.** It's simple and directly targets hallucination.
- **Have a separate scorer, and route anything below a threshold to review.** CASSIA's 75/100 is a reasonable starting point to calibrate against Dr. Talkington's decisions.
- **Run each cluster more than once and treat disagreement across runs as a flag.** This is the strongest single signal of a wrong label in the paper.
- **Explicitly instruct the agent to reason about cancer vs. normal.** One sentence made a large difference; the instruction alone still doesn't replace copy-number evidence.
- **Expect better use of longer marker lists** when the agent reasons in steps (~50 markers) than in a single prompt (~10, per Hou & Ji). Worth testing both on the lab's data.
- **Record the reasoning, not just the label.** CASSIA's report format (markers used, validation result, score) is a good template for what Dr. Talkington reviews.
- **When the agent disagrees with an expert label, check the markers before assuming the agent is wrong.**

## Limits and caveats
- **Performance depends on input marker quality.** The authors recommend QC, doublet detection, and ambient-RNA correction before computing markers. On a developmental dataset with poorly separated clusters, average accuracy fell to 0.53.
- **Clustering is assumed to be done upstream.**
- **Agreement isn't accuracy.** Benchmarks compare against reference labels, which the paper itself shows can be wrong.
- **Cancer results rest on 5 datasets** (2 primary, 3 brain metastases) and a single gold-standard "cancer cell" label.
- **The quality score is itself an LLM judgment.** Its threshold was tuned on these benchmarks and may need recalibrating for other data or models.
- **Costs and runtime grow** with repeated runs and optional agents.
- **Some prompt content is unusual,** e.g., telling the model "You will be rewarded $10,000 if you do a good job." Its effect wasn't tested separately.
- **Models tested (GPT-4o, Claude 3.5, Llama 3.2)** are already superseded; the architecture lessons should outlast the exact numbers.

## Relevance to Project B
The **most directly applicable design reference** in the knowledge base. It shows that the elements Project B plans (separate draft and check agents, a quality score, abstention below a threshold, and a readable reasoning report) measurably improve LLM annotation over a single prompt. Pair it with Hou & Ji 2024 (single-prompt baseline and scoring scheme) and scATOMIC 2023 (hierarchy and abstention to the parent label).

---
**Review status:** Unreviewed · Drafted by Claude from the published PDF, pp. 1–13 (uploaded by user) · Value: high (agent design + confidence thresholds) · Student check: pending (David Graham)
