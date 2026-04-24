# Where the explorer code lives — and where it doesn't

**Q:** Where is the app code for `https://explorer.pwm.platformai.org/`?

**A:** Right here. Three directories under
`pwm-team/infrastructure/agent-web/`:

```
pwm-team/infrastructure/agent-web/
├── frontend/                        Next.js app (app/, lib/, components/)
├── api/                             FastAPI endpoints (main.py, matching.py, demos.py, ...)
├── indexer/                         Python + SQLite event-log indexer
└── deploy/
    ├── Dockerfile.production        multi-stage build bundling all three
    └── nginx/                       reverse-proxy vhost + README
        ├── explorer.pwm.platformai.org.conf
        └── README.md
```

One Docker image (`pwm-explorer:latest`) contains all three services;
only port 3000 is exposed externally.

---

## Q: Should there be a copy of this code under `pwm_product/`?

**No.** The repo separation is:

| Location | Role |
|----------|------|
| `pwm-team/infrastructure/` | **Code** — explorer, contracts, CLI, miner, scoring |
| `pwm-team/pwm_product/` | **Content** — principles, benchmark cards, demos, explainers, reference solvers |

The explorer is *code that displays* pwm_product content. Duplicating
into `pwm_product/` would:

1. **Break the reference-impl / bounty model.** Bounty #2 (80,000 PWM)
   explicitly rewards external developers who build a *competing*
   explorer. If there are two "official" copies, which one do they
   compete against?
2. **Cause drift.** Two copies will diverge silently on every patch.
3. **Multiply the deploy surface.** The Dockerfile, nginx vhost, CI
   pipeline, progress.md signal — all would need a second target.
4. **Lose the git history advantage.** Changes to one wouldn't
   automatically show up in reviews of the other.

---

## Q: Isn't there a note saying "edit `pwm_product/platform/pwm_platform/` for production"?

**Yes — but that note is about a different app.** Two applications are
often confused:

| Application | URL | Code lives at |
|-------------|-----|---------------|
| PWM main platform site | `https://pwm.platformai.org/` | `public/platform/pwm_platform/` (a separate git submodule mounted at `public/`) |
| **PWM explorer (this repo)** | `https://explorer.pwm.platformai.org/` | `pwm-team/infrastructure/agent-web/` |

Different codebases, different repos, different deploys. Don't apply
the auto-memory note about `pwm_product/platform/pwm_platform/` to the
explorer — that rule belongs to the main platform site, not this one.

---

## How the explorer currently gets deployed

- **GCP self-host (canonical):** `https://explorer.pwm.platformai.org/`
  — built locally from this **private** repo with
  `docker build … -t pwm-explorer:latest .`, run behind nginx +
  Let's Encrypt on the same GCP box that hosts `pwm.platformai.org`.
  See `pwm-team/coordination/EXPLORER_HOSTING_OPTIONS.md` Option 3.
  **Only URL to advertise publicly.**

- **Render.com (brittle backup):** `https://pwm-explorer-dsag.onrender.com/`
  — was auto-deploying from the **public** repo's `render.yaml` +
  Dockerfile. On 2026-04-24 the public repo was reverted to exclude
  `pwm-team/` (per the founder-key-safety decision to keep Solidity
  private until mainnet deploy), so Render's next auto-build will
  fail. The currently-running container (built from public
  `b7385c87`) keeps serving until Render gives up on it. **Do not
  advertise this URL.** Disable Render auto-deploy to preserve the
  running container as an ephemeral backup.

Both URLs currently serve the same code, but only the canonical URL
gets new features — it's rebuilt from this private `main` whenever a
new feature lands. Render will stay frozen at the pre-revert commit.

---

## Who should edit what

| I want to change… | Edit… |
|-------------------|-------|
| The home page layout | `pwm-team/infrastructure/agent-web/frontend/app/page.tsx` |
| The matcher scoring | `pwm-team/infrastructure/agent-web/api/matching.py` + `pwm-team/infrastructure/agent-cli/pwm_node/commands/match.py` |
| A benchmark card | DON'T hand-edit — re-run `scripts/generate_benchmark_cards.py`, then edit the `handwritten:` block of the generated YAML |
| A demo dataset | `scripts/generate_demos.py` (re-runs the solvers deterministically) |
| The reference solver | `pwm-team/pwm_product/reference_solvers/{cassi,cacti}/*.py` |
| A target-user explainer | `pwm-team/pwm_product/explainers/{cassi,cacti}.md` |

The rule of thumb: content lives in `pwm_product/`, code lives in
`infrastructure/`. If you're not sure which one you're editing, check
whether your change is "the data PWM shows" (content) or "how PWM shows
it" (code).
