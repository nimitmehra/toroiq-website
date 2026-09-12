"""Validate reviewed research records and render the public example + CSV.

Offline presentation step. Source review and interpretation are manual inputs.
No private tracker data is read. No website is published by this script.
"""
import csv
from datetime import date
from html import escape as e
import io
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'examples/management-expectations.json'


def validate(data):
    assert data['mode']=='historical_worked_example'
    reviewed=date.fromisoformat(data['reviewed_at'])
    records=data['records']; assert len(records)>=2
    assert len({r['id'] for r in records})==len(records)
    dates=[date.fromisoformat(r['published_at']) for r in records]
    assert dates==sorted(dates) and all(d<=reviewed for d in dates)
    assert len({(r['entity'],r['topic']) for r in records})==1
    for r in records:
        assert r['record_type']=='management_expectation' and r['outcome_status']=='not_assessed'
        assert r['summary_type']=='paraphrase'
        assert urlsplit(r['source_url']).scheme=='https'
        assert urlsplit(r['source_url']).netloc=='www.microsoft.com'
        assert r['statement'] and r['source_locator'] and r['speaker']
    assert set(data['assessment']['depends_on']) <= {r['id'] for r in records}


def main():
    data=json.loads(DATA.read_text());validate(data)
    output=io.StringIO()
    fields=['entity','ticker','topic','published_at','period','record_type','statement','horizon','speaker','source_url','source_locator','reviewed_at','outcome_status']
    writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(data['records'])
    (ROOT/'examples/management-expectations.csv').write_text(output.getvalue())
    cards=[]
    for i,r in enumerate(data['records'],1):
        d=date.fromisoformat(r['published_at'])
        cards.append(f'''<article class="event"><p class="eyebrow">0{i} / {d:%d %B %Y} · {e(r['period'])}</p><h3>{e(r['horizon'])}</h3><p>{e(r['statement'])}</p><p class="speaker">{e(r['speaker'])} · Paraphrased expectation</p><a href="{e(r['source_url'])}">Read Microsoft’s transcript ↗</a><details><summary>Find the passage</summary><p>{e(r['source_locator'])}</p></details></article>''')
    template=(ROOT/'examples/page.template.html').read_text()
    rendered=template.replace('{{TIMELINE}}','\n'.join(cards)).replace('{{ASSESSMENT}}',e(data['assessment']['interpretation'])).replace('{{JSON}}',e(json.dumps(data,indent=2,ensure_ascii=False)))
    assert '{{' not in rendered
    (ROOT/'example.html').write_text(rendered)
    print('Validated 3 reviewed statements; rendered example.html and spreadsheet CSV.')


if __name__=='__main__': main()
