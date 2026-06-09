#!/usr/bin/env python3
import argparse
import json
import time
import os
import re
from scraper import fetch
from bs4 import BeautifulSoup

INFILE = 'applicant_data_combined.json'
OUTFILE = 'applicant_data_enhanced.json'


def extract_from_detail(detail_html, row_text=''):
    soup = BeautifulSoup(detail_html, 'html.parser')
    detail_text = soup.get_text(' ', strip=True)
    search_text = f"{row_text} {detail_text}" if detail_text else row_text

    result = {}

    # Semester
    m = re.search(r"\b(Fall|Spring|Summer|Winter)\s+\d{4}\b", search_text, re.IGNORECASE)
    if m:
        result['semester_year'] = m.group(0)

    # GRE AW
    m = re.search(r"GRE\s*AW[:\s]*?([0-9]+(?:\.[0-9]+)?)", search_text, re.IGNORECASE)
    if m:
        result['gre_aw'] = m.group(1)
    else:
        m = re.search(r"Analytical Writing[:\s]*([0-9]+(?:\.[0-9]+)?)", search_text, re.IGNORECASE)
        if m:
            result['gre_aw'] = m.group(1)
        else:
            m = re.search(r"\bAW[:\s]*([0-9]+(?:\.[0-9]+)?)\b", search_text)
            if m:
                result['gre_aw'] = m.group(1)

    # GRE V
    m = re.search(r"GRE\s*V[:\s]*?(\d{2,3})", search_text, re.IGNORECASE)
    if m:
        result['gre_v_score'] = m.group(1)
    else:
        m = re.search(r"GRE\s*(?:Verbal)[:\s]*?(\d{2,3})", search_text, re.IGNORECASE)
        if m:
            result['gre_v_score'] = m.group(1)
        else:
            m = re.search(r"\bV[:\s]*(\d{2,3})\b", search_text)
            if m:
                result['gre_v_score'] = m.group(1)

    # GRE Q
    m = re.search(r"\bQ[:\s]*(\d{2,3})\b", search_text)
    if m:
        result['gre_q_score'] = m.group(1)

    # GRE total explicit
    m = re.search(r"\bGRE(?:\s*General)?[:\s]*?(\d{3})\b", search_text, re.IGNORECASE)
    if m:
        result['gre_score'] = m.group(1)
    else:
        m = re.search(r"\b(\d{3})\s*\(.*?V[:\s]*(\d{2,3})", search_text)
        if m:
            result['gre_score'] = m.group(1)

    # If gre_score missing but V and Q exist, compute
    if 'gre_score' not in result and 'gre_v_score' in result and 'gre_q_score' in result:
        try:
            result['gre_score'] = str(int(result['gre_v_score']) + int(result['gre_q_score']))
        except Exception:
            pass

    # GPA (try to extract if not present)
    if 'gpa' not in result:
        m = re.search(r"GPA[:\s]*([0-9]+(?:\.[0-9]+)?)(?:\s*/\s*[0-9]+(?:\.[0-9]+)?)?", search_text, re.IGNORECASE)
        if m:
            result['gpa'] = float(m.group(1)) if '.' in m.group(1) else int(m.group(1))
        else:
            m = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*/\s*4(?:\.0+)?\b", search_text)
            if m:
                try:
                    result['gpa'] = float(m.group(1))
                except Exception:
                    result['gpa'] = m.group(1)

    return result


def main(limit=None):
    if not os.path.exists(INFILE):
        print('No', INFILE)
        return

    data = json.load(open(INFILE))
    total = len(data)
    print('Loaded', total, 'records')

    updated = 0
    for i, rec in enumerate(data, 1):
        if limit is not None and i > limit:
            break

        url = rec.get('url')
        row_text = rec.get('raw_text', '')
        try:
            if url:
                html = fetch(url, retries=2)
                if html:
                    extras = extract_from_detail(html, row_text=row_text)
                    changed = False
                    for k, v in extras.items():
                        if v is not None and (rec.get(k) is None):
                            rec[k] = v
                            changed = True
                    if changed:
                        updated += 1
        except Exception as e:
            print('Error at', i, url, e)

        if i % 100 == 0 or (limit is not None and i == limit):
            print(f'Processed {i}/{total}, updated {updated} so far')
            json.dump(data, open(OUTFILE, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            time.sleep(1)
        else:
            time.sleep(0.5)

    print('Done. total updated:', updated)
    json.dump(data, open(OUTFILE, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enhance combined GradCafe dataset')
    parser.add_argument('--limit', type=int, default=None, help='Number of records to process')
    args = parser.parse_args()
    main(limit=args.limit)
