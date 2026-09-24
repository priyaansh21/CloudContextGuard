# CloudContextGuard — Global Pitch Deck

`CloudContextGuard_Global_Pitch.pptx` — a 20-slide, cinematically designed pitch
deck built for a global tech-competition audience. It is generated entirely
from the project's own source, docs, and screenshots — nothing in it is
invented.

## Design rationale

The deck deliberately avoids generic "startup pitch" or Canva-template
aesthetics in favor of a dark, cybersecurity-product visual language:
near-black navy backgrounds, glassmorphism panels, HUD-style corner brackets,
and a restrained accent palette (cyan = pass/neutral, green = allow, red =
deny/fail, amber = warning/medium-risk, violet = secondary emphasis). Every
slide carries a persistent footer (product wordmark + slide index) and a
kicker label naming the narrative beat, so the deck reads as one continuous
system rather than a stack of disconnected slides.

Architecture and data-flow diagrams (engine gates, decision funnel, database
schema groupings, threat matrix) are drawn natively with PowerPoint shapes in
the deck's own visual language rather than embedding the existing light-theme
PNGs from `docs/final/assets/diagrams/`. Evidence slides instead embed real
product screenshots from `docs/final/assets/screenshots/`, framed with a
colored border that matches that slide's outcome (red border = a DENY
response, green border = an ALLOW response, cyan = neutral/admin action).

## Slide list

| # | Kicker | Title |
|---|---|---|
| 1 | Hook | CLOUDCONTEXTGUARD |
| 2 | The Problem | A single valid permission is treated as proof enough. |
| 3 | The Question | Can authorization depend on more than identity? |
| 4 | The Solution | How five independent checks converge on one decision |
| 5 | System Architecture | How a request actually moves through the system |
| 6 | The Authorization Pipeline | One request. Six independent gates. |
| 7 | The Risk Engine | A transparent, deterministic risk score |
| 8 | The Central Demonstration | "Valid IAM permission." → the Topic 19 climax (IAM PASS / VPC FAIL / DENY) |
| 9 | Why This Matters | Two ways to answer "should this be allowed?" |
| 10 | Attack Simulator | Six real scenarios. Zero mocked results. |
| 11 | Dynamic Policy, Live | The same request. A policy changed underneath it. |
| 12 | Policy Restoration | The boundary returns the moment it's restored |
| 13 | Security Hardening | What was independently verified |
| 14 | The Live Console | Nine screens. One decision engine underneath. |
| 15 | Data Model | One schema, three purposes |
| 16 | Verified, Not Claimed | Every number here is reproducible |
| 17 | Threat Model | Seven documented threats. Seven verified outcomes. |
| 18 | Engineering Boundaries | What this is not |
| 19 | Roadmap | From simulation to production |
| 20 | Final Takeaway | "IAM tells us who can access. Context tells us whether they should." |

Every slide states, and slide 18 states explicitly and at length, that this
is a **local simulation / academic prototype** with no real AWS account, no
real credentials, and no production deployment — consistent with
`PROJECT_DOCUMENTATION.md` Section 28.

## Screenshots and diagrams used

All 16 screenshots in `docs/final/assets/screenshots/` are used across
slides 2, 8, 10, 11, 12, and the slide 14 dashboard mosaic (9 tiles). No
screenshot was cropped in a way that alters its content, and no screenshot
was staged or fabricated — every one is an actual response from the running
local API/UI, as documented in `docs/research/RESULTS.md`.

Diagrams (engine pipeline, decision funnel, risk bands, schema groups,
threat matrix, roadmap timeline) are original vector shapes built with
`python-pptx`, redrawn from the structure described in
`PROJECT_DOCUMENTATION.md` and `THREAT_MODEL.md` — not embeddings of the
existing docs diagrams, which use a light theme inconsistent with this deck.

## Animation and transition strategy

Every slide has a **Fade Smoothly** transition by default. Slides 7, 8, and
12 use a **Morph** transition instead, to create visual continuity across the
three most important narrative chains:

- 6 → 7 → 8: the authorization pipeline morphs into the risk engine, which
  morphs into the Topic 19 climax — one continuous evaluation, not three
  separate topics.
- 11 → 12: the live policy edit morphs into its restoration, reinforcing
  that it's the same mechanism running in both directions.

Entrance animations (fade/wipe, sequential reveals) were added to slides 1,
4, 6, 7, 8, 11, and 12 — the slides the brief called out for choreography.
The most important beat is on **slide 8** (the Topic 19 climax): the IAM
PASS row and the VPC/Network FAIL row are each bound to
`msoAnimTriggerOnPageClick` rather than a fixed delay, so the presenter
controls exactly how long the pause between them lasts — a deliberate,
presenter-paced dramatic beat rather than a hardcoded wait. The MFA/RISK
rows and evidence screenshot then auto-follow, and the final DENY banner is
also click-gated so the presenter can hold on it.

Remaining slides carry only the global fade transition, since the brief
scoped detailed choreography to slides 1, 6, 7, 8, and 11–12.

### How the animations were built

Static content is generated by `build_deck.py` (python-pptx), which has no
animation API. While building each slide, the script also records an
animation manifest (`anim_manifest.json`) capturing the real python-pptx
shape objects for each animated group, translated to 1-based COM shape
indices via `theme.sidx()`. A separate COM script, `add_animations.py`,
opens the saved `.pptx` in installed PowerPoint, applies the transitions,
and replays the manifest through
`Slide.TimeLine.MainSequence.AddEffect(...)` to add native, editable
PowerPoint animations — the same objects you'd see in the Animation Pane if
you opened the file and pressed Alt+F9 equivalent (Animations tab).

**Known tooling limitation**: the deck's static PNG-based visual QC
(`render.py`, used throughout this build to catch layout bugs) exports only
each slide's final resting state — it cannot show transitions or entrance
animations in motion. Their correctness was therefore verified
structurally (effect counts, shape indices, and trigger types read back via
COM after saving — see the verification step below) rather than visually.
If anything looks off in Slide Show mode, the fix is in `add_animations.py`,
not in `build_deck.py`.

## Rebuilding the deck

```
python build_deck.py       # regenerates the .pptx content + anim_manifest.json
python add_animations.py   # applies transitions + entrance animations via COM
python render.py           # (optional) exports all 20 slides to PNG for visual QC
```

`render.py` and `add_animations.py` both require PowerPoint installed
locally (they drive it via `pywin32`/COM) and will briefly open a visible
PowerPoint window.

## Presenting

- Total slides: 20. At roughly 30–60s of speaker notes per slide (every
  slide has notes; slide 8 carries the longest, ~45–60s), the deck runs
  approximately 12–15 minutes at a natural pace, plus Q&A.
- Speaker notes are embedded on every slide (View → Notes Page, or Presenter
  View) and include an explicit transition line into the next slide.
- Slides 8, 11, and 12 use click-to-advance animation steps — use the
  spacebar/click to pace those three slides deliberately rather than
  auto-advancing.

## Fact-checking

Every metric, scenario, and claim in the deck traces to a specific project
source:
- Test counts (82/82, 17/17 portability) — `docs/research/RESULTS.md`.
- The Topic 19 scenario (IAM PASS / VPC FAIL / MFA FAIL / Risk 100 CRITICAL
  / DENY) and the dynamic-policy scenario (Risk 40 MEDIUM / ALLOW) —
  `docs/research/RESULTS.md` and `docs/final/DYNAMIC_POLICY_EVALUATION.md`.
- The seven threats (T1–T7) and T7's WARNING-not-DENY behavior —
  `THREAT_MODEL.md`.
- Limitations and future-improvement lists — `PROJECT_DOCUMENTATION.md`
  Sections 28 and 29.
- The GitHub repository URL on the closing slide was confirmed via
  `git remote -v` against the real project repository, not guessed.

No AWS integration, production deployment, or real-world incident is
claimed anywhere in the deck.
