# AI Programmer Behavior Analyzer

Analyzes a programmer's source code over multiple submissions to surface
their **habits, patterns, strengths, weaknesses, and skill progression** --
not just whether code is "correct."

Runs entirely locally. No paid AI APIs required for the core system.

## Status: Phase 1 complete (AST feature extraction)

Per the development strategy, the project is being built in strict phases,
and we do not move to the next phase until the current one is verified.

- [x] **Phase 1** -- `backend/analyzer/ast_analyzer.py`: `CodeAnalyzer.analyze(code)`
      extracts structural features via Python's `ast` module. Verified against
      11 sample programs (10 valid + 1 intentionally broken) and 21 pytest
      regression tests.
- [ ] Phase 2 -- Radon complexity metrics (cyclomatic complexity, maintainability index)
- [ ] Phase 3 -- SQLite database (submissions + extracted features)
- [ ] Phase 4 -- Rule-based behavior analysis (no ML yet, to sanity-check features)
- [ ] Phase 5 -- ML behavior classification (Random Forest / XGBoost / K-Means)
- [ ] Phase 6 -- Programmer profiles
- [ ] Phase 7 -- Progress tracking over time
- [ ] Phase 8 -- Dashboard
- [ ] Phase 9 -- Optional local-LLM natural-language explanations (Ollama)

## What Phase 1 actually does

`CodeAnalyzer.analyze(source_code: str) -> dict` returns a JSON-serializable
feature dictionary:

- **General**: LOC, blank lines, comment lines (via `tokenize`, so comments
  inside strings aren't miscounted), function/class/import counts, variable
  and constant counts (heuristic: ALL_CAPS names = constants).
- **Control flow**: if-statements, for/while loops, nested-loop count,
  max loop nesting depth, try/except blocks, ternaries, comprehensions.
- **Functions**: avg/max function length, avg arg count, return-statement
  count, direct-recursion detection (documented limitation: mutual
  recursion across two functions is not detected in this version).
- **Data structures**: list/tuple/set/dict/string literal counts, plus
  heuristic stack/queue/heap detection (stack/queue require actual
  `.append()`/`.pop()` usage or a `deque`/`heapq` import -- not just the
  presence of a list literal).
- **Patterns** (all heuristic, all confidence-scored 0.0-1.0, never
  claimed as certain): sorting, binary search, two pointers, sliding
  window, recursion, divide & conquer, brute force, hash-map lookup,
  dynamic programming, greedy, graph traversal, linear search.

Every heuristic's rationale is documented inline in the code as a comment,
including its known false-positive risks (e.g. variable-name-based
heuristics like "two pointers" will fire on any `left`/`right` variables,
even in unrelated code -- this is intentional and disclosed via the
confidence score, not hidden).

## Running it

```bash
# Run the human-readable feature dump against 10 sample programs
python3 tests/run_ast_analyzer_tests.py

# Run the hard-assertion regression suite
python3 -m pytest tests/test_ast_analyzer.py -v
```

## Project structure

```text
ai-programmer-analyzer/
├── backend/
│   ├── analyzer/
│   │   └── ast_analyzer.py      # Phase 1 (done)
│   ├── ml/                      # Phase 5 (empty)
│   ├── database/                # Phase 3 (empty)
│   └── api/                     # future FastAPI routes (empty)
├── frontend/                    # Phase 8 (empty)
├── data/                        # training data will live here
├── models/                      # trained model artifacts will live here
├── tests/
│   ├── sample_programs/         # 11 test programs (10 valid, 1 broken)
│   ├── run_ast_analyzer_tests.py
│   └── test_ast_analyzer.py
└── requirements.txt
```

## Engineering rules this project follows

- No paid APIs for the core system.
- No hardcoded fake results or randomly-generated scores.
- Never claim exact Big-O complexity without a confidence qualifier.
- Never claim any score is a scientifically valid intelligence measurement.
- Analysis logic, database logic, and ML logic stay in separate modules.
- Invalid/unparseable input is handled gracefully, never an uncaught crash.
