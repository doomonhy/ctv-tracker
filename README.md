# ctv-tracker
**Requirements**

- Cardano Node fully synced (tested with 10.1.4)
- Kupo (tested with 2.10.0). To-do: update shell script to match only the necessary policy ids
  - Current kupo instance will sync from genesis, matching everything with "*" (all PIDs and addrs) and will not prune spent utxos. This can be changed later on for this project for much faster syncing and smaller db size. Current db is around 373 GB
- Python3

**Usage**
- earthvault-wmtx-tracker.py will look for every UTxO containing the EarthVault pid, then for each address found, it will sum up all the unspent WMTx, this will result the .csv file with how much WMTx each EV holder has. This should be more or less the amount to be staked to EN71 once live.
