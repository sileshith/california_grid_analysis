"""Check tracked release text for private paths, attribution and tracking URLs."""
import json
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Spell tokens in pieces so the checker does not trigger on its own source.
PATTERNS={
 'private_chat_url':r'chat'+'gpt'+r'\.com',
 'sandbox_path':r'sand'+'box:',
 'mac_home':r'/Us'+'ers/',
 'tracking':r'utm_'+'[a-z]+',
 'tool_attribution':r'\b(?:Open'+'AI|Claude|Chat'+'GPT|Copilot)\b',
 'generator_attribution':r'\bgenerated'+' by\b',
}


def inspect():
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    findings=[];scanned=0
    for name in paths:
        p=ROOT/name
        if not p.is_file():continue
        try:text=p.read_text()
        except (UnicodeError,OSError):continue
        scanned+=1
        for label,pattern in PATTERNS.items():
            for n,line in enumerate(text.splitlines(),1):
                if re.search(pattern,line,re.I):findings.append(dict(path=name,line=n,pattern=label))
    return dict(scanned_text_files=scanned,findings=findings,scope='Tracked release text, including notebook source and saved outputs. Binary metadata is checked separately.')


if __name__=='__main__':
    result=inspect();print(json.dumps(result,indent=2));raise SystemExit(bool(result['findings']))
