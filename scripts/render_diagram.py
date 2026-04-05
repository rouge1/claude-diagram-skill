#!/usr/bin/env python3
"""
Render Mermaid diagrams or Chart.js configs as interactive HTML visualizations.

Usage:
    python render_diagram.py <input_file>

Supports:
    - .mmd files (Mermaid diagram syntax)
    - .chart.json files (Chart.js configuration)

The script reads the input, injects it into an HTML template, and opens
the result in the default web browser. Output is saved to a project-local
diagrams/ directory.
"""

import json
import shutil
import sys
import webbrowser
from pathlib import Path


def detect_input_type(filepath):
    """Detect input type from file extension."""
    name = Path(filepath).name.lower()
    if name.endswith('.plotly.json'):
        return 'plotly'
    if name.endswith('.chart.json'):
        return 'chartjs'
    if name.endswith('.mmd'):
        return 'mermaid'
    if name.endswith('.json'):
        return 'chartjs'
    print(f"Error: Unsupported file type: {filepath}")
    print("Supported: .mmd (Mermaid), .chart.json (Chart.js), .plotly.json (Plotly)")
    sys.exit(1)


def read_mermaid_file(filepath):
    """Read Mermaid syntax from file."""
    try:
        content = Path(filepath).read_text(encoding='utf-8').strip()
        if not content:
            raise ValueError("Empty diagram file")
        return content
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def read_chart_file(filepath):
    """Read and validate Chart.js config from JSON file."""
    try:
        content = Path(filepath).read_text(encoding='utf-8').strip()
        if not content:
            raise ValueError("Empty chart file")

        config = json.loads(content)

        if not isinstance(config, dict):
            raise ValueError("Chart config must be a JSON object")
        if 'type' not in config:
            raise ValueError("Chart config must have a 'type' field")
        if 'data' not in config:
            raise ValueError("Chart config must have a 'data' field")

        valid_types = ['line', 'bar', 'pie', 'doughnut', 'radar', 'scatter',
                       'bubble', 'polarArea', 'horizontalBar']
        if config['type'] not in valid_types:
            print(f"Warning: Unrecognized chart type '{config['type']}'. "
                  f"Valid types: {', '.join(valid_types)}")

        return config

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading chart file: {e}")
        sys.exit(1)


def read_plotly_file(filepath):
    """Read and validate Plotly config from JSON file."""
    try:
        content = Path(filepath).read_text(encoding='utf-8').strip()
        if not content:
            raise ValueError("Empty plotly file")

        config = json.loads(content)

        if not isinstance(config, dict):
            raise ValueError("Plotly config must be a JSON object")
        if 'data' not in config:
            raise ValueError("Plotly config must have a 'data' field (array of traces)")
        if not isinstance(config['data'], list):
            raise ValueError("Plotly 'data' must be an array of traces")

        return config

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading plotly file: {e}")
        sys.exit(1)


def get_html_template():
    """Return the HTML template path."""
    script_dir = Path(__file__).parent
    template_path = script_dir.parent / 'templates' / 'viewer.html'

    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)

    return template_path


def get_output_dir(input_path):
    """Return the diagrams directory based on input file location.

    If the input file is already inside a 'diagrams/' directory, use that.
    Otherwise, create a 'diagrams/' directory next to the input file.
    """
    input_path = Path(input_path).resolve()
    parent = input_path.parent

    # If the input is already in a directory called 'diagrams', use it
    if parent.name == 'diagrams':
        parent.mkdir(parents=True, exist_ok=True)
        return parent

    # Otherwise, create a diagrams/ sibling directory
    diagrams_dir = parent / 'diagrams'
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    return diagrams_dir


def discover_diagrams(diagrams_dir):
    """Get sorted list of all HTML diagram files in the directory."""
    return sorted(
        [f.name for f in diagrams_dir.glob('*.html')],
        key=lambda x: (diagrams_dir / x).stat().st_mtime
    )


def inject_template(template_path, render_mode, mermaid_syntax, chart_config,
                     diagram_list, current_file, plotly_config=None):
    """Inject all data into the HTML template in a single pass."""
    html = template_path.read_text(encoding='utf-8')

    html = html.replace('__RENDER_MODE__', json.dumps(render_mode))
    html = html.replace('__MERMAID_DIAGRAM__', json.dumps(mermaid_syntax))
    html = html.replace('__CHART_CONFIG__', json.dumps(chart_config))
    html = html.replace('__PLOTLY_CONFIG__', json.dumps(plotly_config))
    html = html.replace('__DIAGRAM_LIST__', json.dumps(diagram_list))
    html = html.replace('__CURRENT_FILE__', json.dumps(current_file))

    return html


def update_sibling_diagrams(template_path, diagrams_dir, diagram_list,
                            current_stem):
    """Update navigation lists in all other diagram HTML files."""
    source_files = list(diagrams_dir.glob('*.mmd')) + \
                   list(diagrams_dir.glob('*.chart.json')) + \
                   list(diagrams_dir.glob('*.plotly.json'))

    updated = 0
    for src in source_files:
        stem = src.stem
        if src.name.endswith('.plotly.json'):
            stem = src.name.rsplit('.plotly.json', 1)[0]
        elif src.name.endswith('.chart.json'):
            stem = src.name.rsplit('.chart.json', 1)[0]

        if stem == current_stem:
            continue

        html_file = diagrams_dir / f'{stem}.html'
        if not html_file.exists():
            continue

        try:
            input_type = detect_input_type(str(src))
            if input_type == 'mermaid':
                content = read_mermaid_file(str(src))
                html = inject_template(
                    template_path, 'mermaid', content, None,
                    diagram_list, f'{stem}.html'
                )
            elif input_type == 'plotly':
                config = read_plotly_file(str(src))
                html = inject_template(
                    template_path, 'plotly', None, None,
                    diagram_list, f'{stem}.html', config
                )
            else:
                config = read_chart_file(str(src))
                html = inject_template(
                    template_path, 'chartjs', None, config,
                    diagram_list, f'{stem}.html'
                )

            html_file.write_text(html, encoding='utf-8')
            updated += 1
        except Exception as e:
            print(f"  Warning: Could not update {src.name}: {e}")

    if updated:
        print(f"  Updated navigation in {updated} other diagram(s)")


def main():
    """Main execution."""
    if len(sys.argv) != 2:
        print("Usage: python render_diagram.py <input_file>")
        print("  Supported: .mmd (Mermaid), .chart.json (Chart.js)")
        sys.exit(1)

    input_file = sys.argv[1]
    input_type = detect_input_type(input_file)
    input_path = Path(input_file).resolve()

    # Read input
    mermaid_syntax = None
    chart_config = None
    plotly_config = None

    if input_type == 'mermaid':
        mermaid_syntax = read_mermaid_file(input_file)
        print(f"  Read Mermaid diagram from {input_path.name}")
    elif input_type == 'plotly':
        plotly_config = read_plotly_file(input_file)
        trace_count = len(plotly_config.get('data', []))
        print(f"  Read Plotly config from {input_path.name} ({trace_count} traces)")
    else:
        chart_config = read_chart_file(input_file)
        print(f"  Read Chart.js config from {input_path.name} (type: {chart_config['type']})")

    # Determine output location (based on where the input file lives)
    diagrams_dir = get_output_dir(input_path)

    # Determine output stem
    if input_path.name.endswith('.plotly.json'):
        source_stem = input_path.name.rsplit('.plotly.json', 1)[0]
    elif input_path.name.endswith('.chart.json'):
        source_stem = input_path.name.rsplit('.chart.json', 1)[0]
    else:
        source_stem = input_path.stem

    output_file = diagrams_dir / f'{source_stem}.html'

    # Copy source file to diagrams/ if not already there
    if input_path.parent.resolve() != diagrams_dir.resolve():
        dest = diagrams_dir / input_path.name
        shutil.copy2(str(input_path), str(dest))
        print(f"  Source copied to: {dest}")

    # Discover existing diagrams (including the one we're about to write)
    existing = discover_diagrams(diagrams_dir)
    if output_file.name not in existing:
        existing.append(output_file.name)
    diagram_list = existing

    # Load template and inject everything in ONE pass
    template_path = get_html_template()
    html = inject_template(
        template_path, input_type, mermaid_syntax, chart_config,
        diagram_list, output_file.name, plotly_config
    )

    # Save HTML (single write, no double-save)
    output_file.write_text(html, encoding='utf-8')
    print(f"  Saved to: {output_file}")

    # Update sibling diagrams with new navigation list
    update_sibling_diagrams(template_path, diagrams_dir, diagram_list,
                            source_stem)

    # Open in browser AFTER everything is written
    webbrowser.open(output_file.as_uri())
    print(f"  Opening in browser...")

    print(f"\n  Diagram features:")
    print(f"    Theme switcher (top-left)")
    print(f"    Export as PNG/SVG (top-right)")
    print(f"    Zoom: mouse wheel or +/- keys")
    print(f"    Pan: click and drag")
    print(f"    Keyboard: arrows=navigate, r=reset, ?=help")
    print(f"\n  Accessible at: {output_file}")


if __name__ == '__main__':
    main()
