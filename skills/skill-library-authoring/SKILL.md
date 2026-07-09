---
name: skill-library-authoring
description: "Use when building a LIBRARY of multiple related Claude Code skills together (not a single skill) — organizing them into a coherent, installable plugin, avoiding duplicated content across skills, getting cross-skill relative paths right, and batch-verifying the whole set. Trigger phrases: 'build a skill library', 'author multiple Claude Code skills', 'organize a plugin of skills', 'avoid duplicating content across skills', 'cross-skill references', 'verify skill library', 'SKILL.md frontmatter conventions for a library'. This is domain-agnostic — not specific to FPGAs — and is a companion to, not a replacement for, the single-skill-authoring skill-creator skill."
---

# Authoring a library of Claude Code skills

**Meta-skill, not FPGA content.** This documents the process used to build the other 13 skills in this repo, so it generalizes to any domain. It's a companion to `skill-creator` (if installed — commonly found at a path like `/mnt/skills/examples/skill-creator/`), not a replacement: skill-creator covers writing and grading *one* skill (frontmatter conventions, description-optimization eval loops, packaging); this skill covers the problems that only show up once you have *several* related skills that need to work together as a set.

## When to use this vs. skill-creator

- Writing or improving a single `SKILL.md`, running trigger-phrase evals, packaging one skill → **skill-creator**.
- Deciding how many skills a project needs, organizing them into one plugin, keeping shared facts consistent across them, getting cross-skill links right, verifying the whole set at once → **this skill**.
- Building a multi-skill library in practice uses both: skill-creator per individual skill, this skill for the library-level structure holding them together.

## Library-level layout

```
<repo>/
├── README.md                    # catalog table (skill -> one-line purpose) + install instructions
├── .claude-plugin/
│   ├── plugin.json              # plugin manifest: name, description, keywords
│   └── marketplace.json         # self-installable entry: source: "./"
├── references/                  # facts used by THREE OR MORE skills - see no-duplication-checklist.md
│   └── <shared-fact>.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md             # frontmatter + concise body, progressive disclosure into references/
        └── references/          # this skill's own deep material only
```

This is the exact structure this repo (`FpgaSkills`) uses: `references/clock-family-reference.md` is a fact five different skills need (the 322.265625/644.53125 MHz clock-period math) and none of them re-derive it — they all link to the one canonical copy.

## The no-duplication rule

Any number, derivation, or definition that more than one skill needs lives in exactly **one** canonical file; every consumer links to it instead of restating it. See `references/no-duplication-checklist.md` for the decision guide on where a given fact belongs (shared top-level `references/` vs. a skill's own `references/` vs. inline in a `SKILL.md` body). Violating this is how a library quietly drifts: two skills each state a number "for convenience," someone updates one copy later, and the two skills silently disagree.

## The relative-path depth mistake (made twice building this repo — don't repeat it)

A `SKILL.md` at `skills/X/SKILL.md` reaches a sibling skill with *../Y/*. A reference file at `skills/X/references/foo.md` is **one directory level deeper**, so the same sibling needs *../../Y/* — one more `../` than it would take from `SKILL.md` itself. This exact off-by-one was made and had to be fixed twice while building this repo's `timing-closure-ultrascale` and `bitstream-and-bringup` skills. See `references/path-depth-cheatsheet.md` for the general counting rule (count directory levels from the referencing file up to the repo root, then back down to the target) with worked diagrams reproducing the actual bug.

(Note on notation: this file uses italics like *../Y/* for illustrative, non-resolvable placeholder paths, and backticks like `references/path-depth-cheatsheet.md` for real, resolvable cross-references — precisely so `verify-skill-library.py` doesn't flag the illustrative examples as broken links.)

## Writing descriptions that disambiguate

Trigger phrases in a `description` need to be concrete (protocol names, tool commands, error-message-like phrases) rather than abstract summaries, especially when two skills in the same library cover adjacent ground. Worked examples from this repo: `uvm-testbench-generation` (authoring driver/monitor/scoreboard components) vs. `simulation-workflow` (running/debugging what's already built) stay disambiguated because their trigger phrases target different verbs ("write a testbench" vs. "why is my testbench hanging"); `timing-closure-ultrascale` (timing reports) vs. `synthesis-implementation-vivado` (utilization/resource reports) stay disambiguated by naming the specific report commands each owns (`report_timing_summary` vs. `report_utilization`) rather than both claiming "reports" generically.

## Deciding skill vs. reference-file vs. shared-top-level-file

- **New skill**: the topic has its own distinct trigger surface — phrases a user would say that don't overlap with an existing skill's. (`market-order-entry-conveyor` earned its own skill because "order entry gateway" domain terms are a distinct trigger surface, not because it was long.)
- **A skill's own `references/` file**: material only that one skill needs, too long to keep the `SKILL.md` body scannable (code templates, full command references, worked examples).
- **Shared top-level `references/` file**: a fact three or more skills would otherwise each restate (see the no-duplication rule above).

## Batch verification

Run `references/verify-skill-library.py <repo-root>` after any change to the library — it's a single reusable script (not an inline snippet to rewrite each time) that checks every `SKILL.md` frontmatter parses as YAML with `name` matching its directory and no duplicate names across the library, every `.json` manifest is valid, and every backtick-quoted relative path resolves to a real file. This consolidates checks that are easy to get subtly wrong by hand — the path-depth mistake above is exactly the kind of thing this script catches immediately that a visual review can miss.

## See also

`skill-creator` (single-skill authoring and eval loops, if installed), `references/path-depth-cheatsheet.md`, `references/no-duplication-checklist.md`, `references/verify-skill-library.py`.
