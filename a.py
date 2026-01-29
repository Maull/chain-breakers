#!/bin/bash

# Header
echo "Co,Sq,Slot"

# --- COMPANY 0 ---
# 5 Squads (0-4), 10 Slots (0-9)
for squad in {0..4}; do
  for slot in {0..9}; do
    echo "0,$squad,$slot"
  done
done

# --- COMPANIES 1-10 ---
# 11 Squads (0-10), 10 Slots (0-9)
for company in {1..10}; do
  for squad in {0..10}; do
    for slot in {0..9}; do
      echo "$company,$squad,$slot"
    done
  done
done