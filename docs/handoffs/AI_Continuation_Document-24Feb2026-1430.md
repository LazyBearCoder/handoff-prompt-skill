# PROJECT CONTINUATION DOCUMENT
## Session 1 — February 24, 2026

### 1. PROJECT IDENTITY

- **Project Name:** handoff-prompt-skill
- **What This Project Is:** A Claude Code skill that generates structured AI continuation documents, plus Python tooling for monitoring context, managing documents, and analyzing handoff history.
- **Primary Objective:** Enable seamless context handoff between AI sessions without losing project state, decisions, or reasoning.
- **Strategic Intent:** Solve the context window problem — when AI conversations get too long, quality degrades. This allows proactive context clearing with full continuity.
- **Hard Constraints:** Must work as a standalone skill (no external dependencies beyond Claude Code), Python scripts must be standalone (no pip install required), must include attribution to dontsleeponai.com.

### 2. WHAT EXISTS RIGHT NOW

- **What is built and working:**
  - `handoff-prompt.md` — Complete skill file with documentation and the handoff prompt
  - `context_monitor.py` — Standalone script to monitor context usage and suggest /handoff at threshold
  - `handoff_cli.py` — CLI tool to list, view, search, diff, and extract from handoff documents
  - `analytics.py` — Analytics tool for timelines, confidence trends, issue extraction, HTML reports
  - `README.md` — Full documentation with installation and usage instructions
  - `settings.example.json` — Example configuration

- **What is partially built:**
  - Skill is complete but not yet installed/tested in a live Claude Code environment
  - Python scripts are written but not tested on actual handoff data

- **What is broken or blocked:**
  - Nothing known

- **What has NOT been started yet:**
  - Live testing in Claude Code with actual conversations
  - Any refinements based on real-world usage

### 3. ARCHITECTURE & TECHNICAL MAP

- **Tech stack / tools / platforms:**
  - Claude Code (skill system via .md files)
  - Python 3.6+ (standalone scripts, no external dependencies)
  - Markdown (continuation document format)

- **Key data structures, tables, files, or repos:**
  - `docs/handoffs/AI_Continuation_Document-*.md` — Generated handoff documents
  - `~/.claude/skills/` — Claude Code skills installation directory
  - `~/.claude/settings.json` — Configuration for handoffMode setting

- **How the system works end-to-end:**
  1. User runs `/handoff [directive]` in Claude Code
  2. Skill executes the handoff prompt (defined in skill file)
  3. AI generates continuation document with 8 sections
  4. Document saved to `docs/handoffs/AI_Continuation_Document-DATE-TIME.md`
  5. Context cleared via `/clear`
  6. Resume prompt either copied to clipboard or auto-executed based on handoffMode setting
  7. Fresh AI reads handoff document and continues work

- **Naming conventions or standards in use:**
  - Handoff filenames: `AI_Continuation_Document-DDMMMYYYY-HHMM.md`
  - Section headers: `## Section Name`
  - Confidence flags: ✅ HIGH, ⚠️ MEDIUM, ❓ LOW

- **External dependencies:**
  - None — fully standalone

### 4. RECENT WORK — WHAT JUST HAPPENED (HIGH PRIORITY)

- **What was worked on in this session:**
  - Created complete handoff-prompt skill package
  - Built three Python tools: context_monitor.py, handoff_cli.py, analytics.py
  - Updated skill file to include the full handoff prompt
  - User pointed out the actual handoff prompt was missing — added it to the skill file

- **What decisions were made and WHY:**
  - **Standalone Python scripts**: User chose standalone scripts over pip package. This makes distribution simpler and lowers barrier to use.
  - **docs/handoffs/ directory**: User specified this location for generated documents (keeps them organized).
  - **Configurable handoff mode**: User wanted both clipboard and auto-paste modes with per-invocation override flags.
  - **"handoff-prompt" name**: User chose to match the source methodology name for recognition.
  - **Package for sharing**: User wants to share this with the original creator (dontsleeponai.com), so the package is self-contained with proper attribution.

- **What changed in the system:**
  - Initially created skill documentation but didn't include the actual handoff prompt
  - Added the full handoff prompt after user feedback
  - All Python scripts are executable (chmod +x)

- **What was discussed but NOT yet implemented:**
  - Live testing of the skill in an actual Claude Code environment
  - Any refinements based on real usage

- **Open threads or unresolved questions:**
  - None — skill is complete and ready for testing

### 5. WHAT COULD GO WRONG

- **Known bugs or issues:**
  - `context_monitor.py` estimates token usage from file size since Claude Code doesn't expose exact token counts — this is an approximation
  - Python scripts use only standard library (no rich terminal output) for compatibility

- **Edge cases to watch for:**
  - If `docs/handoffs/` directory doesn't exist, scripts should handle gracefully
  - Context monitor may not find Claude's context files on all systems/versions
  - Handoff documents with very long content may hit filesystem limits

- **Technical debt or shortcuts taken:**
  - Used newline-based screen clearing in context_monitor.py instead of os.system for security reasons
  - Analytics HTML generation is simple (no CSS framework) to keep it standalone

- **Assumptions being made that could be wrong:**
  - Assumed Claude Code stores sessions in ~/.claude/ or ~/Library/Application Support/ — may vary by version
  - Assumed user has Python 3.6+ installed
  - Assumed ~200k token context window for Claude Sonnet 4.6

### 6. HOW TO THINK ABOUT THIS PROJECT

1. **What is the core architectural pattern or design philosophy, and why was it chosen?**
   - **Philosophy**: "Zero dependencies, maximum portability." Everything works as a standalone file or script. No pip install, no npm, no build process. This ensures anyone can use it immediately regardless of their setup.

2. **What is the most common mistake a new person working on this would make?**
   - Trying to modify the handoff prompt structure itself. The 8 sections are carefully designed based on the handoff-prompt methodology. Changing them breaks the continuity contract.
   - Forgetting that the skill file IS the prompt — it's not code that generates prompts, it's a documentation file that Claude reads and executes.

3. **What looks like it should be refactored or redesigned but intentionally should NOT be? Why?**
   - **The handoff prompt text**: It's long and repetitive, but this is intentional. It must be self-contained because each AI session starts fresh. The prompt cannot rely on external context.
   - **Standalone Python scripts**: They could be consolidated into a package with subcommands, but that would require installation. Keeping them separate makes each one drop-in usable.

### 7. DO NOT TOUCH LIST

Explicit rules for the next AI:
- Do NOT modify the 8-section handoff prompt structure without explicit instruction
- Do NOT add external dependencies (Python packages, npm modules, etc.) to any scripts
- Do NOT change the handoff document filename format: `AI_Continuation_Document-DDMMMYYYY-HHMM.md`
- Do NOT remove or change the attribution to dontsleeponai.com
- Do NOT break standalone compatibility — everything must work without installation
- Preserve the `docs/handoffs/` directory structure for generated documents
- Ask before making changes that would require users to reinstall or reconfigure

### 8. CONFIDENCE & FRESHNESS

- **Project Identity**: ✅ HIGH CONFIDENCE — Created this session
- **What Exists Right Now**: ✅ HIGH CONFIDENCE — Created this session
- **Architecture & Technical Map**: ✅ HIGH CONFIDENCE — Created this session
- **Recent Work**: ✅ HIGH CONFIDENCE — This is what we just did
- **What Could Go Wrong**: ⚠️ MEDIUM — Based on analysis, not tested
- **How to Think About This Project**: ✅ HIGH CONFIDENCE — Documented design decisions
- **Do Not Touch List**: ✅ HIGH CONFIDENCE — Explicit constraints
- **Confidence & Freshness**: ✅ HIGH CONFIDENCE — Meta-section
