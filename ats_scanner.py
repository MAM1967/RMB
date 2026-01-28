import requests
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_single_company(domain, timeout=5):
    """Check one company for ATS board - returns immediately on first hit"""
    company_name = domain.split('.')[0]
    
    patterns = [
        f"https://{domain}/careers",
        f"https://jobs.{domain}",
        f"https://careers.{domain}",
        f"https://{domain}/jobs",
        f"https://boards.greenhouse.io/{company_name}",
        f"https://jobs.lever.co/{company_name}",
        f"https://jobs.ashbyhq.com/{company_name}",
        f"https://{company_name}.wd1.myworkdayjobs.com",
        f"https://jobs.smartrecruiters.com/{company_name}",
    ]
    
    for url in patterns:
        try:
            resp = requests.head(
                url, 
                timeout=timeout, 
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if resp.status_code == 200:
                return {
                    'domain': domain,
                    'careers_url': resp.url,
                    'pattern_matched': url,
                    'status': 'FOUND'
                }
        except requests.exceptions.RequestException:
            continue
    
    return {
        'domain': domain,
        'careers_url': None,
        'pattern_matched': None,
        'status': 'NOT_FOUND'
    }

def scan_companies(company_list, max_workers=10):
    """Scan companies in parallel with progress updates"""
    results = []
    completed = 0
    total = len(company_list)
    
    print(f"Starting scan of {total} companies with {max_workers} workers...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_domain = {
            executor.submit(check_single_company, domain): domain 
            for domain in company_list
        }
        
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                if completed % 10 == 0 or result['status'] == 'FOUND':
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    remaining = (total - completed) / rate if rate > 0 else 0
                    
                    status_emoji = "✓" if result['status'] == 'FOUND' else "✗"
                    print(f"{status_emoji} {completed}/{total} | {domain} | "
                          f"{elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining")
                    
            except Exception as e:
                print(f"✗ Error processing {domain}: {e}")
                results.append({
                    'domain': domain,
                    'careers_url': None,
                    'pattern_matched': None,
                    'status': 'ERROR'
                })
                completed += 1
    
    return results

def save_results(results, filename='ats_scan_results.csv'):
    """Save results to CSV"""
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['domain', 'status', 'careers_url', 'pattern_matched'])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults saved to {filename}")

if __name__ == "__main__":
    # Read companies from CSV - handle different possible column names
    companies = []
    with open('companies.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        # Print headers to debug
        first_row = next(reader)
        headers = list(first_row.keys())
        print(f"CSV headers found: {headers}")
        
        # Try to find domain column (case insensitive)
        domain_col = None
        for header in headers:
            if 'domain' in header.lower():
                domain_col = header
                break
        
        if not domain_col:
            print("ERROR: Could not find 'domain' column in CSV")
            print("Available columns:", headers)
            exit(1)
        
        # Add first row's domain
        companies.append(first_row[domain_col])
        
        # Add rest of domains
        for row in reader:
            if row[domain_col]:  # Skip empty domains
                companies.append(row[domain_col])
    
    print(f"Loaded {len(companies)} companies from companies.csv")
    
    # Run scan
    results = scan_companies(companies, max_workers=15)
    
    # Summary
    found = [r for r in results if r['status'] == 'FOUND']
    not_found = [r for r in results if r['status'] == 'NOT_FOUND']
    errors = [r for r in results if r['status'] == 'ERROR']
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Found: {len(found)} ({len(found)/len(results)*100:.1f}%)")
    print(f"  Not Found: {len(not_found)} ({len(not_found)/len(results)*100:.1f}%)")
    print(f"  Errors: {len(errors)} ({len(errors)/len(results)*100:.1f}%)")
    print(f"{'='*60}")
    
    if found:
        print("\nSample found:")
        for r in found[:10]:
            print(f"  {r['domain']} → {r['careers_url']}")
    
    save_results(results)
