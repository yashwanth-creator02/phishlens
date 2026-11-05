#!/usr/bin/env python3
"""Verify Supabase Row-Level Security (RLS) isolation between users."""
import argparse
import json
import os
import urllib.request
import urllib.error

def main():
    parser = argparse.ArgumentParser(description="Verify Supabase RLS row isolation")
    parser.add_argument("--supabase-url", default=os.getenv("SUPABASE_URL"))
    parser.add_argument("--anon-key", default=os.getenv("SUPABASE_ANON_KEY", os.getenv("SUPABASE_KEY", "")))
    parser.add_argument("--token-a", default=os.getenv("USER_A_TOKEN", os.getenv("SUPABASE_USER_A_TOKEN", "")))
    parser.add_argument("--token-b", default=os.getenv("USER_B_TOKEN", os.getenv("SUPABASE_USER_B_TOKEN", "")))
    parser.add_argument("--analysis-a", default=os.getenv("ANALYSIS_A", ""))
    parser.add_argument("--analysis-b", default=os.getenv("ANALYSIS_B", ""))
    args = parser.parse_args()

    if not args.supabase_url or not args.token_a or not args.token_b or not args.analysis_a or not args.analysis_b:
        print("Error: SUPABASE_URL, token-a, token-b, analysis-a, and analysis-b must be provided via args or environment.")
        exit(1)

    url_base = args.supabase_url.rstrip("/")

    def query(token: str, analysis_id: str) -> list:
        url = f"{url_base}/rest/v1/analyses?id=eq.{analysis_id}"
        req = urllib.request.Request(url, headers={
            "apikey": args.anon_key,
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        })
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"HTTP error {e.code}: {e.read().decode()}")
            raise

    print(f"Verifying RLS on {url_base}...")
    
    res_a_a = query(args.token_a, args.analysis_a)
    assert len(res_a_a) == 1, f"User A should see analysis A, got {res_a_a}"
    
    res_a_b = query(args.token_a, args.analysis_b)
    assert res_a_b == [], f"User A should not see analysis B, got {res_a_b}"

    res_b_b = query(args.token_b, args.analysis_b)
    assert len(res_b_b) == 1, f"User B should see analysis B, got {res_b_b}"

    res_b_a = query(args.token_b, args.analysis_a)
    assert res_b_a == [], f"User B should not see analysis A, got {res_b_a}"

    print("RLS verification passed: users are strictly isolated.")

if __name__ == "__main__":
    main()
