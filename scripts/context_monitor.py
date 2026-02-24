#!/usr/bin/env python3
"""
Context Monitor for Claude Code + Handoff-Prompt

Monitors Claude Code context window usage and suggests running /handoff
when approaching the configured threshold.

Usage:
    python context_monitor.py                    # Check current context status
    python context_monitor.py --watch            # Continuously monitor (updates every 30s)
    python context_monitor.py --threshold 80     # Set custom threshold (default: 80%)
    python context_monitor.py --install-hook     # Show hook installation instructions

Requirements:
    - macOS/Linux with Claude Code
    - Python 3.6+
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path


# Default configuration
DEFAULT_THRESHOLD = 80  # Suggest handoff at 80% context usage
CHECK_INTERVAL = 30     # Seconds between checks in watch mode


def get_claude_context_path():
    """
    Find Claude Code's context storage location.
    May vary by OS and Claude Code version.
    """
    home = Path.home()

    # Possible locations (adjust as Claude Code evolves)
    possible_paths = [
        home / ".claude" / "context" / "current.json",
        home / ".claude" / "sessions" / "current" / "context.json",
        home / ".config" / "claude-code" / "context.json",
        home / "Library" / "Application Support" / "Claude Code" / "context.json",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def estimate_context_usage():
    """
    Estimate context window usage.

    Since Claude Code doesn't expose exact token counts,
    we estimate based on conversation history file size
    and typical token-to-byte ratio.

    Returns: dict with usage information
    """
    context_path = get_claude_context_path()

    if not context_path:
        # If we can't find context file, check common session locations
        home = Path.home()
        session_dirs = [
            home / ".claude" / "sessions",
            home / "Library" / "Application Support" / "Claude Code" / "sessions",
        ]

        total_size = 0
        for session_dir in session_dirs:
            if session_dir.exists():
                for file in session_dir.rglob("*.json"):
                    try:
                        total_size += file.stat().st_size
                    except (OSError, PermissionError):
                        pass

        file_size = total_size
    else:
        file_size = context_path.stat().st_size

    # Estimate: ~4 characters per token
    estimated_tokens = file_size / 4

    # Claude Sonnet 4.6 has ~200k context window
    max_tokens = 200_000

    percentage = min(100, (estimated_tokens / max_tokens) * 100)

    # Determine status
    if percentage >= 90:
        status = "CRITICAL"
    elif percentage >= 80:
        status = "WARNING"
    elif percentage >= 60:
        status = "MODERATE"
    else:
        status = "OK"

    return {
        "tokens_used": int(estimated_tokens),
        "tokens_total": max_tokens,
        "percentage": round(percentage, 1),
        "status": status,
        "file_size": file_size,
        "context_path": str(context_path) if context_path else "Not found"
    }


def format_status_bar(usage, width=50):
    """Create a visual status bar."""
    filled = int((usage["percentage"] / 100) * width)

    # Choose bar character based on status
    if usage["status"] in ("CRITICAL", "WARNING"):
        bar_char = "█"
    elif usage["status"] == "MODERATE":
        bar_char = "│"
    else:
        bar_char = "│"

    filled_part = bar_char * filled
    empty_part = "░" * (width - filled)

    return filled_part + empty_part


def print_status(usage, threshold=DEFAULT_THRESHOLD):
    """Print formatted context status."""
    print(f"\n{'='*60}")
    print(f"  Claude Code Context Monitor")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    print(f"Status:         {usage['status']}")
    print(f"Tokens Used:    {usage['tokens_used']:,} / {usage['tokens_total']:,}")
    print(f"Usage:          {usage['percentage']}%")

    print(f"\n[{format_status_bar(usage)}] {usage['percentage']}%")

    # Handoff suggestion
    if usage["percentage"] >= threshold:
        print(f"\n{'='*60}")
        print(f"  ⚠️  RECOMMENDATION: Run /handoff now")
        print(f"  Your context is at {usage['percentage']}% (threshold: {threshold}%)")
        print(f"  Run: /handoff")
        print(f"{'='*60}\n")
    elif usage["percentage"] >= threshold - 10:
        print(f"\n  ℹ️  Approaching threshold. Consider /handoff soon.\n")
    else:
        print(f"\n  ✅ Context level is healthy.\n")


def clear_screen():
    """Clear terminal screen in a cross-platform way."""
    # Print newlines to clear screen (safer than os.system)
    print("\n" * 100)


def watch_mode(threshold=DEFAULT_THRESHOLD):
    """Continuously monitor context usage."""
    print(f"Monitoring context usage (updating every {CHECK_INTERVAL}s)")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            clear_screen()
            usage = estimate_context_usage()
            print_status(usage, threshold)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def install_hook(threshold=DEFAULT_THRESHOLD):
    """
    Generate instructions for installing as a Claude Code hook.

    Claude Code hooks are configured in ~/.claude/settings.json
    """
    hook_script = Path(__file__).absolute()
    hook_config = {
        "hooks": {
            "SessionStart": f"python {hook_script} --threshold {threshold}"
        }
    }

    print("\n" + "="*60)
    print("  Hook Installation Instructions")
    print("="*60 + "\n")

    print("Add the following to your ~/.claude/settings.json:\n")
    print(json.dumps(hook_config, indent=2))
    print("\n" + "="*60)
    print("\nThis will run context_monitor at the start of each session.")
    print("You'll see a warning if your context is above the threshold.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Claude Code context usage and suggest /handoff"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Threshold percentage (default: {DEFAULT_THRESHOLD}%)"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Continuously monitor (update every 30s)"
    )
    parser.add_argument(
        "--install-hook",
        action="store_true",
        help="Show instructions for installing as a SessionStart hook"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON for scripting"
    )

    args = parser.parse_args()

    # Get current usage
    usage = estimate_context_usage()

    if args.json:
        # JSON output for scripting
        print(json.dumps({
            **usage,
            "threshold": args.threshold,
            "should_handoff": usage["percentage"] >= args.threshold
        }))
        return 0 if usage["percentage"] < args.threshold else 1

    if args.install_hook:
        install_hook(args.threshold)
        return 0

    if args.watch:
        watch_mode(args.threshold)
        return 0

    # Single check mode
    print_status(usage, args.threshold)

    # Exit code based on threshold
    return 0 if usage["percentage"] < args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
