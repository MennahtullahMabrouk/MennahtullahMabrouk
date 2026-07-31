#!/usr/bin/env python3
import re
from pathlib import Path

SVG = Path("assets/game-runner.svg")
README = Path("README.md")

svg = SVG.read_text()
match = re.search(r"STAGE (\d+)", svg)
if match is None:
    raise SystemExit("STAGE number not found in game-runner.svg")
stage = int(match.group(1)) + 1
SVG.write_text(svg.replace(f"STAGE {match.group(1)}", f"STAGE {stage}"))

readme = README.read_text()
vmatch = re.search(r"game-runner\.svg\?v=(\d+)", readme)
if vmatch is None:
    raise SystemExit("game-runner cache-buster not found in README")
version = int(vmatch.group(1)) + 1
README.write_text(
    readme.replace(f"game-runner.svg?v={vmatch.group(1)}", f"game-runner.svg?v={version}")
)

print(f"STAGE {match.group(1)} -> {stage}, ?v={vmatch.group(1)} -> {version}")
