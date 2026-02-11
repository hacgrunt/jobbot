# Crypto PMM Expert Agent — Setup Guide

## How to Set This Up in Claude

### Step 1: Create a New Project
1. Go to claude.ai
2. Click "Projects" in the left sidebar
3. Click "Create Project"
4. Name it something like "Crypto PMM Brain" or "PMM Strategy Partner"

### Step 2: Add the System Prompt
1. Open the project
2. Click "Set custom instructions" (or the gear icon)
3. Copy-paste EVERYTHING from SYSTEM_PROMPT.md (everything below the "---" line) into the Instructions field
4. Save

### Step 3: Upload the Knowledge Base
Upload these files as Project Knowledge:
* 01_PMM_FRAMEWORKS.md — Core frameworks, playbooks, and strategy templates
* 02_CASE_STUDIES.md — Real campaign teardowns and pattern analysis
* 03_ECOSYSTEM_PLAYBOOKS.md — Ecosystem-specific marketing guidance
* 04_METRICS_AND_OPERATIONS.md — Metrics, measurement, team operations
* 05_AI_X_CRYPTO.md — AI x crypto deep dive and market map

### Step 4: Add Your Own Materials (Recommended)
Upload your personal materials to make it even more tailored:
* Your ENS take-home deck (GTM strategy for ENSv2)
* Any positioning docs or messaging frameworks you've built
* Competitive analyses you've done
* Past campaign briefs or launch plans
* Any strategic docs from Rhetor, Vayner3, or other roles (that you're able to share)

### Step 5: Test It
Start a conversation in the project and try prompts like:
* "I'm evaluating a PMM role at [protocol]. Help me build a 90-day plan."
* "How would you position a new restaking protocol against EigenLayer?"
* "Tear apart this messaging — [paste messaging]. What's weak?"
* "I need a launch strategy for an AI agent platform on Solana."
* "What's the best GTM approach for a chain abstraction product?"

## How to Keep It Current
The knowledge base is static — it won't update itself. To keep it sharp:
1. **Monthly:** Add new case studies when you see interesting launches or campaigns
2. **Quarterly:** Update the ecosystem playbooks with new narrative shifts
3. **As needed:** Add competitive intel docs, new framework iterations, conference takeaways
4. **After interviews:** Add learnings and research from companies you evaluate

## What This Agent Is Good At
* Strategic brainstorming on positioning, messaging, GTM
* Competitive analysis and differentiation strategy
* Launch planning and campaign design
* Evaluating PMM approaches and identifying gaps
* Thinking through ecosystem-specific dynamics
* AI x crypto strategy and positioning

## What This Agent Is NOT
* A replacement for real-time market data (pair with Kaito, Dune, CT monitoring)
* A content generation machine (it can help draft, but you provide the voice)
* A substitute for talking to actual users and community members
* Up-to-date on events after its knowledge cutoff (search the web for that)

## Suggested Workflow
1. Use this agent for **STRATEGIC thinking** — positioning, GTM planning, competitive analysis
2. Use regular Claude (with web search) for **CURRENT events** — market moves, competitor launches, news
3. Use Dune/Artemis/DefiLlama for **DATA** — on-chain metrics, TVL, developer activity
4. Use CT/Discord for **SENTIMENT** — community temperature, narrative shifts, cultural moments
