#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "⚙️  Inizializzazione ambiente..."
    python3 -m venv venv
fi

# Assicuriamoci che rich sia installato
venv/bin/pip install --quiet prompt_toolkit rich

venv/bin/python fantaasta_cli.py
