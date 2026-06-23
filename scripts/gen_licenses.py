#!/usr/bin/env python3
"""
VLK Launcher — CLI License Generator
Usage: python scripts/gen_licenses.py --count 10 --role user
Calls the server API to generate license keys.
"""
import argparse
import requests
import os

def main():
    parser = argparse.ArgumentParser(description="Generate VLK license keys")
    parser.add_argument("--count", type=int, default=5, help="Number of keys")
    parser.add_argument("--role", choices=["user","admin","superadmin"], default="user")
    parser.add_argument("--server", default=os.environ.get("VLK_SERVER_URL","http://localhost:8000"))
    parser.add_argument("--token", default=os.environ.get("VLK_ADMIN_TOKEN",""))
    parser.add_argument("--master-pw", default=os.environ.get("MASTER_PASSWORD",""))
    args = parser.parse_args()

    if not args.token:
        print("Error: Provide --token or set VLK_ADMIN_TOKEN env var")
        return

    r = requests.post(
        f"{args.server}/licenses/generate",
        json={"role": args.role, "count": args.count},
        headers={
            "Authorization": f"Bearer {args.token}",
            "X-Master-Password": args.master_pw,
        },
        timeout=10
    )
    if r.ok:
        data = r.json()
        print(f"Generated {len(data['generated'])} {args.role} license(s):")
        for key in data["generated"]:
            print(f"  {key}")
    else:
        print(f"Error {r.status_code}: {r.text}")

if __name__ == "__main__":
    main()
