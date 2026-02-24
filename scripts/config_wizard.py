#!/usr/bin/env python3
"""
Configuration Wizard for handoff-prompt skill

An interactive TUI wizard for configuring the handoff-prompt skill.
Guides users through first-time setup with keyboard-driven menus.

Usage:
    python config_wizard.py
    python config_wizard.py --help
    python config_wizard.py --version

Requirements:
    - Python 3.6+
    - simple-term-menu: pip install simple-term-menu (optional, provides better UI)

Version: 1.0.0
"""

import os
import sys
import json
import argparse
from pathlib import Path


__version__ = "1.0.0"


def get_config_paths():
    """
    Get possible configuration paths based on fallback chain.

    Returns:
        dict: Paths for project and global config
    """
    # Determine project root (current directory or parent of scripts/)
    script_path = Path(__file__).absolute()
    project_root = script_path.parent.parent

    # Project-specific config
    project_config_dir = project_root / ".claude" / "skills" / "handoff-prompt"
    project_config = project_config_dir / "config.json"

    # Global config
    home = Path.home()
    global_config_dir = home / ".claude" / "skills" / "handoff-prompt"
    global_config = global_config_dir / "config.json"

    return {
        "project_root": project_root,
        "project_config_dir": project_config_dir,
        "project_config": project_config,
        "global_config_dir": global_config_dir,
        "global_config": global_config,
    }


def existing_config():
    """
    Check for existing configuration files.

    Returns:
        dict: Info about existing configs
    """
    paths = get_config_paths()
    return {
        "project_exists": paths["project_config"].exists(),
        "global_exists": paths["global_config"].exists(),
    }


def load_existing_config():
    """
    Load existing configuration if available.

    Returns:
        dict: Existing config or empty dict
    """
    paths = get_config_paths()

    # Check project config first
    if paths["project_config"].exists():
        try:
            with open(paths["project_config"], "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Check global config
    if paths["global_config"].exists():
        try:
            with open(paths["global_config"], "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    return {}


def save_config(config, scope="project"):
    """
    Save configuration to the specified scope.

    Args:
        config (dict): Configuration to save
        scope (str): "project" or "global"

    Returns:
        Path: Path to saved config file
    """
    paths = get_config_paths()

    if scope == "project":
        config_dir = paths["project_config_dir"]
        config_path = paths["project_config"]
    else:
        config_dir = paths["global_config_dir"]
        config_path = paths["global_config"]

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Save config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


def try_import_menu():
    """
    Try to import simple-term-menu, provide fallback instructions.

    Returns:
        module or None: The menu module if available
    """
    try:
        from simple_term_menu import TerminalMenu
        return TerminalMenu
    except ImportError:
        return None


def show_install_hint():
    """Show hint about installing simple-term-menu for better UX."""
    if try_import_menu() is None:
        print()
        print("Tip: Install 'simple-term-menu' for a better TUI experience:")
        print("  pip install simple-term-menu")
        print()


def show_menu_simple(options, title=None, cursor=None):
    """
    Show a simple text-based menu without dependencies.

    Args:
        options (list): List of option strings
        title (str): Menu title
        cursor (int): Initial cursor position

    Returns:
        int or None: Index of selected option, or None if cancelled
    """
    print()
    if title:
        print(title)
        print("=" * len(title))

    for i, option in enumerate(options):
        prefix = "> " if i == cursor else "  "
        print(f"{prefix}{i + 1}. {option}")

    print()
    print("Use arrow keys to navigate, Enter to select, q to quit")

    return cursor


def is_interactive():
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def run_fallback_menu(options, title=None):
    """
    Run a fallback menu using basic input for systems without simple-term-menu.

    Args:
        options (list): List of option strings
        title (str): Menu title

    Returns:
        int or None: Index of selected option, or None if cancelled
    """
    if not is_interactive():
        # Non-interactive mode: use simple input prompt
        print()
        if title:
            print(title)
        print()
        for i, option in enumerate(options):
            print(f"{i + 1}. {option}")
        print()

        try:
            choice = input("Enter choice (number): ").strip()
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(options):
                    return num - 1
        except (EOFError, KeyboardInterrupt):
            return None

        return None

    # Interactive mode with arrow key support
    try:
        import tty
        import termios

        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch == '\x1b':  # Escape sequence
                    # Read the rest of the escape sequence
                    ch += sys.stdin.read(2)
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (ImportError, termios.error):
        # Fallback to simple input on error or Windows
        def getch():
            # Use simple input() as fallback
            return None

        # Use simple input-based menu
        print()
        if title:
            print(title)
        print()
        for i, option in enumerate(options):
            print(f"{i + 1}. {option}")
        print()

        try:
            choice = input("Enter choice (number): ").strip()
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(options):
                    return num - 1
        except (EOFError, KeyboardInterrupt):
            return None

        return None

    cursor = 0

    while True:
        # Clear screen and show menu (print newlines for portability)
        print("\n" * 100)
        show_menu_simple(options, title, cursor)

        # Get input
        try:
            key = getch()

            if key is None:
                # getch failed, fall back to number input
                break

            if key == 'q' or key == '\x03':  # q or Ctrl+C
                return None
            elif key == '\r' or key == '\n':  # Enter
                return cursor
            elif key == '\x1b[A':  # Up arrow
                cursor = max(0, cursor - 1)
            elif key == '\x1b[B':  # Down arrow
                cursor = min(len(options) - 1, cursor + 1)
            elif key.isdigit():
                # Number key selection
                num = int(key)
                if 1 <= num <= len(options):
                    return num - 1
        except (EOFError, KeyboardInterrupt):
            return None

    # Final fallback to numbered input
    print()
    if title:
        print(title)
    print()
    for i, option in enumerate(options):
        print(f"{i + 1}. {option}")
    print()

    try:
        choice = input("Enter choice (number): ").strip()
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(options):
                return num - 1
    except (EOFError, KeyboardInterrupt):
        pass

    return None


def run_tui_menu(options, title=None):
    """
    Run a TUI menu using simple-term-menu if available, with fallback.

    Args:
        options (list): List of option strings
        title (str): Menu title

    Returns:
        int or None: Index of selected option, or None if cancelled
    """
    TerminalMenu = try_import_menu()

    if TerminalMenu:
        # Use simple-term-menu
        menu = TerminalMenu(
            options,
            title=title,
            cycle_cursor=True,
            clear_screen=True,
        )
        selection = menu.show()
        return selection
    else:
        # Fallback to basic menu
        return run_fallback_menu(options, title)


def show_welcome():
    """Show welcome screen and initial prompt."""
    print()
    print("=" * 60)
    print("  handoff-prompt Configuration Wizard")
    print("=" * 60)
    print()
    print("This wizard will help you configure the handoff-prompt skill.")
    print()
    print("handoff-prompt helps you create structured AI continuation")
    print("documents before clearing context, enabling seamless handoff")
    print("to a fresh AI instance.")
    print()


def ask_configure_now():
    """
    Ask if user wants to configure now.

    Returns:
        bool: True if user wants to configure
    """
    options = ["Yes, configure now", "No, exit"]
    title = "Do you want to configure handoff-prompt now?"

    selection = run_tui_menu(options, title)

    if selection is None:
        return False

    return selection == 0


def ask_continuation_method():
    """
    Ask user to choose continuation method.

    Returns:
        str: "compact" or "handoff"
    """
    options = [
        "Compact  - Claude Code's built-in context summarization",
        "Handoff  - Generate structured continuation document",
    ]
    title = "Choose continuation method:"

    print()
    print("Continuation Method Options:")
    print("-" * 40)
    print("Compact:   Faster, less detailed. Good for quick context reduction.")
    print("Handoff:   Creates 8-section document with decisions and reasoning.")
    print("           Better for complex projects and long-term work.")
    print()

    selection = run_tui_menu(options, title)

    if selection is None:
        return None

    return "compact" if selection == 0 else "handoff"


def ask_handoff_mode():
    """
    Ask user to choose handoff mode.

    Returns:
        str: "clipboard" or "auto-paste"
    """
    options = [
        "Clipboard   - Copy resume prompt to clipboard",
        "Auto-paste  - Automatically execute resume prompt",
    ]
    title = "Choose resume prompt delivery:"

    print()
    print("Resume Prompt Delivery Options:")
    print("-" * 40)
    print("Clipboard:  Resume prompt is copied. You paste it manually.")
    print("Auto-paste: Resume prompt executes automatically after /clear.")
    print()

    selection = run_tui_menu(options, title)

    if selection is None:
        return None

    return "clipboard" if selection == 0 else "auto-paste"


def ask_config_scope():
    """
    Ask user to choose configuration scope.

    Returns:
        str: "project" or "global"
    """
    paths = get_config_paths()

    options = [
        f"Project   - Save to .claude/skills/handoff-prompt/config.json",
        f"Global    - Save to ~/.claude/skills/handoff-prompt/config.json",
    ]
    title = "Save configuration globally or for this project only?"

    print()
    print("Configuration Scope:")
    print("-" * 40)
    print(f"Project path: {paths['project_config']}")
    print(f"Global path:  {paths['global_config']}")
    print()
    print("Project:  Only affects this project.")
    print("Global:   Applies to all projects (recommended).")
    print()

    selection = run_tui_menu(options, title)

    if selection is None:
        return None

    return "project" if selection == 0 else "global"


def run_wizard():
    """
    Run the full configuration wizard.

    Returns:
        dict or None: Configuration dict if successful, None if cancelled
    """
    show_welcome()

    # Ask if user wants to configure
    if not ask_configure_now():
        print("\nExiting without making changes.")
        return None

    # Ask for continuation method
    continuation_method = ask_continuation_method()
    if continuation_method is None:
        print("\nConfiguration cancelled.")
        return None

    # Ask for handoff mode (only if handoff selected)
    handoff_mode = "clipboard"  # default
    if continuation_method == "handoff":
        handoff_mode = ask_handoff_mode()
        if handoff_mode is None:
            print("\nConfiguration cancelled.")
            return None

    # Ask for config scope
    scope = ask_config_scope()
    if scope is None:
        print("\nConfiguration cancelled.")
        return None

    # Build configuration
    config = {
        "continuationMethod": continuation_method,
        "handoffMode": handoff_mode,
    }

    # Save configuration
    try:
        config_path = save_config(config, scope)
        print()
        print("=" * 60)
        print("  Configuration Saved Successfully!")
        print("=" * 60)
        print()
        print(f"Location: {config_path}")
        print()
        print("Configuration:")
        print(f"  continuationMethod: {continuation_method}")
        print(f"  handoffMode: {handoff_mode}")
        print()
        print("You can change these settings anytime by:")
        print("  1. Running this wizard again")
        print(f"  2. Editing {config_path}")
        print()

        return config

    except Exception as e:
        print()
        print(f"Error saving configuration: {e}")
        return None


def print_version():
    """Print version information."""
    print(f"Configuration Wizard for handoff-prompt v{__version__}")
    print()


def print_help():
    """Print help information."""
    print()
    print("=" * 60)
    print("  handoff-prompt Configuration Wizard")
    print("=" * 60)
    print()
    print("USAGE:")
    print("  python config_wizard.py [OPTIONS]")
    print()
    print("OPTIONS:")
    print("  -h, --help     Show this help message")
    print("  -v, --version  Show version information")
    print("  --check        Check existing configuration without running wizard")
    print()
    print("DESCRIPTION:")
    print("  This wizard guides you through configuring the handoff-prompt skill.")
    print("  You can choose:")
    print("    - Continuation method (Compact or Handoff)")
    print("    - Resume prompt delivery (if using Handoff)")
    print("    - Configuration scope (project or global)")
    print()
    print("CONFIGURATION LOCATIONS:")
    paths = get_config_paths()
    print(f"  Project: {paths['project_config']}")
    print(f"  Global:  {paths['global_config']}")
    print()
    print("For more information, visit:")
    print("  https://github.com/LazyBearCoder/handoff-prompt-skill")
    print()


def check_config():
    """Check and display existing configuration."""
    paths = get_config_paths()
    existing = existing_config()

    print()
    print("Existing Configuration:")
    print("-" * 40)

    if existing["project_exists"]:
        print(f"✓ Project: {paths['project_config']}")
        try:
            with open(paths["project_config"], "r") as f:
                config = json.load(f)
            print(f"  continuationMethod: {config.get('continuationMethod', 'not set')}")
            print(f"  handoffMode: {config.get('handoffMode', 'not set')}")
        except Exception as e:
            print(f"  Error reading config: {e}")
    else:
        print(f"✗ Project: {paths['project_config']} (not found)")

    if existing["global_exists"]:
        print(f"✓ Global: {paths['global_config']}")
        try:
            with open(paths["global_config"], "r") as f:
                config = json.load(f)
            print(f"  continuationMethod: {config.get('continuationMethod', 'not set')}")
            print(f"  handoffMode: {config.get('handoffMode', 'not set')}")
        except Exception as e:
            print(f"  Error reading config: {e}")
    else:
        print(f"✗ Global: {paths['global_config']} (not found)")

    if not existing["project_exists"] and not existing["global_exists"]:
        print("  No configuration found. Run the wizard to create one.")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Configuration Wizard for handoff-prompt skill",
        add_help=False
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message"
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version information"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check existing configuration without running wizard"
    )

    args = parser.parse_args()

    if args.help:
        print_help()
        return 0

    if args.version:
        print_version()
        return 0

    if args.check:
        check_config()
        return 0

    # Show install hint if simple-term-menu is not available
    TerminalMenu = try_import_menu()
    if TerminalMenu is None and is_interactive():
        show_install_hint()

    # Check for existing configuration
    existing = existing_config()

    if existing["project_exists"] or existing["global_exists"]:
        print()
        print("Existing configuration detected:")
        if existing["project_exists"]:
            paths = get_config_paths()
            print(f"  - Project: {paths['project_config']}")
        if existing["global_exists"]:
            paths = get_config_paths()
            print(f"  - Global:  {paths['global_config']}")
        print()

        options = [
            "Run wizard to update configuration",
            "Exit without changes",
        ]
        title = "What would you like to do?"

        selection = run_tui_menu(options, title)

        if selection is None or selection == 1:
            print("\nExiting.")
            return 0

    # Run the wizard
    config = run_wizard()

    if config:
        return 0
    else:
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
        sys.exit(1)
