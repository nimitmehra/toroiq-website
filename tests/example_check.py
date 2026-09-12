"""Check the cold-outreach example, downloads and responsive layout."""
import csv
import io
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8766/'
with sync_playwright() as p:
    browser=p.firefox.launch()
    page=browser.new_page(accept_downloads=True,viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    response=page.goto(BASE.rstrip('/')+'/example.html',wait_until='networkidle')
    assert response.ok
    assert page.locator('h1').count()==1 and page.locator('.event').count()==3
    assert 'Historical example' in page.locator('.date-label').inner_text()
    for suffix in ['json','csv']:
        with page.expect_download() as result:
            page.locator(f'a[download][href$=".{suffix}"]').last.click()
        text=Path(result.value.path()).read_text()
        if suffix=='json':
            data=json.loads(text);assert len(data['records'])==3
            assert all(r['record_type']=='management_expectation' for r in data['records'])
            assert data==json.loads((ROOT/'examples/management-expectations.json').read_text())
        else:
            rows=list(csv.DictReader(io.StringIO(text)));assert len(rows)==3
            assert rows[0]['published_at']=='2025-01-29' and rows[-1]['published_at']=='2025-07-30'
    page.locator('.json summary').click();assert page.locator('.json pre').is_visible()
    for width in [320,390,768,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
    page.locator('.json summary').click();page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path='/private/tmp/toroiq-example-desktop.png',full_page=True)
    page.set_viewport_size({'width':390,'height':900});page.screenshot(path='/private/tmp/toroiq-example-mobile.png',full_page=True)
    nojs=browser.new_context(java_script_enabled=False);fallback=nojs.new_page()
    fallback.goto(BASE.rstrip('/')+'/example.html')
    assert fallback.locator('.event').count()==3
    assert fallback.locator('a[download]').count()==3
    assert not errors,errors
    browser.close()
print('PASS: three sourced statements, CSV/JSON downloads, four widths, readable without JavaScript.')
