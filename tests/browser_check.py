"""Optional browser integration checks. Requires Playwright with Firefox installed.

Run against localhost or pass the deployed URL as the first argument.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit, unquote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8766/'
ENGINE = sys.argv[2] if len(sys.argv) > 2 else 'firefox'

with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch()
    context = browser.new_context(viewport={'width': 1440, 'height': 1050}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE, wait_until='networkidle')
    page.wait_for_function('document.querySelector("#focus").options.length > 1')
    assert page.locator('h1').count() == 1
    assert page.locator('.project-card').count() == 4
    assert page.locator('.seed-download').count() == 4
    ids = page.locator('[id]').evaluate_all('(els) => els.map(e => e.id)')
    assert len(ids) == len(set(ids))
    for href in page.locator('a[href]').evaluate_all('(els) => els.map(e => e.getAttribute("href"))'):
        parts = urlsplit(href)
        if href.startswith('#'):
            assert parts.fragment in ids, href
        elif not parts.scheme and href != '/':
            assert (ROOT / unquote(parts.path)).exists(), href

    # The illustration must actually advance, pause and respect motion preferences.
    page.wait_for_function('Number(document.querySelector(".travel-pulse").style.opacity) > 0.2', timeout=2000)
    first_x = page.locator('.travel-pulse').first.get_attribute('cx')
    page.wait_for_timeout(250)
    assert page.locator('.travel-pulse').first.get_attribute('cx') != first_x, 'No immediate movement'
    assert page.locator('.agent-activity').is_visible()
    page.wait_for_function('document.querySelector(".graph-window").dataset.phase === "1"', timeout=7000)
    page.wait_for_function('Number(document.querySelector(".travel-pulse").style.opacity) > 0.2', timeout=2000)
    page.locator('#motion-toggle').click()
    phase = page.locator('.graph-window').get_attribute('data-phase')
    x = page.locator('.travel-pulse').first.get_attribute('cx')
    page.wait_for_timeout(350)
    assert page.locator('.graph-window').get_attribute('data-phase') == phase
    assert page.locator('.travel-pulse').first.get_attribute('cx') == x
    assert page.locator('#motion-toggle').get_attribute('aria-pressed') == 'true'
    page.locator('#motion-toggle').click()
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_function('document.querySelector("#motion-toggle").disabled')
    assert page.locator('#motion-toggle').is_disabled()
    assert page.locator('.graph-window').get_attribute('data-motion') == 'paused'
    assert page.locator('.travel-pulse').first.evaluate('(e) => getComputedStyle(e).display') == 'none'
    page.emulate_media(reduced_motion='no-preference')
    page.wait_for_function('!document.querySelector("#motion-toggle").disabled')

    for market in ['macro', 'nse', 'us', 'crypto']:
        page.locator(f'[data-market="{market}"]').click()
        assert page.locator('#market').input_value() == market
        assert page.locator(f'[data-market="{market}"]').get_attribute('aria-pressed') == 'true'
        first_id = page.locator('#focus option').nth(1).get_attribute('value')
        page.locator('#focus').select_option(first_id)
        page.locator('#cadence').select_option('weekly')
        page.locator('#question').fill('What could change my research thesis?')
        with page.expect_download() as info:
            page.locator('.download-button').click()
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / 'config.json'
            info.value.save_as(config_path)
            config = json.loads(config_path.read_text())
            assert config['mode'] == 'seed' and config['focus'] == [first_id]
            assert config['market'] == market and config['cadence'] == 'weekly'
            output = Path(directory) / 'workspace'
            result = subprocess.run([sys.executable, str(ROOT / 'starter/seed.py'), '--config', str(config_path), '--output', str(output)], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            assert first_id in [n['id'] for n in json.loads((output / 'graph.json').read_text())['nodes']]
            assert json.loads((output / 'workspace.json').read_text())['schedule_active'] is False
        with page.expect_download() as info:
            page.locator('#selected-seed').click()
        graph = json.loads(Path(info.value.path()).read_text())
        assert graph['market'] == market and len(graph['nodes']) >= 10

    page.locator('#question').fill(' ')
    assert page.locator('#question').evaluate('(e) => !e.checkValidity()')
    page.locator('#question').fill('Which dependencies deserve a closer look?')
    page.locator('#copy-config').click()
    page.wait_for_function('document.querySelector("#config-status").textContent.length > 0')
    assert page.locator('#config-status').inner_text()
    page.locator('[data-market="macro"]').click()
    page.locator('#cadence').select_option('on-demand')
    page.locator('.wordmark').first.focus()
    page.evaluate('window.scrollTo(0, 0)')
    page.screenshot(path='/private/tmp/toroiq-seeds-desktop.png', full_page=True)
    for width in [320, 375, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
        if width == 390:
            page.screenshot(path='/private/tmp/toroiq-seeds-mobile.png', full_page=True)
    page.locator('#build').scroll_into_view_if_needed()
    page.wait_for_timeout(100)
    assert page.locator('.graph-window').get_attribute('data-motion') == 'paused'
    no_js = browser.new_context(java_script_enabled=False)
    fallback = no_js.new_page()
    fallback.goto(BASE)
    assert fallback.locator('noscript a').is_visible()
    assert not fallback.locator('#config-form').is_visible()
    assert fallback.locator('.seed-download').count() == 4
    # Every public machine-readable resource must parse from the actual server.
    for path in ['projects.json', 'starter/seeds/index.json', 'starter/seed.schema.json', 'starter/seed.config.example.json']:
        response = context.request.get(BASE.rstrip('/') + '/' + path)
        assert response.ok, path
        response.json()
    assert errors == [], errors
    browser.close()
print('PASS: animation movement/pause/reduced-motion/offscreen; four seed/config downloads and CLI roundtrips; six viewport widths; no-JS, links and browser errors')
