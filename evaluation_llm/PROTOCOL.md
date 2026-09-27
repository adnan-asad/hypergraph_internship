# Blind LLM evaluation protocol — assessor clarification

Defined after frozen clustering/retrieval outputs existed and before judge ratings. This is a post-hoc evaluation, not a preregistered experiment. Weights, partitions, generated text and rankings remain unchanged. The assessor explicitly accepts a documented blind LLM judge with manual checks; a domain expert is not mandatory.

Separate fresh-context LLM judges receive only their anonymized packets and rubric, not this project's history, configuration names, embeddings, scores or identity key. The judge is independent of the embedding representation but is an AI assistant, not a domain expert. Model family may share general training biases; independence is methodological, not statistical proof of unrelated training data. Each judge makes one pass. No rating is revised to improve a result. Store all decisions and evidence rationales before decoding the key.

## Coherence

Judge 48 packets: all twelve 2024 top-level groups in each gamma control, plus a matched type-composition-and-size-preserving random-assignment null per group. Each packet contains fifteen uniformly sampled members, without replacement. Use ordinal 1=incoherent/mere names or broad domain only, 2=mixed subthemes, 3=mostly recognizable scientific theme with exceptions, 4=clear specific scientific concept. Generic 'materials science' is insufficient. Judge the sample, not unseen members. Report actual/null means, per-group differences, and descriptive bootstrap intervals over matched group pairs. One null realization and one judge limit significance/generalizability. No claim of expert agreement.

## Label faithfulness

Four uniformly sampled groups per level (0/1) per snapshot: 32 items. Evaluate the unchanged label and gloss against member text, keyword witnesses and cutoff-available relation context. Categories: accurate_informative; supported_but_vague; unsupported_or_wrong; insufficient_evidence. Overclaim numerator is unsupported_or_wrong; denominator is determinate judgments (report all-category counts and uncertainty bounds including insufficient cases). Quoted examples must not be mistaken for universal statements about all members. Rate both label and gloss together, explain scope, and separately flag a too-broad/misleading theme. Copy integrity is distinct from this judgment. Underlying text is unversioned and full papers are unavailable: evaluate support in the supplied extraction, not external scientific truth.

## Downstream evidence

All fourteen Type-A and four Type-B questions, both frozen result lists, independently anonymized. For Type A report direct method-node recovery (aliases only when unambiguous from returned text), method mentions in claims separately, and supported expected-claim coverage. For Type B rate each required rubric claim full/partial/absent/contradicted, with 1/0.5/0/0 descriptive coverage. Report required-source coverage using only attached provenance titles and explicit returned citations. Preserve rubric caveats about asserted versus empirical evidence. Unknown provenance is not a citation hit. No web knowledge or ground-truth facts may be inserted into the retrieved evidence. This evaluates evidence available to an answerer, not generated-answer accuracy. The original retriever uses one coarse filtering step, not full multilevel routing.

## Spot checks and uncertainty

The developer's previous manual review is retained as developmental coherence error analysis. Fresh human spot checks of this new evaluation must be explicitly recorded; an assistant's audit must not be called a human check. Select six cases deterministically after ratings; include adverse/null cases and keep disagreements. Pending human checks remain pending. Bootstrap intervals describe the sampled groups/items conditional on one judge, not model stochasticity or independent corpora. Report denominators and missing values everywhere.
