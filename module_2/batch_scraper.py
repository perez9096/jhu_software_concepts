#!/usr/bin/env python3
"""
Batch scraper runner with intermediate saves.
Scrapes in chunks (e.g., 50 pages per batch) and saves results after each batch.
"""

import json
import os
from scraper import scrape_data, save_data, load_data

BATCH_SIZE = 50
FINAL_OUTPUT = "applicant_data.json"
BATCH_OUTPUT = "applicant_data_batch_{}.json"
COMBINED_OUTPUT = "applicant_data_combined.json"


def batch_scrape(total_pages=200, batch_size=BATCH_SIZE):
    """Run scraper in batches with intermediate saves.
    
    Note: scrape_data() always starts from page 1 and goes up to max_pages.
    To avoid re-fetching, we accumulate results and track which URLs we've seen.
    """
    all_data = []
    existing_urls = set()
    
    num_batches = (total_pages + batch_size - 1) // batch_size
    
    for batch_num in range(1, num_batches + 1):
        start_page = (batch_num - 1) * batch_size + 1
        end_page = min(batch_num * batch_size, total_pages)
        
        print(f"\n{'='*60}")
        print(f"BATCH {batch_num}: Scraping pages 1-{end_page} (new data only)")
        print(f"{'='*60}")
        
        # Scrape up to end_page (always from page 1 internally)
        batch_data = scrape_data(max_pages=end_page)
        
        # Extract only new records we haven't seen before
        new_records = []
        for record in batch_data:
            if record['url'] not in existing_urls:
                new_records.append(record)
                existing_urls.add(record['url'])
        
        all_data.extend(new_records)
        
        # Save batch results
        batch_file = BATCH_OUTPUT.format(batch_num)
        save_data(new_records, filename=batch_file)
        print(f"New records in batch {batch_num}: {len(new_records)}")
        print(f"Batch results saved: {batch_file}")
        
        print(f"Total accumulated unique records: {len(all_data)}")
        
        # Save combined progress
        save_data(all_data, filename=COMBINED_OUTPUT)
        print(f"Progress saved: {COMBINED_OUTPUT}")
    
    # Save final output
    save_data(all_data, filename=FINAL_OUTPUT)
    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(all_data)} records saved to {FINAL_OUTPUT}")
    print(f"{'='*60}")
    
    return all_data


if __name__ == "__main__":
    import sys
    
    total_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else BATCH_SIZE
    
    batch_scrape(total_pages=total_pages, batch_size=batch_size)
