# Ingestion agent instructions

These are the instructions for the agent that reads a paper and writes its record
for the Annotation Explorer. For now a person runs Claude through these steps by
hand. A future automated agent should follow the same contract: it reads
`sources/<id>/paper.md` and writes `ingested/<id>.json`, which must validate
against `schema/ingested_paper.schema.json`.

## Steps

1. **Pick papers.** `python pipeline/build_index.py --pending 10` lists the
   highest-ranked papers that haven't been ingested. The ranking follows
   [`../SKILLS.md`](../SKILLS.md).
2. **Fetch sources.** `python pipeline/fetch_sources.py <id>` (or `--next 5`)
   saves the best free text to `sources/<id>/paper.md` and records where it came
   from in `source.json`.
3. **Read and write.** Read `paper.md` and write `ingested/<id>.json` (rules
   below). The file name and `id` must match.
4. **Build.** `python pipeline/build_index.py` validates every record, re-ranks the
   papers and regenerates `web/data/papers.json`. Invalid records are reported and
   skipped.

## Rules for the record

**Ground everything in the sources you read.**
- Every statement must come from `paper.md`. Don't fill gaps from memory.
- List what you actually read in `ingestion.sources`, and say in
  `ingestion.notes` what you couldn't read (figures, supplements, full text).
- If only the abstract was available, say so in `notes` and use `"unknown"` for
  workflow steps you can't judge.

**Links.**
- Include only links that appear in the source text, or that you've checked
  resolve (e.g. a code repository named in the paper).
- Accession numbers given in the text (GEO, ArrayExpress) can be turned into
  their standard URLs.

**Enhanced abstract.** Write it in your own words; don't copy the abstract.
- `tldr`: one sentence on what the paper does and its headline result.
- `sections`: 3–5 short headed sections, e.g. Problem, Method, Evaluation,
  Results.
- `key_findings` and `limitations`: short bullets. Include limitations the
  authors state.
- `why_it_matters`: relevance to this project, naming the `SKILLS.md` rule and
  tier the paper was given.

**Workflow mapping.** Fill in all nine steps:

| `involvement` | Use when |
|---|---|
| `core` | The paper's main contribution is at this step |
| `used` | The paper performs this step with existing methods |
| `mentioned` | Discussed, assumed or shown, but not performed |
| `none` | Not addressed |
| `unknown` | Can't tell from the sources read |

For each step, give a one- or two-sentence `summary`, plus `methods` and
`tools` when the paper names them.

**Algorithms and tools.** Use `role`: `proposed` (the paper's own), `used`,
or `compared` (a baseline). Always list baselines with role `compared`; that's
how the app tells real use apart from benchmarking.

**Use the vocabulary's names.** Write tool and method names as they appear in
[`vocab/vocabulary.json`](vocab/vocabulary.json) (e.g. `Seurat`, `Scanpy`,
`SNN graph clustering`, `Log normalization`), so usage can be counted across
papers. A version can follow the name (`Seurat v5`, `Monocle 3`) and is kept
separately. If something genuinely isn't in the vocabulary, use the paper's name
for it. The build lists unmatched names in `cache/unlisted_names.json`; add them
to the vocabulary (as new entries or aliases) when they'll recur.

**Marker definitions (`cell_types`).** List only cell types the paper defines
with explicit marker genes. Keep the paper's gene symbols, including mouse
capitalization, and put species and tissue in `context`. These rows are the seed
material for annotation rules, so leave the list empty rather than guess.

## Output

One JSON file per paper in `ingested/`. Commit `ingested/*.json` and
`web/data/papers.json`. `sources/` is git-ignored because full texts may not be
redistributable.
