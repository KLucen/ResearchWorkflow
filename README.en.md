# ResearchWorkflow

**A workflow that lets an AI agent deep-read papers for you — without ever concluding on your behalf.**

Keep literature in Zotero, notes in Obsidian. The agent turns papers into structured reading guides
and evidence notes. You only do the highlighting and answer the questions it asks you.

[中文 README](README.md) · [15-minute quickstart](docs/02-quickstart.md) · [Design rationale](docs/01-design.md) · [FAQ](docs/07-faq.md)

> The user-facing documentation is written in Chinese. This file is the English entry point;
> the workflow itself is language-agnostic (see [`template/00_System/Config.md`](template/00_System/Config.md)).

---

## The problem it solves

Ask an LLM to read papers and you usually get one of three bad outcomes:

| Bad outcome | What it looks like | This workflow's answer |
|---|---|---|
| **It concludes for you** | You can't tell which sentence came from the paper and which the model invented — so you don't dare cite your own notes | **Three-layer evidence discipline**: paper verbatim / agent inference (explicitly marked provisional) / your own response — physically separated |
| **It misses your point** | A fluent summary of everything you didn't care about | **Five-color annotation channel**: you just highlight in Zotero; the color carries the semantics, and the agent routes accordingly |
| **Knowledge doesn't accumulate** | Fifty papers later your head is still a pile of sand; every question means re-reading | **Claim ledger**: cross-paper claims with stable IDs, evidence backlinks, and state transitions — queryable and refutable |

In one line:

> **The agent does not judge. The agent structures and retrieves. Judgment stays in your highlights.**

---

## How it runs

```
                    ┌─────────────────────────────────────────┐
                    │  Zotero (immutable source of truth)     │
                    │  PDFs · bibliographic data · highlights │
                    └────────────────┬────────────────────────┘
                                     │  read-only
                        ┌────────────▼────────────┐
                        │  rvzotero.py            │  ← replaces Zotero plugins
                        │  Local API access layer │     stdlib-only, any agent can call
                        └────────────┬────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
   ┌────▼─────┐              ┌───────▼────────┐          ┌────────▼────────┐
   │  ingest  │              │     query      │          │      lint       │
   │ paper →  │              │ answer research│          │ consistency &   │
   │ notes    │              │ questions      │          │ broken links    │
   └────┬─────┘              └───────┬────────┘          └────────┬────────┘
        │                            │                            │
        └────────────────────────────┼────────────────────────────┘
                                     │  write
                    ┌────────────────▼────────────────────────┐
                    │  Obsidian vault                         │
                    │  pass1/ reading guides (not evidence)   │
                    │  pass2/ deep-read notes (evidence layer)│
                    │  02_Wiki/ persistent knowledge (claims) │
                    │  03_Vocabulary/ vocabulary (language)   │
                    └─────────────────────────────────────────┘
```

### Two load-bearing ideas

**1. Guide first, notes second — a two-step ingest**

When a new paper arrives, the agent produces **only a five-minute reading guide** — one page,
~1000 characters: what problem it attacks, a chapter map, what the authors *claim*, what you need
to know beforehand, and which questions to hold in mind.

Then you read the paper and highlight. **Only after your annotations exist** does the agent write
the second file, the deep-read note. Passages influenced by your highlights are wrapped in
`==highlight==` so you can see at a glance what your own reading brought out.

Why bother? Because **a "summary" produced before you annotated anything is an unconfirmed object
that nonetheless looks like evidence**. That is the most dangerous failure mode.

**2. Five-color annotation — telling the agent what you're thinking**

| Color | Meaning | Destination |
|---|---|---|
| 🟡 Yellow | Unknown word | Vocabulary, never the knowledge layer |
| 🟢 Green | Term definition / explanation | Concept page |
| 🔵 Blue | Impact, opinion, solution | Claim ledger (recorded as supporting) |
| 🔴 Red | Flaw, open problem, challenge | Counter-evidence, conflicts, research gaps |
| 🟣 Purple | Relevance to my own research | How much this paper matters to *you* |

Purple is the one signal the agent cannot infer from the text — only you know it.

> **A pitfall we hit in practice**: if you read with a translation plugin, annotation comments end up
> containing both `🔤machine translation🔤` and *your own written words*. This workflow splits by the
> `🔤…🔤` **span**: inside the span is a machine dictionary entry (never quotable as paper text);
> outside it is what you said. Judging by "does the whole comment contain 🔤" throws your own words away.

---

## Using it

### What you need

- **Obsidian** (free) — for notes
- **Zotero** (free) — for literature and annotations
- **Python 3.8+** — standard library only, no `pip install` needed
- **Any agent that can read files and run commands** — Claude Code, Cursor, Codex, DSH, or your own

### Five steps

```bash
# 1. Get the repo
git clone https://github.com/KLucen/ResearchWorkflow.git
cd ResearchWorkflow

# 2. Copy the blank vault skeleton
cp -r template/ ~/MyResearchVault

# 3. Zotero → Settings → Advanced → enable "Allow other applications on this computer"

# 4. Verify the agent can reach your Zotero
python tools/zotero/rvzotero.py ping
# → {"ok": true, "library": "users/0", ...}   "ok" means you're good

# 5. Point your agent at it
#    Hand it agent/AGENTS.md, then say:
#    "Read agent/AGENTS.md and <VAULT>/00_System/Config.md, then ingest the first
#     paper in my Zotero collection <name>"
```

**Don't skip filling in `<VAULT>/00_System/Config.md`** — it is the configuration source of truth
and the agent reads it before every task.

Full version: [docs/02-quickstart.md](docs/02-quickstart.md)

### The daily loop

```
                  ┌──────────────────────────────────────────┐
                  │                                          │
   ① drop paper   ② agent writes      ③ you read + highlight
   into Zotero ──→ a guide in     ──→  (in Zotero, not Obsidian)
                   pass1/待精读/
                                             │
                                             ▼
   ⑥ answer its    ←──  ⑤ agent writes  ←──  ④ tell the agent
   questions            the deep-read        "I've read it"
        │               note (pass2/)
        │
        └──→ ⑦ every few papers, have the agent update the 02_Wiki/ claim ledger
                (requires your approval)
```

Inputs, outputs, and human checkpoints for each step: [docs/03-workflow.md](docs/03-workflow.md)

---

## Repository layout

```
ResearchWorkflow/
├─ README.md              You are here (Chinese)
├─ README.en.md           English
├─ docs/                  Human-readable documentation
│   ├─ 01-design.md           Why it's designed this way
│   ├─ 02-quickstart.md       15-minute setup
│   ├─ 03-workflow.md         ingest / query / lint in full
│   ├─ 04-schemas.md          Field reference
│   ├─ 05-zotero-access.md    Zotero access layer & troubleshooting
│   ├─ 06-agent-integration.md Wiring up your own agent
│   └─ 07-faq.md              FAQ
├─ template/              ★ Copy this → your vault
│   ├─ 00_System/             Agent constitution, config, schemas, dashboards
│   ├─ 01_Papers/             Guides + deep-read notes
│   ├─ 02_Wiki/               Persistent knowledge
│   └─ 03_Vocabulary/         Vocabulary
├─ tools/zotero/          ★ Portable Zotero access layer (replaces plugins)
│   ├─ rvzotero.py            Stdlib-only CLI
│   ├─ README.md              Command reference
│   └─ tests/                 Offline unit tests + mock server
└─ agent/                 ★ Let any agent plug in
    ├─ AGENTS.md              Universal integration contract
    ├─ skills/                Two installable skills
    └─ adapters/              Per-harness setup instructions
```

---

## About the Zotero access layer

**No Zotero plugin required.** This repo ships `tools/zotero/rvzotero.py`, which talks straight to
Zotero's Local API using nothing but the Python standard library:

```bash
python tools/zotero/rvzotero.py ping                            # health check
python tools/zotero/rvzotero.py collections                     # list collections
python tools/zotero/rvzotero.py search --query "diffusion" --limit 5
python tools/zotero/rvzotero.py annotations --key <item-key>    # read five-color annotations (full by default)
python tools/zotero/rvzotero.py retrieve --key <item-key> --query "evaluation"  # full-text search
python tools/zotero/rvzotero.py attachment --key <item-key>     # resolve the PDF path on disk
```

It ships fixes for several pitfalls we actually hit — pitfalls that fail *silently* if unhandled:

- `/children` **returns zero annotations when called without parameters** (no error) — the worst one;
  you conclude the paper has no annotations at all
- List endpoints are **silently truncated at 100** — the client must page through using the
  `Total-Results` header
- The `page` parameter of `fulltext?page=N` is **ignored outright by Zotero** — you always get the whole
  document back; the tool slices locally and labels the resulting page numbers as *estimated*
- A paper often has several PDF attachments, and **annotations live on only one of them**
- Zotero's Local API answers **HTTP/1.0**, so PowerShell's `Invoke-RestMethod` on Windows fails to
  complete the handshake

One principle runs through the whole layer: **whenever what comes back is less than what exists, say so.**
Every truncation, estimate or degradation therefore shows up in the output as a `truncated` / `note`
field — never silently.

Command reference: [tools/zotero/README.md](tools/zotero/README.md)
Rationale and troubleshooting: [docs/05-zotero-access.md](docs/05-zotero-access.md)

---

## Supported agents

This workflow is **not bound to any agent implementation**. It needs exactly three capabilities:
read files, write files, run commands.

| Harness | Integration | Notes |
|---|---|---|
| **Claude Code** | `CLAUDE.md` + `.claude/skills/` | [adapter](agent/adapters/claude-code.md) |
| **Cursor** | `.cursor/rules/*.mdc` | [adapter](agent/adapters/cursor.md) |
| **Codex** | repo-root `AGENTS.md` | [adapter](agent/adapters/codex.md) |
| **DSH** | `~/.dsh/skills/<name>/SKILL.md` | [adapter](agent/adapters/dsh.md) (includes plugin-replacement table) |
| **Other / custom** | paste the contract into your system prompt | [adapter](agent/adapters/generic.md) |

The single entry point is [agent/AGENTS.md](agent/AGENTS.md) — whatever agent you use, have it read that first.

---

## What this does and doesn't do

**It will not**:

- ❌ Judge whether a paper is good or worth following
- ❌ Produce "conclusions" before you have annotated anything
- ❌ Treat machine translation as paper text
- ❌ Promote a judgment into a persistent Wiki claim without your approval
- ❌ Write anything to your Zotero (the entire access layer is read-only)

**It needs you to**:

- ✅ Actually highlight in Zotero (that's the only signal input)
- ✅ Answer the agent's questions (it will leave `PENDING_RESEARCHER_RESPONSE` rather than answer for you)
- ✅ Approve or reject Wiki changes

---

## License

[MIT](LICENSE)
