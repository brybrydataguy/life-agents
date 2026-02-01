# CLAUDE.md - Weekly Journal Review System

## Purpose
Generate weekly reflection reviews that synthesize daily journals, track alignment with goals, and provide actionable guidance.

## Trigger Command
When the user asks for a "weekly review" or "journal review", execute the full review process below.

---

## Review Process

### Step 1: Gather Context
Read ALL of the following files before generating the review:

**Daily Journals** (last 14 days):
- `journals/daily/YYYY-MM-DD.md` — Read all entries from the past 2 weeks

**Previous Weekly Reviews**:
- `journals/weekly/claude-*.md` — Read ALL previous Claude-generated reviews to track patterns over time

**Context Files** (always read all):
- `context/goals/2026.md` — Current year goals and processes
- `context/goals/life.md` — Life purpose and values
- `context/state/life-areas.yaml` — Current status of each life area
- `context/state/open-loops.md` — Pending actions and unresolved items
- `context/history/decisions.md` — Past decisions for context

### Step 2: Analyze
Identify:
- **Themes**: What topics/concerns appeared repeatedly?
- **Emotional patterns**: Track mood survey data across entries
- **Energy patterns**: Wired/Tired/Comfortable trends
- **Alignment gaps**: Where actual focus diverged from stated goals
- **Progress signals**: Evidence of movement on goals
- **Warning signs**: Stress, burnout, neglected areas, or concerning patterns

### Step 3: Generate Review
Output to: `journals/weekly/claude-YYYY-MM-DD.md` (using current date)

---

## Output Format

```markdown
# Weekly Review: [DATE RANGE]
Generated: YYYY-MM-DD

## 🧠 What's Been On Your Mind
[2-3 paragraph narrative synthesis of the dominant themes, concerns, and preoccupations from the daily journals. Be specific—reference actual events, decisions, and reflections.]

## 🎯 Focus Analysis

### Intended Focus (from goals)
[Bullet list of where you said you wanted to focus based on 2026.md]

### Actual Focus (from journals)
[Bullet list of where time/energy actually went based on journal content]

### Alignment Assessment
[Brief analysis of the gap between intended and actual. No judgment—just clarity.]

## 📊 Scorecard

| Life Area | Goal Status | This Week | Trend | Notes |
|-----------|-------------|-----------|-------|-------|
| Health & Energy | [from 2026.md] | [0-10] | ↑↓→ | [specific observation] |
| Fitness | [from 2026.md] | [0-10] | ↑↓→ | [specific observation] |
| Connection | [from 2026.md] | [0-10] | ↑↓→ | [specific observation] |
| Career (Shopify) | [from 2026.md] | [0-10] | ↑↓→ | [specific observation] |
| Side Business | [from 2026.md] | [0-10] | ↑↓→ | [specific observation] |
| Family | [from life-areas.yaml] | [0-10] | ↑↓→ | [specific observation] |
| Investments | [from life-areas.yaml] | [0-10] | ↑↓→ | [specific observation] |

**Overall Week Score: X/10**

### Scoring Rubric
- **8-10**: Strong progress, aligned with goals, positive momentum
- **5-7**: Some progress, minor drift, sustainable pace
- **3-4**: Limited progress, significant drift, needs attention
- **1-2**: Stalled or regressing, intervention needed

## 😊 Mood & Energy Summary
[Summary of mood survey data with any notable patterns. Reference specific days if relevant.]

## 🔄 Open Loops Status
[Review open-loops.md and note any that were mentioned in journals, any progress, or any that need escalation]

## 💡 Recommendations

### Actions to Take
[Specific, actionable items based on journal content and goal gaps. Be concrete.]

### Focus Shifts
[Suggest where to redirect attention if current allocation isn't serving goals]

### Rest & Recovery
[If burnout signals detected, prescribe specific recovery actions. If energy is good, acknowledge it.]

### Questions to Reflect On
[2-3 questions that emerged from the review that might be worth journaling about]

## 📈 Patterns Across Reviews
[If previous claude-*.md reviews exist, note any multi-week patterns: recurring themes, persistent gaps, improving areas, or chronic issues]

---
*This review synthesizes journals from [DATE] to [DATE] against goals in context/goals/2026.md*
```

---

## Scoring Guidelines

Score each area based on evidence in the journals:

**Health & Energy**: Sleep quality, energy levels, creatine consistency, coffee timing, meditation practice

**Fitness**: Exercise frequency, skill progression (pull-ups, pistol squats, handstand work), injury recovery progress

**Connection**: Quality time with Behshad and Aydin, physical affection, friend interactions, colleague relationships, loving-kindness practice

**Career**: Impact of work delivered, relationship building at Shopify, clarity of priorities, energy/mood about work

**Side Business**: Any progress on packaging knowledge, content creation, or business development

**Family**: Aydin-specific time, Behshad-specific time, family events, guardian/trust responsibilities

**Investments**: Portfolio review activity, research conducted, decision quality, alignment with strategy

---

## Tone Guidelines
- Be direct and honest, not artificially positive
- Celebrate genuine wins
- Name concerns clearly without catastrophizing
- Recommendations should be specific and actionable, not generic advice
- Reference actual journal content to ground observations
- If data is missing (e.g., no mood surveys), note it and suggest capturing it

---

## Example Trigger Prompts
- "Run my weekly review"
- "Do a journal review for the past two weeks"
- "Weekly reflection time"
- "Review my journals and give me feedback"
