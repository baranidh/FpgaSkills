# Relative-path depth cheatsheet

The rule: **count directory levels from the file doing the linking, up to a common point, then back down to the target.** The mistake happens when a file inside a skill's `references/` subfolder is treated as if it were as shallow as that skill's own `SKILL.md` — it isn't; it's one level deeper.

## The two depths, side by side

```
skills/
├── skill-a/
│   ├── SKILL.md                    <- depth: skills/skill-a/
│   └── references/
│       └── deep-topic.md           <- depth: skills/skill-a/references/  (ONE LEVEL DEEPER)
└── skill-b/
    └── SKILL.md
```

From `skills/skill-a/SKILL.md`, reaching `skills/skill-b/`:
```
../skill-b/
```
(up one level from `skill-a/` to `skills/`, then into `skill-b/`)

From `skills/skill-a/references/deep-topic.md`, reaching the same `skills/skill-b/`:
```
../../skill-b/
```
(up one level from `references/` to `skill-a/`, up one more to `skills/`, then into `skill-b/`)

**The same file written with only *../skill-b/* from inside `references/` resolves to `skills/skill-a/skill-b/` — a path that doesn't exist.** This is exactly the bug that was made (and had to be fixed) twice while building the `timing-closure-ultrascale` and `bitstream-and-bringup` skills in this repo: a `references/` file linked to a sibling skill with the same `../` count its own `SKILL.md` would have used, one level too shallow.

## Reaching a repo-root shared file

```
skills/skill-a/SKILL.md            -> ../../references/shared-fact.md      (2 levels up: skill-a/ -> skills/ -> repo root)
skills/skill-a/references/x.md     -> ../../../references/shared-fact.md   (3 levels up: references/ -> skill-a/ -> skills/ -> repo root)
```

## The general rule, stated once

1. Count how many directories deep the **referencing file** is, relative to the repo root.
2. Count how many directories deep the **target file** is, relative to the repo root.
3. The number of `../` needed equals (referencing file's depth) minus 1 for its own directory, then descend into the target's path from there.

In practice: don't count mentally under time pressure — write the link, then run `references/verify-skill-library.py` (in the parent skill-library-authoring skill) immediately, since a broken relative path is caught instantly by resolving it against the filesystem rather than by re-deriving the arithmetic by eye a second time.

## Checklist before trusting a cross-reference by eye

- Is the referencing file itself at the skill's top level (`skills/X/SKILL.md`) or nested one level into `references/` (`skills/X/references/*.md`)? The nested case needs one extra `../` for every cross-skill or repo-root target.
- Does the same file link to both a sibling skill AND a repo-root shared file? Each needs its own correctly-counted depth — don't assume they're the same because they're written in the same file.
- After writing or editing any cross-reference, re-run the verification script rather than trusting the visual count — this exact class of error does not produce a Python exception or an obviously wrong rendering; it just silently points at a directory that doesn't exist.
