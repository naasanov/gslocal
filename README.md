# gslocal

Run your [Gradescope](https://gradescope.com) autograder locally against any submission, without uploading anything to Gradescope.

gslocal mirrors Gradescope's exact container workflow: it builds your autograder zip, spins up the same Docker base image Gradescope uses, mounts the submission, runs the grader, and prints a formatted score summary. Build and image caching mean repeat runs are fast.

---

## Requirements

- Python 3.9+
- [Docker Desktop](https://docs.docker.com/get-docker/) (running)
- Git

## Installation

```bash
pip install gslocal
```

---

## Quick Start

In your autograder project directory, run:

```bash
gslocal init
```

This walks you through creating a `gslocal.toml` config file. Then test a submission:

```bash
gslocal run path/to/submission.zip
```

---

## How It Works

gslocal expects your autograder project to produce a Gradescope-compatible zip file via a build command. It is agnostic about your build tool - Maven, Make, a shell script, anything that outputs a zip works.

On each run, gslocal:

1. Prepares the submission (zip, directory, or GitHub clone)
2. Runs your build command if source files changed since the last build
3. Generates a Dockerfile and builds a Docker image if the zip is fresh
4. Runs the container with the submission mounted, waits for results
5. Prints a formatted score summary

**Build caching:** gslocal hashes the files listed in your `watch` config. If nothing changed and the output zip exists, the build is skipped entirely. The Docker image is similarly only rebuilt when the zip changes.

---

## Configuration

gslocal is configured via a `gslocal.toml` file in your autograder project root. Run `gslocal init` to generate one interactively.

```toml
[build]
cmd = "mvn clean package"       # command to produce the autograder zip
zip = "target/*.zip"            # glob pattern locating the output zip
watch = ["src/**/*", "pom.xml"] # glob patterns to watch for rebuild triggering

[docker]
setup = "src/main/resources/setup.sh"  # path to setup.sh inside the project (required)
# metadata = "src/main/resources/mock_submission_metadata.json"  # optional

[run]
timeout = 60     # autograder timeout in seconds
verbose = false  # show full build/docker output instead of spinners
```

**Field reference:**

| Field | Required | Description |
|---|---|---|
| `build.cmd` | yes | Shell command to build the autograder zip |
| `build.zip` | yes | Glob pattern to locate the output zip |
| `build.watch` | yes | Glob patterns whose content is hashed to detect source changes |
| `docker.setup` | yes | Path to `setup.sh` relative to project root |
| `docker.metadata` | no | Path to mock submission metadata JSON; a bundled default is used if omitted |
| `run.timeout` | no | Container timeout in seconds (default: 60) |
| `run.verbose` | no | Show full build and Docker output (default: false) |

gslocal locates `gslocal.toml` by walking up the directory tree from your current working directory, so you can run it from any subdirectory of your project.

---

## Submission Types

gslocal accepts submissions in three formats:

```bash
# Zip file
gslocal run test-zips/solution.zip

# Local directory
gslocal run /path/to/student/project/

# GitHub URL (SSH or HTTPS)
gslocal run git@github.com:student/repo.git
gslocal run https://github.com/student/repo
```

GitHub submissions are cloned with `--depth 1`.

---

## Commands

### `gslocal run <submission>`

Run the autograder against a submission.

| Flag | Description |
|---|---|
| `-r, --rebuild` | Force rebuild of build command and Docker image |
| `-n, --no-build` | Skip build, use existing zip |
| `-i, --interactive` | Drop into a shell inside the container |
| `-c, --clean` | Delete temp files after the run |
| `-t, --timeout SECS` | Override timeout (also: `GSLOCAL_TIMEOUT` env var) |
| `-v, --verbose` | Show full build and Docker output |

Timeout precedence: `--timeout` flag > `GSLOCAL_TIMEOUT` env var > `gslocal.toml` value > 60s default.

After each run, the following are available for inspection:

```
.gslocal/
  temp/
    submission/   # prepared submission files
    results/      # results.json
    autograder/   # extracted autograder zip contents
```

### `gslocal init`

Generate a `gslocal.toml` in the current directory. Prompts for each field with example hints. Skipping a required field writes a placeholder value that gslocal will catch and refuse to run with.

| Flag | Description |
|---|---|
| `--placeholders` | Write config with all sentinel values, no prompts |

### `gslocal clean`

Remove local gslocal state for the current project.

| Flag | Description |
|---|---|
| *(none)* | Delete `.gslocal/temp/` only |
| `--image` | Also remove the Docker image for this project |
| `--all` | Delete `.gslocal/` entirely and remove Docker image (full reset) |

---

## Project State

gslocal stores all state in a `.gslocal/` directory at the project root. Add it to your `.gitignore` (`gslocal init` offers to do this automatically):

```
.gslocal/
```

---

## Adding gslocal to an Existing Autograder

1. Install gslocal: `pip install gslocal`
2. Run `gslocal init` in your autograder project root
3. Fill in your build command, zip output path, and the files to watch for changes
4. Add `.gslocal/` to `.gitignore`
5. Run `gslocal run <submission>` to test

---

## Contributing

Contributions are welcome. To get started:

```bash
git clone https://github.com/naasanov/gslocal.git
cd gslocal
pip install -e .
```

The source lives in `src/gslocal/`. Key modules:

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing and subcommand dispatch |
| `config.py` | Config loading, validation, project root resolution |
| `commands/run.py` | Run orchestration |
| `commands/init.py` | Interactive config generation |
| `commands/clean.py` | State cleanup |
| `build.py` | Build invocation and hash-based caching |
| `submission.py` | Submission preparation (zip, dir, GitHub) |
| `docker.py` | Dockerfile generation, image build, container execution |
| `results.py` | Terminal formatting of `results.json` |

Please open an issue before starting work on a large change.

---

## License

[MIT](LICENSE)
