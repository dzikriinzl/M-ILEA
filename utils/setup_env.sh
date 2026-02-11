#!/bin/bash
echo "[*] Checking M-ILEA Dependencies..."

# Check Java
if type -p java > /dev/null; then
    echo "[+] Java found"
else
    echo "[-] Java not found. Please install JRE/JDK."
fi

# Check Apktool
if type -p apktool > /dev/null; then
    echo "[+] Apktool found"
else
    echo "[-] Apktool not found. Install: sudo apt install apktool"
fi

# Create folders
mkdir -p logs evaluation/results
echo "[*] Workspace ready: /logs and /evaluation/results created."