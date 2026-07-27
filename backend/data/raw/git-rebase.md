# Git Rebase

## Overview

Git rebase is a command that rewrites commit history by applying commits from one branch onto the tip of another. Unlike merging, which creates a merge commit that ties two branch histories together, rebasing produces a linear history by replaying each commit on top of the target branch. Rebasing is a powerful tool for maintaining a clean, readable project history but requires careful use, especially on shared branches.

## Details

### Rebasing vs Merging

Merging preserves the complete history of both branches, including the divergence point and the merge commit. This is the safest approach for shared branches because it does not rewrite history. Rebasing, by contrast, rewrites the commits being moved — each replayed commit gets a new SHA-1 hash, new timestamp, and potentially new content if conflicts are resolved. The result is a linear history that is easier to follow and bisect, but the operation is destructive and should never be performed on commits that have been pushed to a shared branch.

### Interactive Rebase

The `--interactive` (or `-i`) flag opens an editor showing the list of commits in the range being rebased, along with commands for each: `pick`, `reword`, `edit`, `squash`, `fixup`, `exec`, `break`, `drop`, and `label`. This allows you to reorder, combine, split, or remove commits before the rebase proceeds. Interactive rebase is typically used with `HEAD~N` to operate on the last N commits.

### Squashing Commits

Squashing combines multiple commits into a single commit. In interactive rebase, changing `pick` to `squash` for a commit merges it into the previous commit and prompts for a new combined message. The `fixup` command is similar but discards the squashed commit's message, keeping only the previous commit's message. Squashing is useful for cleaning up WIP commits, typo fixes, and experimental changes before sharing work.

## Examples

```bash
# Rebase feature branch onto main
git checkout feature
git rebase main

# Interactive rebase for the last 3 commits
git rebase -i HEAD~3

# In the editor that appears, you might see:
# pick a1b2c3d Add login form
# pick e4f5g6h Fix login validation
# pick i7j8k9l Add tests for login

# To squash the fix into the feature commit, change to:
# pick a1b2c3d Add login form
# fixup e4f5g6h Fix login validation
# pick i7j8k9l Add tests for login

# Abort a rebase if things go wrong
git rebase --abort

# Continue rebase after resolving conflicts
git add <resolved-files>
git rebase --continue

# Skip a problematic commit during rebase
git rebase --skip

# Rebase onto a different branch (e.g., rebase past 5 commits onto main)
git rebase --onto main HEAD~5 HEAD

# Pull with rebase instead of merge (configures pull behavior)
git pull --rebase
# Or set as default:
git config --global pull.rebase true
```

A common workflow is `git pull --rebase` on a feature branch to incorporate upstream changes without creating a merge commit, followed by an interactive rebase to clean up commits before opening a pull request. Always coordinate with teammates before rebasing shared branches.
