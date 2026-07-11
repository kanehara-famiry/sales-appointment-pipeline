#!/opt/data/.venv_sales/bin/python3
"""IS引継ぎ情報・コールログ検索スクリプト
指定された会社名に関連する情報を、ローカルファイルやSlackメモから検索する。

Usage: is_data_search.py <company_name> [--dir <search_directory>]
"""
import sys, json, os, re

def search_files_for_company(company_name, search_dir=None):
    """Search local files for mentions of the company."""
    if not search_dir:
        search_dir = "/opt/data"
    
    results = []
    company_keywords = company_name.replace("株式会社", "").replace("(", "").replace(")", "")
    
    # Search patterns
    patterns = [
        company_name,
        company_keywords,
        re.escape(company_keywords[:max(3, len(company_keywords)//2)])
    ]
    
    # Look for relevant file types
    for root, dirs, files in os.walk(search_dir):
        # Skip cache and venv directories
        if any(skip in root for skip in [".cache", ".venv", "__pycache__", "node_modules"]):
            continue
        
        for f in files:
            if f.endswith(('.md', '.txt', '.log', '.csv', '.json')):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read(5000)  # Read first 5K chars
                        if company_keywords in content or company_name in content:
                            # Extract context lines
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if company_keywords in line or company_name in line:
                                    results.append({
                                        "file": fpath,
                                        "line": i + 1,
                                        "snippet": line.strip()[:200],
                                        "relevance": "高" if company_name in line else "中"
                                    })
                except Exception:
                    continue
    
    return results

def search_slacklike_data(company_name):
    """Search for company-relevant data in known scripts/configs."""
    # Check for known Salesforce/CRM-like data patterns
    crm_data = []
    crm_files = [
        "/opt/data/home/.hermes/",
        "/opt/data/scripts/"
    ]
    
    for base in crm_files:
        if os.path.exists(base):
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.endswith(('.json', '.yaml', '.yml', '.conf')):
                        fpath = os.path.join(root, f)
                        try:
                            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                                content = fp.read()
                                if company_name in content:
                                    crm_data.append({
                                        "source": fpath,
                                        "type": "設定ファイル"
                                    })
                        except Exception:
                            continue
    return crm_data

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: is_data_search.py <company_name>", "results": []}))
        sys.exit(1)
    
    company = sys.argv[1]
    search_dir = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--dir" else "/opt/data"
    
    result = {
        "company": company,
        "local_file_matches": search_files_for_company(company, search_dir),
        "crm_config_matches": search_slacklike_data(company),
        "note": "Slackメッセージ検索にはSlack APIアクセスが必要です。ローカルファイルは検索済み。"
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
