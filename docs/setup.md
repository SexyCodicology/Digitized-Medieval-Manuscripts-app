---
description: >-
  Step-by-step instructions for setting up DMMapp locally, including
  prerequisites, installing dependencies, and running the MkDocs server.
---

# Set up your local environment

This guide walks you through setting up DMMapp on your local machine for development and testing.

## Prerequisites

Before you start, install these tools:

- **Python 3.7 or later** — Required to install and run MkDocs
- **Git** — Required to clone the repository and manage code changes
- **Node.js** — Only required if you want to run the dashboard's JavaScript test suite locally

!!! tip "Check your installations"
    Verify Python is installed by running `python --version` in your terminal. For Git, use `git --version`. For Node.js, use `node --version`.

## Get the code

Clone the repository to your local machine:

```bash
git clone https://github.com/[your-username]/Digitized-Medieval-Manuscripts-app.git
cd Digitized-Medieval-Manuscripts-app
```

Replace `[your-username]` with the actual repository owner's GitHub username.

!!! note "Fork first for contributions"
    If you plan to contribute changes, fork the repository on GitHub first, then clone your fork instead.

## Install dependencies

Install the MkDocs dependencies defined in `requirements.txt`:

```bash
pip install -r requirements.txt
```

!!! note "Virtual environments recommended"
    Consider using a Python virtual environment to keep dependencies isolated. Create one with `python -m venv venv` and activate it before installing packages.

## Preview the application

The dashboard and the rest of the documentation are both built by MkDocs. The dashboard is the `overrides/home.html` template, rendered from `docs/index.md`, and it loads its data from `docs/assets/data.json`. Run the MkDocs development server to preview everything:

```bash
mkdocs serve
```

Open your browser and navigate to:

```
http://localhost:8000
```

You'll see the full dashboard with the library directory, search, and filter features, alongside the rest of the documentation.

!!! tip "Stop the server"
    Press `Ctrl+C` in the terminal to stop the server when you're done.

!!! tip "Live reload"
    MkDocs automatically rebuilds the site when you edit Markdown, template, or asset files. Keep the server running while you work and refresh your browser to see changes.

### Use a different port

If port 8000 is already in use, specify a different address:

```bash
mkdocs serve -a localhost:8080
```

Then visit `http://localhost:8080` instead.

### Build the site

Generate static HTML files for the complete site:

```bash
mkdocs build --clean
```

This creates a `site` directory with the built dashboard and documentation. You typically don't need this for local development—it's used for deployment.

## Run the automated checks

The [deploy workflow](./workflow-validation.md) runs these same checks on
every pull request, so running them locally first catches problems before you
push.

Install the extra development dependencies, which add `pytest` and
`jsonschema` on top of `requirements.txt`:

```bash
pip install -r requirements-dev.txt
```

Validate `docs/assets/data.json` against `schema.json`, the identifier and
IIIF evidence ledgers, the reviewed link-assertion register, and the
linked-data pilot decisions:

```bash
python scripts/validate_data.py
python scripts/validate_identifier_evidence.py
python scripts/validate_iiif_evidence.py
python scripts/validate_link_assertions.py
python scripts/validate_linked_data_pilot.py
```

Check that your branch hasn't silently dropped a published ID, alias, or
approved link since it diverged from `master`:

```bash
python scripts/verify_identifier_history.py "$(git merge-base HEAD origin/master)"
python scripts/verify_link_assertion_history.py "$(git merge-base HEAD origin/master)"
```

Run the pytest suite covering the build hooks (`hooks/library_pages.py`,
`hooks/linked_data.py`) and scripts. Use `python -m pytest`, not a bare
`pytest`, so the repo root is on `sys.path` and the tests can import `hooks`
and `scripts` as packages:

```bash
python -m pytest tests -q
```

Run the Node test suite covering the dashboard's client-side behavior
(`docs/assets/dashboard.js`). This requires Node.js and installs `jsdom` as
its only dependency:

```bash
npm ci
npm test
```

After `mkdocs build --clean` (see [Build the site](#build-the-site) above),
verify the built linked-data release:

```bash
python scripts/verify_linked_data.py site
```

## Verify your setup

Test that everything works:

1. **Dashboard**: Run `mkdocs serve`, open `http://localhost:8000`, and verify the library list loads
2. **Search**: Type a city name in the search box and confirm the list filters
3. **Documentation**: Navigate between the other documentation pages from the site navigation

If all three work, you're ready to contribute!

## Troubleshoot common issues

### Python not found

**Windows**: Make sure Python is added to your PATH during installation. Reinstall Python and check "Add Python to PATH."

**macOS/Linux**: You might need to use `python3` and `pip3` instead of `python` and `pip`.

### Port already in use

If you see "Address already in use," another service is using port 8000. Run `mkdocs serve -a localhost:8080` to use a different port instead.

### MkDocs command not found

After installing MkDocs, close and reopen your terminal. If the issue persists, verify pip installed packages to your active Python environment:

```bash
pip show mkdocs-material
```

## Next steps

Now that your environment is ready:

- [Update the data](update-data.md) — Add or edit library entries
- [View the schema](schema.md) — Understand the data structure
- [Contributing guidelines](contributing.md) — Learn the contribution workflow

Ready to make your first contribution! 🚀
