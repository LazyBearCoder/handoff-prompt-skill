#!/usr/bin/env python3
"""
Handoff Analytics - Generate insights from AI continuation documents

Analyze handoff history to identify trends, recurring issues, confidence
patterns, and project progression over time.

Usage:
    python analytics.py summary                    # Overall summary of all handoffs
    python analytics.py timeline                   # Visual timeline of project
    python analytics.py confidence                 # Show confidence trends
    python analytics.py issues                     # Extract and categorize issues
    python analytics.py report                     # Generate full HTML report
    python analytics.py --export json              # Export data as JSON

Requirements:
    - Python 3.6+
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter, defaultdict


# Import handoff_cli functions (we'll inline key functions to keep standalone)
DEFAULT_HANDOFF_DIR = Path("docs/handoffs")


def find_handoff_directory(start_dir: Path = None) -> Path:
    """Find the handoff directory by searching up from current location."""
    if start_dir is None:
        start_dir = Path.cwd()

    current_handoff = start_dir / DEFAULT_HANDOFF_DIR
    if current_handoff.exists():
        return current_handoff

    for parent in [start_dir, *start_dir.parents]:
        check_path = parent / DEFAULT_HANDOFF_DIR
        if check_path.exists():
            return check_path

    return DEFAULT_HANDOFF_DIR


def list_handoffs(handoff_dir: Path = None) -> List[Path]:
    """List all handoff documents, sorted by modification time (newest first)."""
    if handoff_dir is None:
        handoff_dir = find_handoff_directory()

    if not handoff_dir.exists():
        return []

    handoffs = []
    for file in handoff_dir.glob("AI_Continuation_Document-*.md"):
        if file.is_file():
            handoffs.append(file)

    handoffs.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return handoffs


def parse_handoff(filepath: Path) -> Dict:
    """Parse a handoff document into structured data."""
    content = filepath.read_text()

    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    timestamp_match = re.search(r'(\d{2}[A-Za-z]{3}\d{4}-\d{4})', filepath.name)
    timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"

    return {
        "filepath": filepath,
        "filename": filepath.name,
        "timestamp": timestamp,
        "sections": sections,
        "modified": datetime.fromtimestamp(filepath.stat().st_mtime)
    }


def extract_confidence_levels(sections: Dict) -> Dict[str, str]:
    """Extract confidence levels from sections."""
    confidences = {}

    # Look for confidence indicators in section content
    confidence_pattern = r'[✅❓⚠️]|(high|medium|low)\s*confidence'

    for name, content in sections.items():
        if '✅' in content or 'high confidence' in content.lower():
            confidences[name] = 'high'
        elif '❓' in content or 'low confidence' in content.lower():
            confidences[name] = 'low'
        elif '⚠️' in content or 'medium confidence' in content.lower():
            confidences[name] = 'medium'
        else:
            confidences[name] = 'unknown'

    return confidences


def extract_issues(sections: Dict) -> List[Dict]:
    """Extract issues, bugs, and risks from handoff sections."""
    issues = []

    # Check "What Could Go Wrong" section
    wcgw = sections.get('What Could Go Wrong', '')
    for line in wcgw.split('\n'):
        line = line.strip()
        if line.startswith('-') or line.startswith('*'):
            issues.append({
                'type': 'risk',
                'description': line[1:].strip()
            })

    # Check "Current System State" for broken/partial items
    state = sections.get('Current System State', '')
    for line in state.split('\n'):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['broken', 'bug', 'issue', 'error', 'doesnt work']):
            if line.strip().startswith(('-', '*')):
                issues.append({
                    'type': 'bug',
                    'description': line.strip()[1:].strip()
                })

    return issues


def analyze_handoffs(handoffs: List[Path]) -> Dict:
    """Analyze all handoff documents and extract metrics."""
    data = {
        'total_handoffs': len(handoffs),
        'time_span': None,
        'handoffs': [],
        'issues': [],
        'confidence_trends': defaultdict(lambda: {'high': 0, 'medium': 0, 'low': 0}),
        'sections_frequency': Counter(),
        'project_phases': []
    }

    if not handoffs:
        return data

    timestamps = []

    for handoff in handoffs:
        parsed = parse_handoff(handoff)
        data['handoffs'].append(parsed)
        timestamps.append(parsed['modified'])

        # Extract issues
        issues = extract_issues(parsed['sections'])
        for issue in issues:
            issue['handoff'] = parsed['filename']
            issue['timestamp'] = parsed['modified']
            data['issues'].append(issue)

        # Track confidence levels
        confidences = extract_confidence_levels(parsed['sections'])
        for section, level in confidences.items():
            if level in ('high', 'medium', 'low'):
                data['confidence_trends'][section][level] += 1

        # Count section frequency
        for section_name in parsed['sections'].keys():
            data['sections_frequency'][section_name] += 1

    # Calculate time span
    if timestamps:
        data['time_span'] = {
            'start': min(timestamps),
            'end': max(timestamps),
            'duration_days': (max(timestamps) - min(timestamps)).days
        }

    return data


def print_summary(data: Dict):
    """Print a summary of handoff analytics."""
    print(f"\n{'='*70}")
    print(f"  Handoff Analytics Summary")
    print(f"{'='*70}\n")

    print(f"Total handoffs:        {data['total_handoffs']}")
    print(f"Total issues found:    {len(data['issues'])}")

    if data['time_span']:
        span = data['time_span']
        print(f"Time span:             {span['start'].strftime('%Y-%m-%d')} to {span['end'].strftime('%Y-%m-%d')}")
        print(f"Duration:              {span['duration_days']} days")
        if span['duration_days'] > 0:
            freq = data['total_handoffs'] / span['duration_days']
            print(f"Frequency:             {freq:.2f} handoffs/day")

    print(f"\n{'='*70}")
    print(f"  Most Common Sections")
    print(f"{'='*70}\n")

    for section, count in data['sections_frequency'].most_common(10):
        bar = '█' * (count * 2)
        print(f"  {section[:30]:<30} {bar} ({count})")

    print(f"\n{'='*70}")
    print(f"  Issues Summary")
    print(f"{'='*70}\n")

    issue_types = Counter([i['type'] for i in data['issues']])
    for issue_type, count in issue_types.most_common():
        print(f"  {issue_type.capitalize():<15} {count}")

    return 0


def print_timeline(data: Dict):
    """Print a visual timeline of handoffs."""
    if not data['handoffs']:
        print("No handoffs to display.")
        return 1

    print(f"\n{'='*70}")
    print(f"  Project Timeline")
    print(f"{'='*70}\n")

    for i, handoff in enumerate(data['handoffs'][:20], 1):  # Limit to 20
        parsed = handoff
        time_str = parsed['modified'].strftime('%Y-%m-%d %H:%M')

        # Extract brief description from Project Identity
        identity = parsed['sections'].get('Project Identity', '')
        desc = identity.split('\n')[0][:50] if identity else 'No description'

        print(f"{i:2d}. [{time_str}] {desc}")

    if len(data['handoffs']) > 20:
        print(f"\n... and {len(data['handoffs']) - 20} more")

    return 0


def print_confidence(data: Dict):
    """Print confidence trends across sections."""
    if not data['confidence_trends']:
        print("No confidence data found.")
        return 1

    print(f"\n{'='*70}")
    print(f"  Confidence Trends by Section")
    print(f"{'='*70}\n")

    for section, levels in data['confidence_trends'].items():
        total = sum(levels.values())
        if total == 0:
            continue

        high_pct = (levels['high'] / total) * 100
        med_pct = (levels['medium'] / total) * 100
        low_pct = (levels['low'] / total) * 100

        print(f"{section}:")
        print(f"  ✅ High:   {levels['high']:>3} ({high_pct:>5.1f}%)")
        print(f"  ⚠️  Medium: {levels['medium']:>3} ({med_pct:>5.1f}%)")
        print(f"  ❓ Low:    {levels['low']:>3} ({low_pct:>5.1f}%)")
        print()

    return 0


def print_issues(data: Dict):
    """Print categorized issues from all handoffs."""
    if not data['issues']:
        print("No issues found.")
        return 0

    # Group issues by type
    by_type = defaultdict(list)
    for issue in data['issues']:
        by_type[issue['type']].append(issue)

    print(f"\n{'='*70}")
    print(f"  Issues Extracted ({len(data['issues'])} total)")
    print(f"{'='*70}\n")

    for issue_type, issues in by_type.items():
        print(f"\n{issue_type.upper()} ({len(issues)})")
        print(f"{'-'*70}")

        # Show recent issues first
        issues.sort(key=lambda i: i['timestamp'], reverse=True)
        for issue in issues[:10]:
            time_str = issue['timestamp'].strftime('%Y-%m-%d')
            print(f"  [{time_str}] {issue['description'][:70]}")

        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")

    return 0


def generate_html_report(data: Dict, output_path: Path = None):
    """Generate an HTML report with all analytics."""
    if output_path is None:
        output_path = Path("handoff-report.html")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Handoff Analytics Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #1e40af; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 15px 30px 15px 0; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #2563eb; }}
        .metric-label {{ font-size: 14px; color: #6b7280; text-transform: uppercase; }}
        .section-bar {{ height: 24px; background: #2563eb; border-radius: 4px; margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; }}
        .confidence-high {{ color: #059669; }}
        .confidence-medium {{ color: #d97706; }}
        .confidence-low {{ color: #dc2626; }}
        .issue-bug {{ border-left: 3px solid #dc2626; padding-left: 10px; }}
        .issue-risk {{ border-left: 3px solid #d97706; padding-left: 10px; }}
        .timestamp {{ color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Handoff Analytics Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Overview</h2>
        <div class="metric">
            <div class="metric-value">{data['total_handoffs']}</div>
            <div class="metric-label">Total Handoffs</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(data['issues'])}</div>
            <div class="metric-label">Issues Found</div>
        </div>
"""

    if data['time_span']:
        html += f"""
        <div class="metric">
            <div class="metric-value">{data['time_span']['duration_days']}</div>
            <div class="metric-label">Days Active</div>
        </div>
"""

    # Sections section
    html += """
        <h2>Most Common Sections</h2>
        <table>
            <tr><th>Section</th><th>Frequency</th></tr>
"""
    for section, count in data['sections_frequency'].most_common():
        html += f"            <tr><td>{section}</td><td>{count}</td></tr>\n"
    html += "        </table>\n"

    # Confidence section
    html += """
        <h2>Confidence Trends</h2>
        <table>
            <tr><th>Section</th><th>High</th><th>Medium</th><th>Low</th></tr>
"""
    for section, levels in data['confidence_trends'].items():
        total = sum(levels.values())
        if total > 0:
            html += f"            <tr><td>{section}</td>"
            html += f"<td class='confidence-high'>{levels['high']}</td>"
            html += f"<td class='confidence-medium'>{levels['medium']}</td>"
            html += f"<td class='confidence-low'>{levels['low']}</td></tr>\n"
    html += "        </table>\n"

    # Issues section
    if data['issues']:
        html += """
        <h2>Issues</h2>
        <table>
            <tr><th>Type</th><th>Description</th><th>Found</th></tr>
"""
        for issue in sorted(data['issues'], key=lambda i: i['timestamp'], reverse=True)[:50]:
            time_str = issue['timestamp'].strftime('%Y-%m-%d')
            html += f"            <tr class='issue-{issue['type']}'>"
            html += f"<td>{issue['type']}</td>"
            html += f"<td>{issue['description'][:80]}</td>"
            html += f"<td>{time_str}</td></tr>\n"
        html += "        </table>\n"

    # Timeline section
    html += """
        <h2>Timeline</h2>
        <table>
            <tr><th>When</th><th>Handoff</th></tr>
"""
    for handoff in data['handoffs'][:30]:
        time_str = handoff['modified'].strftime('%Y-%m-%d %H:%M')
        identity = handoff['sections'].get('Project Identity', '')
        desc = identity.split('\n')[0][:60] if identity else 'No description'
        html += f"            <tr><td>{time_str}</td><td>{desc}</td></tr>\n"
    html += "        </table>\n"

    html += """
    </div>
</body>
</html>
"""

    output_path.write_text(html)
    print(f"\n✅ HTML report generated: {output_path}")
    print(f"   Open in browser: file://{output_path.absolute()}")

    return 0


def export_json(data: Dict, output_path: Path = None):
    """Export analytics data as JSON."""
    if output_path is None:
        output_path = Path("handoff-analytics.json")

    # Convert datetime objects to strings for JSON serialization
    export_data = {
        'total_handoffs': data['total_handoffs'],
        'issues': [
            {**issue, 'timestamp': issue['timestamp'].isoformat()}
            for issue in data['issues']
        ],
        'confidence_trends': dict(data['confidence_trends']),
        'sections_frequency': dict(data['sections_frequency']),
    }

    if data['time_span']:
        export_data['time_span'] = {
            'start': data['time_span']['start'].isoformat(),
            'end': data['time_span']['end'].isoformat(),
            'duration_days': data['time_span']['duration_days']
        }

    output_path.write_text(json.dumps(export_data, indent=2))
    print(f"\n✅ JSON export saved: {output_path}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate analytics from handoff documents"
    )

    parser.add_argument(
        '--export', '-e',
        choices=['json', 'html'],
        help='Export format'
    )

    subparsers = parser.add_subparsers(dest='command', help='Analytics commands')

    subparsers.add_parser('summary', help='Show overall summary')
    subparsers.add_parser('timeline', help='Show project timeline')
    subparsers.add_parser('confidence', help='Show confidence trends')
    subparsers.add_parser('issues', help='Show extracted issues')
    subparsers.add_parser('report', help='Generate full HTML report')

    args = parser.parse_args()

    # Load and analyze data
    handoffs = list_handoffs()

    if not handoffs:
        print("No handoff documents found.")
        print("Create one with: /handoff")
        return 1

    data = analyze_handoffs(handoffs)

    # Handle export
    if args.export == 'json':
        return export_json(data)
    elif args.export == 'html':
        return generate_html_report(data)

    # Handle commands
    if not args.command:
        return print_summary(data)

    commands = {
        'summary': print_summary,
        'timeline': print_timeline,
        'confidence': print_confidence,
        'issues': print_issues,
        'report': lambda d: generate_html_report(d)
    }

    handler = commands.get(args.command)
    if handler:
        return handler(data)

    return 1


if __name__ == "__main__":
    sys.exit(main())
