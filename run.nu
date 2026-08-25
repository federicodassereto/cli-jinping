#!/usr/bin/env nu

cd $env.FILE_PWD

if not ("venv" | path exists) {
    print "⚙️  Inizializzazione ambiente..."
    ^python3 -m venv venv
}

# Select bin or Scripts based on OS
let bin_dir = if $nu.os-info.name == "windows" { "venv/Scripts" } else { "venv/bin" }
let pip_cmd = ([$bin_dir, "pip"] | path join)
let python_cmd = ([$bin_dir, "python"] | path join)

# Assicuriamoci che rich sia installato
^$pip_cmd install --quiet prompt_toolkit rich

^$python_cmd fantaasta_cli.py