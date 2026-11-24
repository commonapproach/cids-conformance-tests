"""Builds the test capsules in ``capsules/``.

The capsules are generated so that every broken capsule is a small, known
change to a clean base capsule. Edit the definitions in ``catalog.py`` and
run ``python -m cidsconformance build`` to regenerate. Don't hand-edit the
files in ``capsules/``: CI checks they match the generator.
"""
