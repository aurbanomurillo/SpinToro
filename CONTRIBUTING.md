# Contributing

Thanks for your interest in improving SpinToro.

## Before you start

- Read the README to understand the two entry points: `console.py` and `main.py`.
- Keep the torus math intact unless a change explicitly requires otherwise.
- Prefer minimal edits that preserve the existing style of the code.

## Suggested workflow

1. Create a feature branch.
2. Make focused changes.
3. Run the relevant script:
   - `python console.py` for console rendering changes.
   - `python main.py` for export changes.
4. Verify the output.
5. Open a pull request with a clear summary.

## Commit messages

Use concise, professional commit messages written in English. Good examples:

- `docs: add project overview and usage guide`
- `chore: ignore generated video assets`
- `feat: add console renderer restoration`

## Expectations

- Avoid unrelated refactors.
- Do not change the donut mathematics unless necessary.
- Update documentation when behavior changes.
