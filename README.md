# ctv-tracker
**Requirements**

- Cardano Node fully synced (tested with 10.1.4)
- Kupo (tested with 2.10.0). To-do: update shell script to match only the necessary policy ids
  - Current kupo instance will sync from genesis, matching everything with "*" (all PIDs and addrs) and will not prune spent utxos. This can be changed later on for this project for much faster syncing and smaller db size. Current db is around 373 GB
- Python3
