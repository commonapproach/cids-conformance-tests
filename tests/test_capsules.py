"""Every capsule gives exactly its expected SHACL and data-quality results,
and the generated files are up to date."""

import pytest

from cidsconformance.build import build
from cidsconformance.suite import capsule_dirs, check_capsule

DIRS = capsule_dirs()


def test_there_are_capsules_in_every_category():
    cats = {d.parent.name for d in DIRS}
    assert cats == {"valid", "invalid", "data-quality"}


@pytest.mark.parametrize("capsule_dir", DIRS, ids=[d.name for d in DIRS])
def test_capsule_matches_expected(capsule_dir):
    problems = [p for outcome in check_capsule(capsule_dir) for p in outcome.problems]
    assert not problems, "\n".join(problems)


def test_generated_files_are_up_to_date():
    stale = build(check=True)
    assert not stale, "Run `python -m cidsconformance build`:\n" + "\n".join(stale)
