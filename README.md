# claude-diagram-skill

A Claude Code skill for generating interactive diagrams, charts, and data visualizations — rendered in the browser with theme switching, export, and keyboard navigation.

## What it does

When you run `/diagram [target]` in Claude Code, it analyzes your code or data and generates an interactive visualization. Three rendering engines cover different use cases:

| Engine | File type | Best for |
|--------|-----------|----------|
| **Mermaid.js** | `.mmd` | Flowcharts, sequence diagrams, ER diagrams, state machines, class diagrams |
| **Chart.js** | `.chart.json` | Line, bar, pie, radar, scatter charts — simple quantitative comparisons |
| **Plotly.js** | `.plotly.json` | Annotations, shaded regions between curves, subplots, reference lines, computed data |

## Install

Copy or symlink this directory to your Claude Code skills path:

```bash
# Option 1: Clone directly
git clone git@github.com:rouge1/claude-diagram-skill.git ~/.claude/skills/diagram

# Option 2: Symlink if you cloned elsewhere
ln -s /path/to/claude-diagram-skill ~/.claude/skills/diagram
```

## Usage

```
/diagram auth flow          # flowchart of authentication logic
/diagram database schema    # ER diagram from your models
/diagram user growth        # line chart with data
/diagram theta decay        # plotly chart with annotations and filled regions
```

Claude picks the right engine automatically based on what you're visualizing.

## Viewer features

All diagrams render in a unified HTML viewer with:

- **Theme switching** — dark/light modes (Mermaid also has forest, neutral)
- **Export** — PNG and SVG (Mermaid), PNG (Chart.js, Plotly)
- **Zoom & pan** — mouse wheel + drag (Mermaid), built-in toolbar (Plotly)
- **Keyboard shortcuts** — `+`/`-` zoom, `r` reset, arrows navigate, `?` help
- **Multi-diagram navigation** — prev/next through all diagrams in a project

## File structure

```
├── SKILL.md                  # Skill definition (what Claude reads)
├── scripts/
│   └── render_diagram.py     # Renders source files into interactive HTML
└── templates/
    └── viewer.html           # HTML template with all three engines
```

## How it works

1. Claude generates a source file (`.mmd`, `.chart.json`, or `.plotly.json`) in `./diagrams/`
2. `render_diagram.py` reads the source, injects it into `viewer.html`, saves the result
3. The HTML opens in your browser with full interactivity
4. Navigation is automatically updated across all diagrams in the project
