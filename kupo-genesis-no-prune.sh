#!/bin/bash
kupo \
        --node-socket $HOME/mainnet/node.socket \
        --node-config $HOME/mainnet/config.json \
        --host 0.0.0.0 \
        --since origin \
        --match "*" \
        --workdir /mnt/sdb2/db-genesis-no-prune
