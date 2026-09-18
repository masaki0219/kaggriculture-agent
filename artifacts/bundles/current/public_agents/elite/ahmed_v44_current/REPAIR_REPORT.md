# Ahmed V44 Repair Report

- Generated: `2026-09-18T14:40:51+09:00`
- Notebook: `artifacts/bundles/current/public_agents/elite/ahmed_v44_current/source/kaggriculture-v44-winning-the-same-turn-sale-race.ipynb`
- Build dir: removed after the validated runtime entrypoint was frozen
- Candidates: **2**

## Cell replay

| Cell | Status | Detail | First line |
|---:|---|---|---|
| 2 | ok | WORKDIR rewrites=1 | from pathlib import Path |
| 4 | ok | WORKDIR rewrites=0 | import hashlib |
| 6 | ok | WORKDIR rewrites=0 | import ast, hashlib, json |
| 8 | exec-error | ModuleNotFoundError: No module named 'IPython' | import gzip, io, tarfile |
| 10 | risk-skip | external-process call: run |  |

## Candidate validation

| Rank | Origin | Relative path | Bytes | SHA256 | Import | Detail |
|---:|---|---|---:|---|---|---|
| 1 | generated/build (intermediate removed) | final entrypoint retained below | 323883 | `fe370bd8a9d0f3770e61cff4d9e60e19198e058a0fa1fb0adeb873a9d89c6640` | OK | agent |
| 2 | raw-cell:4 (intermediate removed) | source preserved in the original notebook | 338999 | `279813df77a28210076989e602da58c22ebc4186023aa77018a8ce6db5c6cc76` | FAIL | NameError: name 'WORKDIR' is not defined |

## Result

**SUCCESS**

- Chosen origin: `generated/build`
- Final entrypoint: `notebook_extract/main.py`
- SHA256: `fe370bd8a9d0f3770e61cff4d9e60e19198e058a0fa1fb0adeb873a9d89c6640`
- Callables: `agent`

The artifact is now ready for a fresh frontier-screen smoke test.
