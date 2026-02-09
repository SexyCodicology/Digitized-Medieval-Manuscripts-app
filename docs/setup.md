# Set up your local environment

This guide walks you through setting up DMMapp on your local machine for development and testing.

## Prerequisites

Before you start, install these tools:

- **Python 3.7 or later** — Required to run the local dashboard server
- **Git** — Required to clone the repository and manage code changes
- **Node.js** (optional) — Only needed if you're working with the documentation site

!!! tip "Check your installations"
    Verify Python is installed by running `python --version` in your terminal. For Git, use `git --version`.

## Get the code

Clone the repository to your local machine:

```bash
git clone https://github.com/[your-username]/Digitized-Medieval-Manuscripts-App.git
cd Digitized-Medieval-Manuscripts-App
```

Replace `[your-username]` with the actual repository owner's GitHub username.

!!! note "Fork first for contributions"
    If you plan to contribute changes, fork the repository on GitHub first, then clone your fork instead.

## Run the dashboard

Start a local web server to view the DMMapp dashboard:

```bash
python -m http.server
```

Open your browser and navigate to:

```
http://localhost:8000
```

You'll see the full dashboard with the library directory, search, and filter features.

!!! tip "Stop the server"
    Press `Ctrl+C` in the terminal to stop the server when you're done.

### Use a different port

If port 8000 is already in use, specify a different port:

```bash
python -m http.server 8080
```

Then visit `http://localhost:8080` instead.

## Run the documentation

The project uses MkDocs to generate documentation from Markdown files.

### Install MkDocs

Install MkDocs and the required theme:

```bash
pip install mkdocs mkdocs-material
```

!!! note "Virtual environments recommended"
    Consider using a Python virtual environment to keep dependencies isolated. Create one with `python -m venv venv` and activate it before installing packages.

### Start the documentation server

Run the MkDocs development server:

```bash
mkdocs serve
```

Open your browser and navigate to:

```
http://localhost:8000
```

The documentation site runs on the same port as the dashboard server. Make sure you stop one before starting the other.

!!! tip "Live reload"
    MkDocs automatically rebuilds the site when you edit Markdown files. Keep the server running while you work and refresh your browser to see changes.

### Build the documentation

Generate static HTML files for the documentation:

```bash
mkdocs build
```

This creates a `site` directory with the complete documentation site. You typically don't need this for local development—it's used for deployment.

## Verify your setup

Test that everything works:

1. **Dashboard**: Run `python -m http.server`, open `http://localhost:8000`, and verify the library list loads
2. **Search**: Type a city name in the search box and confirm the list filters
3. **Documentation**: Run `mkdocs serve`, open `http://localhost:8000`, and navigate between pages

If all three work, you're ready to contribute!

## Troubleshoot common issues

### Python not found

**Windows**: Make sure Python is added to your PATH during installation. Reinstall Python and check "Add Python to PATH."

**macOS/Linux**: You might need to use `python3` instead of `python`:

```bash
python3 -m http.server
```

### Port already in use

If you see "Address already in use," another service is using the port. Either stop that service or use a different port number.

### MkDocs command not found

After installing MkDocs, close and reopen your terminal. If the issue persists, verify pip installed packages to your active Python environment:

```bash
pip show mkdocs
```

## Next steps

Now that your environment is ready:

- [Update the data](update-data.md) — Add or edit library entries
- [View the schema](schema.md) — Understand the data structure
- [Contributing guidelines](contributing.md) — Learn the contribution workflow

Ready to make your first contribution! 🚀
