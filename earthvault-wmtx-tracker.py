import json
import os
import requests
import csv

CACHE_FILE = "cache/ev-cache.json" # after first run, this file will be updated with new UTXOs on subsequent runs, so we don't have to fetch everything every time
WMTX_PID = "e5a42a1a1d3d1da71b0449663c32798725888d2eb0843c4dabeca05a" # policy id for WMTX token

API_CTV_OG = "http://192.168.15.6:1442/matches/addr1qxhxhrcqul2uxhuj3z7l2uny4wuqgevp7f8eay0et4r4yqemma2p8lwj23rpu4dx6fpff28ex68km228d3cspkmgj9wsgjd6th"
API_CTV_AGGRO = "http://192.168.15.6:1442/matches/addr1q83f6tdruwhl9uffy5gjp74kg4ckd6k4yf87ufzcyn3lulw4cgufghdhcrvdzru7e72erjmju0lh8yarmqs9hwujf7asgffay2"
API_CTV_TREASURY = "http://192.168.15.6:1442/matches/addr1q9555y0h2ctyxpeudqsz2y8hrjtpylcalt5yamhwu2h849aj4d49ywtglhllmcttw43e2l78t9zf6ya8wwj26y6pnc5svxumhw" # ev held here
API_EARTHVAULT = "http://192.168.15.6:1442/matches/*?policy_id=2af4e8789778b79ddf25f2062377709e49181265d87beb2f99c902a4&unspent" # earthvault pid
API_HEALTH = "http://192.168.15.6:1442/health"

def save_to_csv(data, filename):
    sorted_holders = sorted(data.items(), key=lambda x: x[1], reverse=True)

    # Save to CSV
    with open("holders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["address", "amount"])
        for addr, amt in sorted_holders:
            writer.writerow([addr, amt])

    print(f"Saved {len(sorted_holders)} holders to holders.csv")

def fetch_api_data(url):
    try:
        response = requests.get(url, timeout=3600)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []
    
def get_current_slot():
    resp = requests.get(API_HEALTH, timeout=10)
    lines = resp.text.splitlines()
    for line in lines:
        if line.startswith("kupo_most_recent_node_tip"):
            # line looks like: "kupo_most_recent_node_tip  167673954"
            return int(line.split()[1])
    return 0

def load_utxos():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            utxos = json.load(f)
        print(f"Loaded {len(utxos)} UTXOs from cache.")

        # Find the max slot number
        max_slot = max(utxo.get("created_at", {}).get("slot_no", 0) for utxo in utxos)
        print(f"Max slot in cache: {max_slot}")

        # Fetch current tip
        current_slot = get_current_slot()
        print(f"Current node tip: {current_slot}")

        if max_slot >= current_slot:
            print("Cache is up to date. No new UTXOs.")
            return utxos

        # Fetch new UTXOs after max_slot
        print(f"Fetching new UTXOs after slot {max_slot}...")
        # Assuming API supports a 'start_slot' query param
        new_utxos = fetch_api_data(f"{API_EARTHVAULT}&created_after={max_slot}")
        print(f"Fetched {len(new_utxos)} new UTXOs.")

        if new_utxos:
            utxos.extend(new_utxos)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(utxos, f, indent=2)
            print("Cache updated with new UTXOs.")

        return utxos
    else:
        # Cache doesn't exist, fetch all
        print("Fetching all UTXOs from API...")
        utxos = fetch_api_data(API_EARTHVAULT)
        print(f"Fetched {len(utxos)} UTXOs.")
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(utxos, f, indent=2)
        return utxos

def get_token_balance(addr, pid):
    """Fetch unspent outputs for an address and sum the balance of a given policy id"""
    url = f"http://192.168.15.6:1442/matches/{addr}?policy_id={pid}&unspent"
    utxos = fetch_api_data(url)
    total = 0
    for utxo in utxos:
        assets = utxo.get("value", {}).get("assets", {})
        for asset_id, amount in assets.items():
            if asset_id.startswith(pid):
                total += amount
    return total

def get_wmtx_amt():
    files = ["ev-holders.csv"]
    # add to filter_addr any address that should not be included as a holder, this may include nft marketplace and lending/borrow addresses.
    filter_addr = ["addr1x8rjw3pawl0kelu4mj3c8x20fsczf5pl744s9mxz9v8n7efvjel5h55fgjcxgchp830r7h2l5msrlpt8262r3nvr8ekstg4qrx"] # JPG.store Ask v1 addr
    holders_addrs = set()

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                holders_addrs.add(row[0])  # add to set (no duplicates)
    
    holders_addrs = [addr for addr in holders_addrs if addr not in filter_addr]
    
    results = []
    for addr in holders_addrs:
        amt = get_token_balance(addr, WMTX_PID)
        if amt == 0:
            continue
        print(f"{addr}: {amt}")
        results.append((addr, amt))
    results.sort(key=lambda x: x[1], reverse=True)
    with open("ev-wmtx-balances.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["address", "amount"])
        for addr, amt in results:
            writer.writerow([addr, amt])

    print(f"Saved {len(results)} addresses")

def main():
    utxos = load_utxos()
    holders = {}

    for i, utxo in enumerate(utxos, start=1):
        addr = utxo.get("address")
        assets = utxo.get("value", {}).get("assets", {})

        if i % 100 == 0:
            print(f"Processing {i}/{len(utxos)} UTXOs...")

        for asset_id, amount in assets.items():
            if asset_id.startswith("2af4e8789778b79ddf25f2062377709e49181265d87beb2f99c902a4"):
                holders[addr] = holders.get(addr, 0) + amount

    sorted_holders = sorted(holders.items(), key=lambda x: x[1], reverse=True)

    print("\nWallets holding tokens from this policy:")
    for addr, amt in sorted_holders:
        print(f"{addr}: {amt}")
    save_to_csv(holders, "holders.csv")

if __name__ == "__main__":
    # main()
    get_wmtx_amt()
