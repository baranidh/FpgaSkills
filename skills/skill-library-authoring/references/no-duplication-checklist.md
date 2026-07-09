# No-duplication checklist

Any fact, number, or derivation used by more than one skill lives in exactly one canonical file. This checklist is the decision guide for *where* — and the discipline for catching drift once a library has grown past a handful of skills.

## Where does a given fact belong?

| Used by | Belongs in |
|---|---|
| Only one skill | That skill's own `references/` file, or inline in its `SKILL.md` if short |
| Two skills that are tightly coupled (e.g. a worked example and the skill it demonstrates) | Still consider a shared top-level file if the fact is load-bearing (a number others might need to change consistently) — two IS enough to justify it if the fact is a number/derivation rather than prose |
| Three or more skills | Top-level `references/<fact>.md`, unconditionally — this is the bright line used in this repo (the 322.265625/644.53125 MHz clock math lives in one file linked from five skills) |

## Signs a library already has a duplication problem

- The same number appears in two files with even slightly different formatting (e.g. `3.1 ns` in one place and `3.10303 ns` in another) — this is what drift looks like before it becomes a real inconsistency; the first divergence is often just rounding, but it means the two copies are no longer the same source of truth.
- A definition (a glossary term, a protocol field's meaning) is restated in prose in more than one `SKILL.md` instead of one file being linked from both.
- Two skills each contain their own copy of a code template that's conceptually "the same," with small accidental differences that make it unclear which one is current.

## How to check a library for this, mechanically

Grep for the specific numbers/terms that are supposed to be canonical-in-one-place and confirm they only appear as full derivations in that one file, with other appearances being short references back to it (e.g. "see `clock-family-reference.md`") rather than restated derivations:

```bash
grep -rl "<canonical-number-or-term>" . --include=*.md
```

Read every file returned — files other than the canonical one should only *reference* the fact, not re-derive or restate its value. `verify-skill-library.py`'s duplication check automates a version of this for a configurable list of canonical facts.

## Fixing an already-duplicated fact

1. Pick (or create) the one canonical file.
2. Move the full derivation/definition there if it doesn't already live there.
3. In every other location, replace the restated content with a short cross-reference link.
4. Re-run `verify-skill-library.py` to confirm the link resolves (see `path-depth-cheatsheet.md` for getting the relative path right) and that no other copy of the derivation remains.
