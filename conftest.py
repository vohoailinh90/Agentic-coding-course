"""pytest: put the repository root on sys.path so tests can `import src...`.

`python -m unittest` (which scripts/mutation_check.py uses) already runs from
the root, so this file only matters for pytest.
"""
