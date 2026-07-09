#!/usr/bin/env python3
"""
Batch structural verification for a Claude Code skill library.

Consolidates checks that are easy to get subtly wrong by hand (especially
the relative-path depth mistake in path-depth-cheatsheet.md) into one
reusable script, instead of rewriting the same ad hoc checks by hand
every time a library changes.

Checks performed:
  1. Every skills/*/SKILL.md has well-formed YAML frontmatter with a
     `name` field matching its directory name, and a `description`.
  2. No duplicate skill `name` across the library.
  3. Every top-level *.json file (e.g. .claude-plugin manifests) is
     valid JSON.
  4. Every backtick-quoted relative path reference (in the style of
     ../foo/bar.md) in any .md/.py/.tcl file resolves to a real file on
     disk.

Does NOT check: content accuracy, description trigger-phrase quality
(that's a judgment call, not a mechanical one - see skill-creator's eval
loop for that), or the no-duplication rule (grep manually per
no-duplication-checklist.md, or extend CANONICAL_FACTS below).

Usage:
    python3 verify-skill-library.py <repo-root>

Requires: PyYAML (pip install pyyaml)
"""

import json
import os
import re
import sys
import glob

try:
    import yaml
except ImportError:
    print("This script requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# Facts that must be fully derived in exactly one file, with other
# appearances treated as references only. Extend this list per-project -
# see no-duplication-checklist.md for how to decide what belongs here.
CANONICAL_FACTS = {
    # "example-canonical-number": "references/example-canonical-file.md",
}


def check_frontmatter(repo_root: str) -> list:
    errors = []
    names = {}
    skill_files = sorted(glob.glob(os.path.join(repo_root, "skills", "*", "SKILL.md")))
    if not skill_files:
        errors.append(f"no skills/*/SKILL.md files found under {repo_root} - wrong repo root?")
        return errors

    for path in skill_files:
        content = open(path).read()
        m = re.match(r"^---\n(.*?)\n---\n", content, re.S)
        if not m:
            errors.append(f"{path}: no '---' delimited frontmatter block")
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            errors.append(f"{path}: frontmatter is not valid YAML: {e}")
            continue
        if not fm or "name" not in fm or "description" not in fm:
            errors.append(f"{path}: frontmatter missing 'name' or 'description'")
            continue

        dirname = os.path.basename(os.path.dirname(path))
        if fm["name"] != dirname:
            errors.append(f"{path}: name '{fm['name']}' != directory name '{dirname}'")
        if fm["name"] in names:
            errors.append(f"{path}: duplicate skill name '{fm['name']}' "
                           f"(also used by {names[fm['name']]})")
        names[fm["name"]] = path

    print(f"[frontmatter] checked {len(skill_files)} SKILL.md files, "
          f"{len(names)} distinct skill names")
    return errors


def check_json_manifests(repo_root: str) -> list:
    errors = []
    manifest_paths = glob.glob(os.path.join(repo_root, ".claude-plugin", "*.json"))
    for path in manifest_paths:
        try:
            json.load(open(path))
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON: {e}")
    print(f"[json] checked {len(manifest_paths)} manifest files")
    return errors


def check_cross_references(repo_root: str) -> list:
    errors = []
    checked = 0
    seen = set()
    patterns = ["**/*.md", "**/*.py", "**/*.tcl", "**/*.sv"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(repo_root, pattern), recursive=True))

    for path in files:
        content = open(path, errors="replace").read()
        base_dir = os.path.dirname(path)
        for m in re.finditer(r"`(\.\.?/[^`]+?)`", content):
            target = m.group(1)
            path_part = target.split("#")[0].rstrip()
            resolved = os.path.normpath(os.path.join(base_dir, path_part))
            checked += 1
            key = (path, target)
            if key in seen:
                continue
            seen.add(key)
            if not os.path.exists(resolved):
                rel_path = os.path.relpath(path, repo_root)
                errors.append(f"{rel_path}: reference '{target}' resolves to "
                               f"'{resolved}' which does not exist")

    print(f"[cross-refs] checked {checked} backtick-quoted relative path references")
    return errors


def check_canonical_facts(repo_root: str) -> list:
    """Every configured canonical fact should appear as a full derivation
    only in its designated file; other appearances should be references,
    not restatements. This is a coarse heuristic (a term appearing
    elsewhere isn't automatically wrong - it might legitimately be a
    reference/citation) so treat findings here as things to review, not
    automatic failures."""
    warnings = []
    if not CANONICAL_FACTS:
        return warnings
    for term, canonical_file in CANONICAL_FACTS.items():
        canonical_path = os.path.join(repo_root, canonical_file)
        if not os.path.exists(canonical_path):
            warnings.append(f"canonical file for '{term}' does not exist: {canonical_file}")
            continue
        hits = []
        for path in glob.glob(os.path.join(repo_root, "**/*.md"), recursive=True):
            if os.path.abspath(path) == os.path.abspath(canonical_path):
                continue
            if term in open(path, errors="replace").read():
                hits.append(os.path.relpath(path, repo_root))
        if hits:
            warnings.append(f"'{term}' (canonical: {canonical_file}) also appears in: "
                             f"{', '.join(hits)} - confirm these are references, not restated derivations")
    return warnings


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    repo_root = sys.argv[1]

    all_errors = []
    all_errors += check_frontmatter(repo_root)
    all_errors += check_json_manifests(repo_root)
    all_errors += check_cross_references(repo_root)
    warnings = check_canonical_facts(repo_root)

    print()
    if warnings:
        print("WARNINGS (review, not necessarily errors):")
        for w in warnings:
            print(" -", w)
        print()

    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s)")
        for e in all_errors:
            print(" -", e)
        sys.exit(1)
    else:
        print("PASSED: no structural errors found")
        sys.exit(0)


if __name__ == "__main__":
    main()
