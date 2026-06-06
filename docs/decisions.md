# Decisions Log

## 2026-06-06 — Initial chapter framing

Decision: Set up this repository around the working claim that the Kerkrade low-cost IoT stream carries a decomposable antecedent-hydrological-state signal once barometric effects are explicitly characterized and separated.

Alternatives considered: Treat the chapter as a direct flood-prediction chapter; treat it as a purely barometric mine-gas dynamics chapter; delay repository setup until after data ingestion.

Reasoning: The June 2026 pre-work plan makes the first month a foundation and decomposition sprint. The chapter should survive either outcome of the first kill check: if pressure explains only part of CO2 variance, the hydrological-signal framing proceeds; if pressure explains nearly all variance, the chapter can redirect toward a barometric-decomposition methods contribution without losing the work already done.

Source: `chapter-prework/June 2026 - How-To.docx`; `chapter-prework/Lit-scaffold - chapter draft.docx`.

## 2026-06-06 — Repository structure

Decision: Use numbered runnable scripts in `scripts/` and reusable package code in `src/`, with no notebooks as core analytical artifacts.

Alternatives considered: Notebook-first exploratory workflow.

Reasoning: The chapter needs reproducible, defensible analysis steps. Numbered scripts make the run order explicit; `src/` keeps readers, feature builders, models, and evaluation code stable across scripts.

Source: `chapter-prework/June 2026 - How-To.docx`; `chapter-prework/skill-dissertation-chapter-scaffold/reference/repo_layout.md`.

