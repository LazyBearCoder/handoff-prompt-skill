# handoff-prompt

Create a structured AI continuation document before clearing context, enabling seamless handoff to a fresh AI instance.

**Source:** Based on the handoff-prompt methodology from [dontsleeponai.com/handoff-prompt](https://www.dontsleeponai.com/handoff-prompt)

## When to Use

Use this skill when:
- Your AI context window is getting heavy (approaching 80% capacity)
- You've completed a major feature or architectural decision
- You want to preserve project state, decisions, and reasoning before clearing context
- You need to hand off work to a fresh AI instance

## How to Use

### Basic Usage

```
/handoff
```

Generates a continuation document with no specific next task directive. The fresh AI will ask what to work on next.

### With Directive

```
/handoff continue testing the billing system
```

Generates a continuation document with a specific next task directive.

### Mode Override Flags

```
/handoff --clipboard    # Force clipboard mode (copy resume prompt to clipboard)
/handoff --auto         # Force auto-paste mode (automatically execute resume prompt)
```

## Configuration

Add these settings to your Claude Code `settings.json`:

```json
{
  "continuationMethod": "ask",     // "compact", "handoff", or "ask" (default)
  "handoffMode": "clipboard"       // "clipboard" (default) or "auto-paste"
}
```

### continuationMethod

Controls which method to use when clearing context:

| Value | Behavior |
|-------|----------|
| `"ask"` (default) | Ask the user once which method they prefer, then remember their choice |
| `"compact"` | Always use Claude Code's built-in `/compact` |
| `"handoff"` | Always use the handoff-prompt skill |

**First-time experience:** When set to `"ask"` (or unset), the skill will ask the user to choose between Compact and Handoff the first time context is cleared. Their choice is saved to settings.json for future sessions.

### handoffMode

Controls how the resume prompt is delivered after handoff:

| Value | Behavior |
|-------|----------|
| `"clipboard"` (default) | Resume prompt is copied to clipboard. You paste it manually. |
| `"auto-paste"` | Resume prompt is automatically executed. |

## What the Skill Does

1. **Checks user preference** for Compact vs Handoff (asks once if not set)
2. **If Handoff is chosen:**
   - Analyzes current conversation to extract project state, recent work, and decisions
   - Generates continuation document with 8 structured sections
   - Saves document to `docs/handoffs/AI_Continuation_Document-DATE-TIME.md`
   - Clears context automatically via `/clear`
   - Handles resume prompt based on `handoffMode` setting
3. **If Compact is chosen:**
   - Delegates to Claude Code's built-in `/compact` command

---

# FIRST-TIME SETUP PROMPT

When this skill is invoked and `continuationMethod` is not set (or is `"ask"`), ask the user:

---
You're about to clear your context. Which method would you like to use?

**Compact** — Claude Code's built-in context summarization. Faster, less detailed, good for quick context reduction.

**Handoff** — Generates a structured 8-section continuation document with decision reasoning, architecture details, and a resume prompt. Better for complex projects and long-term work.

Your choice will be remembered for future sessions. You can change it anytime in settings.json with `continuationMethod`.

Which would you prefer: [Compact] or [Handoff]?
---

After the user responds, update their settings.json:

```json
{
  "continuationMethod": "handoff"  // or "compact"
}
```

Then proceed with the chosen method.

---

# THE HANDOFF PROMPT

When handoff is selected, execute the following prompt to generate the continuation document and resume prompt:

---

Generate an AI Project Continuation Document and a Resume Prompt.

PURPOSE:
You are creating a handoff package so a fresh AI instance with zero prior context
can resume this project exactly where we are leaving off — with no guessing,
no hallucinating, and no re-discovery.

Write this as if briefing a senior technical colleague who is sharp but has
never seen this project before. Be precise. Be concise. Preserve reasoning.
Skip filler.

---

STEP 1: Generate the Continuation Document using this structure.

Save or present it as: AI_Continuation_Document-[DDMMMYYYY]-[HHMM].md (e.g. AI_Continuation_Document-17Feb2026-1430.md)

---

# PROJECT CONTINUATION DOCUMENT
## Session [number] — [today's date]

### 1. PROJECT IDENTITY

- **Project Name:**
- **What This Project Is:** (1–2 sentences. What it does, who it's for.)
- **Primary Objective:** (The measurable goal.)
- **Strategic Intent:** (Why this project exists. What long-term outcome it serves.)
- **Hard Constraints:** (Non-negotiable rules, platform limitations, design decisions that must not change.)

### 2. WHAT EXISTS RIGHT NOW

Describe the current state of the system honestly.

- **What is built and working:**
- **What is partially built:**
- **What is broken or blocked:**
- **What has NOT been started yet:**

### 3. ARCHITECTURE & TECHNICAL MAP

- **Tech stack / tools / platforms:**
- **Key data structures, tables, files, or repos:**
- **How the system works end-to-end:** (Describe the core logic flow in numbered steps.)
- **Naming conventions or standards in use:**
- **External dependencies:** (APIs, services, integrations)

### 4. RECENT WORK — WHAT JUST HAPPENED (HIGH PRIORITY)

This section matters more than anything above it for continuation purposes.
Be detailed. Be specific.

- **What was worked on in this session:**
- **What decisions were made and WHY:**
  (Include the reasoning and tradeoffs. This prevents the next AI from undoing your work.)
- **What changed in the system:**
- **What was discussed but NOT yet implemented:**
- **Open threads or unresolved questions:**

### 5. WHAT COULD GO WRONG

- **Known bugs or issues:**
- **Edge cases to watch for:**
- **Technical debt or shortcuts taken:**
- **Assumptions being made that could be wrong:**
  (Flag anything the next AI might incorrectly assume about the system.)

### 6. HOW TO THINK ABOUT THIS PROJECT

Answer these three questions:
1. What is the core architectural pattern or design philosophy, and why was it chosen?
2. What is the most common mistake a new person working on this would make?
3. What looks like it should be refactored or redesigned but intentionally should NOT be? Why?

### 7. DO NOT TOUCH LIST

Explicit rules for the next AI:
- Do NOT refactor stable, working systems without being asked.
- Do NOT redesign architecture unless explicitly instructed.
- Preserve existing naming conventions.
- Maintain previously chosen tradeoffs — they were chosen for reasons documented above.
- Ask before introducing new frameworks, libraries, or dependencies.
- [Add any project-specific constraints here.]

### 8. CONFIDENCE & FRESHNESS

For each major section above, flag:
- ✅ HIGH CONFIDENCE — verified or built this session
- ⚠️ MEDIUM — carried forward from earlier, not re-verified
- ❓ LOW — assumed or inferred, should be validated

---

STEP 2: Generate the Resume Prompt.

After the Continuation Document, generate a single copy-pasteable Resume Prompt
inside a code block.

The Resume Prompt must work as a standalone message in a brand new conversation.
It should instruct the next AI to:

1. Read the attached AI_Continuation_Document-[DDMMMYYYY]-[HHMM].md in full before doing anything.
2. Check for a USER DIRECTIVE below.
3. Summarize its understanding of the current project state in 3–5 sentences.
4. Confirm the next action it will take.
5. Ask clarification questions ONLY if something blocks execution.
6. Then begin working.

The Resume Prompt must include this section at the end:

---
USER DIRECTIVE (fill in or leave blank):

[Write your specific instruction here if you want the AI to do something specific next.
If left blank, the AI should analyze the project state, propose the most strategic
next action with brief reasoning, and wait for confirmation before proceeding.]
---

The Resume Prompt must be fully self-contained. Do not add any commentary
outside of the Continuation Document and the Resume Prompt.

---

# END OF HANDOFF PROMPT

After generating both the Continuation Document and Resume Prompt above:

1. Save the Continuation Document to: `docs/handoffs/AI_Continuation_Document-[DDMMMYYYY]-[HHMM].md`
2. Check the user's `handoffMode` setting:
   - If "clipboard": Copy the Resume Prompt to clipboard and notify the user
   - If "auto-paste": Execute `/clear`, then output the Resume Prompt
3. If user provided a directive (e.g., `/handoff continue testing`), insert it into the USER DIRECTIVE section

## Resume Prompt Behavior

When the fresh AI reads the continuation document via the resume prompt:

- It confirms understanding of the project state
- It acknowledges the "Do Not Touch" list
- It asks: "What would you like me to work on next?"

If you provided a directive in `/handoff [directive]`, that directive is included in the resume prompt.

## Why This Works

Unlike generic summaries that treat all information equally, this handoff approach:

- **Recency weighting**: What you did in the last 30 minutes matters more than what you did 3 hours ago
- **Reasoning preservation**: Captures WHY you made decisions, not just WHAT you built
- **Regression protection**: Explicit "Do Not Touch" list prevents undoing working code
- **Confidence flags**: The next AI knows what to trust vs. what to verify

## Compact vs Handoff

| Feature | Compact | Handoff |
|---------|---------|---------|
| **Speed** | Fast | Slower (more detailed) |
| **Detail level** | Summary | 8-section structured document |
| **Decision reasoning** | Brief | Preserves WHY decisions were made |
| **Architecture** | Basic | Full technical map |
| **Regression protection** | No | Explicit "Do Not Touch" list |
| **Confidence flags** | No | Yes — shows what to trust |
| **Best for** | Quick sessions, simple projects | Complex projects, long-term work |

## Version

1.1.0 — Added continuationMethod setting with first-time user preference prompt

## Credits

Methodology and prompt structure by [Don't Sleep On AI](https://www.dontsleeponai.com/handoff-prompt)

Packaged as a Claude Code skill for easy context continuation.
