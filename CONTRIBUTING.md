# Contributing

Thanks for your interest in contributing to `gslocal`.

## Before You Start

- For small fixes, feel free to open a pull request directly.
- For larger changes, opening an issue first is appreciated so the approach can be discussed, but you are still welcome to open a pull request directly.
- Be respectful and collaborative. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development Setup

Requirements:

- Python 3.9+
- Docker Desktop
- Git

Clone the repository and install the project in editable mode:

```bash
git clone https://github.com/naasanov/gslocal.git
cd gslocal
pip install -e .
```

## Project Layout

The source code lives in `src/gslocal/`.

- `cli.py` contains CLI argument parsing and subcommand dispatch
- `commands/` contains the `init`, `run`, and `clean` commands
- `build.py` handles autograder build execution and caching
- `docker.py` handles Dockerfile generation and container execution
- `submission.py` prepares zip, directory, and GitHub submissions
- `results.py` formats Gradescope results for terminal output

## Making Changes

- Keep changes focused and scoped to the problem being solved.
- Update documentation when behavior or configuration changes.
- Prefer clear, maintainable code over clever shortcuts.
- Avoid breaking command-line behavior or config format without discussion.

## Testing Changes

There is not yet a formal automated test suite in this repository.

Before opening a pull request, please do the following when relevant:

- Run the CLI locally and verify the changed command behaves as expected
- Test against a real or sample autograder project if your change affects runtime behavior
- Check that documentation examples still match actual CLI behavior

Example manual checks:

```bash
gslocal --version
gslocal init --placeholders
gslocal clean --help
gslocal run --help
```

## Pull Requests

When opening a pull request:

- Explain what changed and why
- Describe how you tested it
- Update `CHANGELOG.md` if the change is user-facing and should appear in release notes
- Call out any tradeoffs, known limitations, or follow-up work

Small, focused pull requests are easier to review and merge.
