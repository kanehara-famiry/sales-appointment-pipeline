#!/opt/data/.venv_sales/bin/python3
"""ドメインパワー取得スクリプト
Usage: domain_authority.py <domain>
Returns JSON with Ahrefs DR, Moz DA (if available), backlink approximation.
"""
import sys, json, urllib.request, re

def get_ahrefs_dr(domain):
    """Ahrefs Domain Rating (free, no key needed)"""
    url = f"https://api.ahrefs.com/v3/public/domain-rating-free?target={domain}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            dr = data.get("domain_rating", {}).get("domain_rating")
            return dr
    except Exception as e:
        return {"error": str(e)}

def estimate_backlinks(domain):
    """Estimate backlinks via Google site search approximation"""
    search_url = f"https://www.google.com/search?q=site:{domain}"
    try:
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Try to find "About X results"
            match = re.search(r'About ([\d,]+) results', html)
            if match:
                return int(match.group(1).replace(',', ''))
            # Fallback: count result divs
            results = html.count('<div class="g"')
            return results if results > 0 else None
    except Exception:
        return None

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: domain_authority.py <domain>"}))
        sys.exit(1)
    
    domain = sys.argv[1].strip()
    # Clean URL to domain
    domain = re.sub(r'^https?://(www\.)?', '', domain).split('/')[0]
    
    result = {
        "domain": domain,
        "ahrefs_dr": None,
        "estimated_backlinks": None,
        "source": "ahrefs_api"
    }
    
    dr = get_ahrefs_dr(domain)
    if isinstance(dr, dict) and "error" in dr:
        result["ahrefs_dr"] = f"error: {dr['error']}"
    else:
        result["ahrefs_dr"] = dr
    
    # Backlink estimate
    bl = estimate_backlinks(domain)
    if bl is not None:
        result["estimated_backlinks"] = bl
        result["backlink_method"] = "Google site: search"
    
    # Interpretation
    dr_val = result["ahrefs_dr"]
    if isinstance(dr_val, (int, float)):
        if dr_val >= 50:
            result["interpretation"] = "高（強いドメインパワー）"
        elif dr_val >= 30:
            result["interpretation"] = "中（一定の被リンクあり）"
        elif dr_val >= 10:
            result["interpretation"] = "低（被リンクは限定的）"
        else:
            result["interpretation"] = "非常に低い（ほぼ被リンクなし）"
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
