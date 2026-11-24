"""CIDS conformance test suite tooling.

Command-line entry point: ``python -m cidsconformance --help``.
"""

import rdflib

# By default rdflib rewrites the lexical form of typed literals when it parses
# them (e.g. "2023-01-01T05:00:00Z" becomes "2023-01-01T05:00:00+00:00" and
# "03" becomes "3"). A conformance suite has to see exactly what a file says,
# so normalization is switched off for everything that uses this package.
rdflib.NORMALIZE_LITERALS = False

__version__ = "0.1.0"
