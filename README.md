# Handoff Prompt Skill for Claude Code

A Claude Code skill that generates structured AI continuation documents using the [handoff-prompt methodology](https://www.dontsleeponai.com/handoff-prompt). Never lose context when clearing your AI's memory again.

## What It Does

When your AI context window fills up, you have two bad options: keep pushing and watch quality degrade, or start over and lose everything. Handoff-prompt gives you a third option: **clear your context on purpose** and use a structured document so the next AI picks up exactly where you left off.

This skill automates that process by:
1. Analyzing your current conversation and project state
2. Generating a structured continuation document with 8 sections
3. Saving it to `docs/handoffs/`
4. Clearing your context
5. Providing a resume prompt for your fresh AI session

## Quick Start

### 1. Install the Skill

Copy the entire `handoff-prompt` folder to your Claude Code skills directory:

```bash
# Clone or download the repository
git clone https://github.com/LazyBearCoder/handoff-prompt-skill.git
cd handoff-prompt-skill

# Copy the skill folder to your global skills directory
mkdir -p ~/.claude/skills
cp -r handoff-prompt ~/.claude/skills/

# The skill is now available globally as /handoff
```

**What gets installed:**
- `SKILL.md` — The main skill file with instructions
- `scripts/` — Python tools (context_monitor.py, handoff_cli.py, analytics.py)
- `references/` — Optional documentation

### 2. Configure (Optional)

Add settings to your Claude Code `settings.json`:

```bash
# Edit your settings
~/.claude/settings.json
```

Add this configuration:

```json
{
  "continuationMethod": "ask",
  "handoffMode": "clipboard"
}
```

**continuationMethod** — Choose how to handle context clearing:
- `"ask"` (default) — Ask once which method to use (Compact or Handoff), then remember your choice
- `"compact"` — Always use Claude Code's built-in `/compact`
- `"handoff"` — Always use the handoff-prompt skill

**First-time experience:** When set to `"ask"` (or unset), you'll be prompted to choose between Compact and Handoff the first time you clear context. Your choice is saved automatically.

**handoffMode** — How the resume prompt is delivered (when using Handoff):
- `"clipboard"` (default) — Resume prompt is copied to clipboard after clearing context. You paste it manually.
- `"auto-paste"` — Resume prompt is automatically executed in the fresh conversation.

### 3. Use It

```bash
# Basic usage — generates handoff, no specific next task
/handoff

# With a directive for the next AI
/handoff continue implementing the user authentication flow

# Override mode for this invocation only
/handoff --auto
/handoff --clipboard
```

## What Gets Generated

The continuation document (`docs/handoffs/AI_Continuation_Document-DATE-TIME.md`) includes:

| Section | Purpose |
|---------|---------|
| **Project Identity** | What this project is, objectives, constraints |
| **Current System State** | What's built, partial, broken, not started |
| **Architecture & Technical Map** | Tech stack, data structures, naming conventions |
| **Recent Work** (Highest Priority) | What was done, decisions made and WHY — recency-weighted |
| **What Could Go Wrong** | Known bugs, edge cases, technical debt |
| **How to Think About This Project** | Design philosophy, common mistakes, anti-patterns |
| **Do Not Touch List** | Guardrails to prevent regressing working code |
| **Confidence Flags** | High/Medium/Low confidence per section |

## How It Works

### The Problem

Generic AI summaries treat all information equally, producing bloated output that buries important details. They don't capture *why* you made decisions — only *what* you built.

### The Solution

Handoff-prompt uses:

1. **Recency weighting** — What you did in the last 30 minutes matters 10x more than what you did 3 hours ago
2. **Reasoning preservation** — Captures the reasoning behind decisions, not just the decisions themselves
3. **Regression protection** — Explicit "Do Not Touch" list prevents the next AI from undoing your work
4. **Confidence flags** — The next AI knows what to trust and what to double-check

## Workflow Example

```bash
# You've been working for hours, context is getting heavy
/handoff

# Skill generates: docs/handoffs/AI_Continuation_Document-24Feb2026-1435.md
# Context is cleared automatically
# Resume prompt is in clipboard (or auto-executed if configured)

# In your fresh conversation, paste the resume prompt:
# "I've read the continuation document. I understand the project state,
# the recent work on the authentication system, and the Do Not Touch list.
# What would you like me to work on next?"

# You reply: "Continue with the password reset flow"
```

## Configuration

### Setting: handoffMode

| Value | Behavior |
|-------|----------|
| `clipboard` | Copy resume prompt to clipboard after `/clear` |
| `auto-paste` | Automatically execute resume prompt after `/clear` |

**Location:** `~/.claude/settings.json`

```json
{
  "handoffMode": "auto-paste"
}
```

### Per-Invocation Override

You can override your default setting for any invocation:

```bash
/handoff --auto        # Force auto-paste mode
/handoff --clipboard   # Force clipboard mode
```

## Compact vs Handoff

When you're about to clear your context, you now have two options:

| Feature | Compact | Handoff |
|---------|---------|---------|
| **Speed** | Fast | Slower (more detailed) |
| **Detail level** | Brief summary | 8-section structured document |
| **Decision reasoning** | Minimal | Preserves WHY decisions were made |
| **Architecture** | Basic overview | Full technical map with data structures |
| **Recent work** | Summarized | Recency-weighted with reasoning |
| **Risks & issues** | Maybe mentioned | Dedicated section with edge cases |
| **Regression protection** | No | Explicit "Do Not Touch" list |
| **Confidence flags** | No | Yes — shows what to trust |
| **Best for** | Quick sessions, simple projects | Complex projects, long-term work |

**Choose Compact if:** You're doing quick tasks, simple projects, or just need to reduce context size.

**Choose Handoff if:** You're working on complex projects, need to preserve decision reasoning, or want to hand off work to continue later.

## File Structure

```
handoff-prompt/              # Skill folder (install this entire folder)
├── SKILL.md                 # The main skill file with YAML frontmatter
├── scripts/                 # Python utilities
│   ├── context_monitor.py   # Context usage monitoring tool
│   ├── handoff_cli.py       # Handoff document manager CLI
│   └── analytics.py         # Analytics and reporting tool
├── references/              # Optional documentation
├── README.md                # This file (for GitHub visitors)
├── LICENSE                  # MIT License
├── settings.example.json    # Example configuration
└── docs/                    # Generated continuation documents go here
    └── handoffs/
        └── AI_Continuation_Document-*.md
```

**Note:** The folder structure follows the official [Claude Skills specification](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf).

## Python Tools

Three standalone Python scripts are included to enhance your handoff workflow:

### 1. Context Monitor (`scripts/context_monitor.py`)

Monitors your Claude Code context usage and suggests running `/handoff` when approaching threshold.

```bash
# Check current context status
python scripts/context_monitor.py

# Continuously monitor (updates every 30s)
python scripts/context_monitor.py --watch

# Set custom threshold (default: 80%)
python scripts/context_monitor.py --threshold 75

# Get JSON output for scripting
python scripts/context_monitor.py --json

# Show hook installation instructions
python scripts/context_monitor.py --install-hook
```

**Features:**
- Estimates token usage from conversation files
- Visual progress bar with status indicators
- Configurable warning threshold
- Watch mode for continuous monitoring
- Can be installed as a SessionStart hook

### 2. Handoff CLI (`scripts/handoff_cli.py`)

Manage and search your handoff documents.

```bash
# List all handoff documents
python scripts/handoff_cli.py list

# Show the most recent handoff
python scripts/handoff_cli.py show latest

# Show a specific handoff by number
python scripts/handoff_cli.py show 1

# Search across all handoffs
python scripts/handoff_cli.py search "authentication"

# Compare two handoffs
python scripts/handoff_cli.py diff 1 2
python scripts/handoff_cli.py diff latest 2

# Extract a specific section
python scripts/handoff_cli.py extract latest "recent work"
```

**Features:**
- List all handoffs with timestamps and descriptions
- View specific handoffs or sections
- Full-text search across all documents
- Diff comparison between handoffs
- Extract individual sections

### 3. Analytics (`scripts/analytics.py`)

Generate insights from your handoff history.

```bash
# Overall summary
python scripts/analytics.py summary

# Visual timeline of project
python scripts/analytics.py timeline

# Confidence trends
python scripts/analytics.py confidence

# Extract and categorize issues
python scripts/analytics.py issues

# Generate full HTML report
python scripts/analytics.py report

# Export data as JSON
python scripts/analytics.py --export json
```

**Features:**
- Project timeline visualization
- Confidence trend analysis across sections
- Issue extraction and categorization
- HTML report generation
- JSON data export

## Credits

**Methodology:** [Don't Sleep On AI — handoff-prompt](https://www.dontsleeponai.com/handoff-prompt)

This skill packages the handoff-prompt methodology (v1.1) as an easy-to-use Claude Code skill following the official [Claude Skills specification](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf).

**Version:** 1.1.0

## License

This skill is provided as-is for use with Claude Code. The underlying handoff-prompt methodology is from dontsleeponai.com.

## Contributing

Ideas for improvements:
- [x] Auto-detect context threshold and suggest `/handoff` → `context_monitor.py`
- [x] Visual analytics from handoff history → `analytics.py`
- [x] Handoff document management → `handoff_cli.py`
- [ ] Support for multiple handoff documents (e.g., per-feature)
- [ ] Integration with git to link handoffs to commits
- [ ] Visual confidence indicators in generated documents

Feel free to fork, modify, and share your improvements.
