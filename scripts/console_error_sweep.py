"""Headless Playwright console-error sweep for Step 4 Criterion 7.

Per `pwm-team/coordination/MAINNET_DEPLOY_UNBLOCK_STEPS_3_TO_7_2026-04-28.md`
§ "Criterion 7 — no JavaScript console errors (Director, in Chrome)".

Loads each of 6 explorer routes in headless Chromium (desktop + mobile
emulation), captures every `page.on("console")` and `page.on("pageerror")`
event, and writes per-route JSON + a Markdown summary. Replaces the manual
"open Chrome 6 times, click around" Director task (D6 in
MAINNET_BLOCKERS_2026-04-30.md) with a CI-runnable script.

Per-route checks:
1. Load the page; wait for `networkidle`.
2. Scroll the full height (triggers lazy-load handlers).
3. Click obvious interactive elements (search inputs, tab triggers,
   nav links — see `INTERACTIONS` table below; per-route safe-click set).
4. Wait 2 seconds for delayed errors.
5. Capture all console.error / page.on("pageerror") events.

Result schema (one JSON file per route per form-factor):

    {
      "url": "https://explorer.pwm.platformai.org/",
      "route": "/",
      "form_factor": "desktop",
      "console_errors": [...],
      "page_errors": [...],
      "console_warnings": [...],
      "interactions_attempted": [...],
      "interactions_failed": [...],
      "screenshot_b64": "<truncated>",
      "duration_ms": 4521,
      "pass": true
    }

Exit codes:
    0  zero console errors AND zero pageerror events on all routes
    1  one or more routes have errors
    2  Playwright not installed (run `pip install playwright && playwright install chromium`)
    3  network / setup error

Usage:

    # Default: canonical explorer URL, both desktop + mobile sweeps
    python3 scripts/console_error_sweep.py

    # Custom URL
    python3 scripts/console_error_sweep.py https://staging.explorer.pwm.platformai.org

    # Desktop only (skip mobile emulation pass)
    python3 scripts/console_error_sweep.py --form-factor desktop

    # Skip interactions (just load + capture; faster ~30 s)
    python3 scripts/console_error_sweep.py --no-interactions

    # Strict mode: also fail on console.warn (default treats warn as soft)
    python3 scripts/console_error_sweep.py --strict-warn

Outputs to:
    pwm-team/coordination/evidence/step4_console/<DATE>/
        sweep_<route>_<form>.json
        sweep_<route>_<form>.png
    pwm-team/coordination/evidence/step4_console/<DATE>/summary.md
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("console_error_sweep")


ROUTES = ["/", "/match", "/demos", "/contribute", "/use", "/roadmap"]

# Per-route safe interactions — selectors to click + text-input values.
# Designed to be tolerant: missing selectors are recorded but don't fail.
INTERACTIONS = {
    "/": [
        {"type": "click_if_present", "selector": "nav a:first-child"},
        {"type": "click_if_present", "selector": "[data-testid='hero-cta']"},
    ],
    "/match": [
        {"type": "fill_if_present", "selector": "input[type='search']", "value": "hyperspectral imaging"},
        {"type": "click_if_present", "selector": "button[type='submit']"},
        {"type": "click_if_present", "selector": "select"},
    ],
    "/demos": [
        {"type": "click_if_present", "selector": "[data-testid='cassi-demo']"},
        {"type": "click_if_present", "selector": "[data-testid='cacti-demo']"},
        {"type": "click_if_present", "selector": "button:has-text('View')"},
    ],
    "/contribute": [
        {"type": "click_if_present", "selector": "input[type='text']:first-of-type"},
        {"type": "click_if_present", "selector": "select:first-of-type"},
    ],
    "/use": [
        {"type": "click_if_present", "selector": "code:first-of-type"},
        {"type": "click_if_present", "selector": "[data-testid='copy-button']"},
    ],
    "/roadmap": [
        {"type": "click_if_present", "selector": "a[href^='#']:first-of-type"},
    ],
}


def _form_factor_args(ff: str) -> dict:
    if ff == "mobile":
        return {
            "viewport": {"width": 412, "height": 915},
            "user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
            "device_scale_factor": 2.625,
            "is_mobile": True,
            "has_touch": True,
        }
    return {
        "viewport": {"width": 1280, "height": 800},
        "is_mobile": False,
        "has_touch": False,
    }


async def sweep_route(
    context, base_url: str, route: str, form_factor: str,
    do_interactions: bool, strict_warn: bool, out_dir: Path,
) -> dict:
    full_url = base_url.rstrip("/") + route
    page = await context.new_page()

    console_errors = []
    console_warnings = []
    page_errors = []

    def _on_console(msg):
        try:
            level = msg.type
            text = msg.text
            entry = {"level": level, "text": text}
            if level == "error":
                console_errors.append(entry)
            elif level == "warning":
                console_warnings.append(entry)
        except Exception:
            pass

    def _on_pageerror(err):
        try:
            page_errors.append({"text": str(err)})
        except Exception:
            pass

    page.on("console", _on_console)
    page.on("pageerror", _on_pageerror)

    started = datetime.now(timezone.utc)
    interactions_attempted = []
    interactions_failed = []
    pass_flag = True
    error_load = None

    try:
        # 1. Load
        await page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            # networkidle is best-effort — many SPAs never fully idle
            pass

        # 2. Scroll
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(300)

        # 3. Interactions
        if do_interactions:
            for interaction in INTERACTIONS.get(route, []):
                interactions_attempted.append(interaction)
                try:
                    if interaction["type"] == "click_if_present":
                        loc = page.locator(interaction["selector"])
                        if await loc.count() > 0:
                            await loc.first.click(timeout=3000, force=False, no_wait_after=True)
                            await page.wait_for_timeout(400)
                    elif interaction["type"] == "fill_if_present":
                        loc = page.locator(interaction["selector"])
                        if await loc.count() > 0:
                            await loc.first.fill(interaction.get("value", ""), timeout=3000)
                            await page.wait_for_timeout(300)
                except Exception as e:
                    interactions_failed.append({**interaction, "error": str(e)[:200]})

        # 4. Wait for delayed errors
        await page.wait_for_timeout(2000)

        # 5. Screenshot
        screenshot_bytes = await page.screenshot(full_page=False)
    except Exception as e:
        pass_flag = False
        error_load = str(e)
        screenshot_bytes = b""

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)

    if console_errors or page_errors:
        pass_flag = False
    if strict_warn and console_warnings:
        pass_flag = False

    result = {
        "url": full_url,
        "route": route,
        "form_factor": form_factor,
        "load_error": error_load,
        "console_errors": console_errors,
        "console_warnings": console_warnings,
        "page_errors": page_errors,
        "interactions_attempted": interactions_attempted,
        "interactions_failed": interactions_failed,
        "duration_ms": duration_ms,
        "pass": pass_flag,
    }

    safe_route = route.replace("/", "_") if route != "/" else "_root"
    json_path = out_dir / f"sweep{safe_route}_{form_factor}.json"
    json_path.write_text(json.dumps(result, indent=2))
    if screenshot_bytes:
        png_path = out_dir / f"sweep{safe_route}_{form_factor}.png"
        png_path.write_bytes(screenshot_bytes)
        result["screenshot_b64"] = base64.b64encode(screenshot_bytes[:512]).decode() + "...truncated"
    else:
        result["screenshot_b64"] = ""

    await page.close()

    icon = "✓" if pass_flag else "✗"
    cerr = len(console_errors)
    perr = len(page_errors)
    cwarn = len(console_warnings)
    print(f"  {icon} [{form_factor:7s}] {route:14s} "
          f"console_err={cerr}  page_err={perr}  console_warn={cwarn}  "
          f"interactions={len(interactions_attempted)}/{len(interactions_failed)} failed  "
          f"({duration_ms}ms)")
    return result


async def run(base_url: str, form_factors: list[str], do_interactions: bool,
              strict_warn: bool) -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return 2

    repo_root = Path(__file__).resolve().parents[1]
    date_tag = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = repo_root / "pwm-team" / "coordination" / "evidence" / "step4_console" / date_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Console-error sweep — Step 4 Criterion 7")
    print(f"URL: {base_url}")
    print(f"Form factors: {', '.join(form_factors)}")
    print(f"Interactions: {'enabled' if do_interactions else 'disabled'}")
    print(f"Strict warn: {'on' if strict_warn else 'off'}")
    print(f"Output: {out_dir}")
    print()

    all_results = []
    overall_pass = True

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        for ff in form_factors:
            ctx_args = _form_factor_args(ff)
            print(f"--- Form factor: {ff} ---")
            context = await browser.new_context(**ctx_args)
            for route in ROUTES:
                r = await sweep_route(
                    context, base_url, route, ff,
                    do_interactions, strict_warn, out_dir,
                )
                all_results.append(r)
                if not r["pass"]:
                    overall_pass = False
            await context.close()
        await browser.close()

    # Summary
    summary_path = out_dir / "summary.md"
    lines = [
        f"# Console-error sweep — {date_tag}",
        "",
        f"**URL:** {base_url}",
        f"**Routes:** {len(ROUTES)}",
        f"**Form factors:** {', '.join(form_factors)}",
        f"**Total runs:** {len(all_results)}",
        f"**Overall:** {'✓ PASS' if overall_pass else '✗ FAIL'}",
        "",
        "| Route | Form | console_err | page_err | console_warn | Interactions failed | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in all_results:
        status = "✓ PASS" if r["pass"] else "✗ FAIL"
        lines.append(
            f"| {r['route']} | {r['form_factor']} | "
            f"{len(r['console_errors'])} | {len(r['page_errors'])} | "
            f"{len(r['console_warnings'])} | "
            f"{len(r['interactions_failed'])}/{len(r['interactions_attempted'])} | {status} |"
        )

    failures = [r for r in all_results if not r["pass"]]
    if failures:
        lines += ["", "## Failures (sample errors)", ""]
        for r in failures:
            lines.append(f"### {r['form_factor']} {r['route']}")
            if r.get("load_error"):
                lines.append(f"- LOAD ERROR: `{r['load_error'][:200]}`")
            for ce in r["console_errors"][:5]:
                lines.append(f"- console.error: `{ce.get('text', '')[:200]}`")
            for pe in r["page_errors"][:5]:
                lines.append(f"- pageerror: `{pe.get('text', '')[:200]}`")
            lines.append("")

    summary_path.write_text("\n".join(lines) + "\n")
    print()
    print("=" * 60)
    print(f"Summary: {summary_path}")
    print(f"Overall: {'✓ PASS' if overall_pass else '✗ FAIL'}")
    return 0 if overall_pass else 1


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("base_url", nargs="?", default="https://explorer.pwm.platformai.org",
                    help="Base URL of the deployed explorer")
    ap.add_argument("--form-factor", choices=["desktop", "mobile", "both"], default="both")
    ap.add_argument("--no-interactions", action="store_true",
                    help="Skip click/fill interactions (load-only sweep ~30s vs ~90s)")
    ap.add_argument("--strict-warn", action="store_true",
                    help="Treat console.warn as a failure (default: only error/pageerror fail)")
    args = ap.parse_args()

    ffs = ["desktop", "mobile"] if args.form_factor == "both" else [args.form_factor]
    do_interactions = not args.no_interactions

    return asyncio.run(run(args.base_url, ffs, do_interactions, args.strict_warn))


if __name__ == "__main__":
    sys.exit(main())
