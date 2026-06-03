#!/usr/bin/env python3
import re

files = [
    'memory/2026-05-26.md',
    'memory/2026-05-31.md',
    'MEMORY.md',
]

patterns = [
    # Telegram bot tokens
    (r'8625632035:AAErDGlE-se2up0_EAw40kORenyZwMWlv34', '[REDACTED]'),
    (r'8943515832:AAHiqfd9EUPtGB64bVJLiqMPM_yQ4Qzzv5c', '[REDACTED]'),
    # Google OAuth
    (r'37264603747-4aqbr5fikmovc2omn45fffct4hv9q1g1\.apps\.googleusercontent\.com', '[REDACTED]'),
    (r'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', '[REDACTED]'),
    # Zoho old
    (r'1000\.3JWYP8QJM6S3CIGPPOQ5R8VOUFCQ9Z', '[REDACTED]'),
    (r'2145cf205323bd243c721dd33ebb9521b6d41d9ce0', '[REDACTED]'),
    (r'1000\.2034b714368b7f024a7d98a0746442cd\.[A-Za-z0-9_-]+', '[REDACTED]'),
    # Zoho new
    (r'1000\.GRI56LMPI3FQGQBZYK7UG2C49XUSDB', '[REDACTED]'),
    (r'1e59379b56985f2a94705fffb72f29469186a0453e', '[REDACTED]'),
    (r'1000\.6[a-zA-Z0-9]+', '[REDACTED]'),
    # DoubleTick
    (r'key_Ru[a-zA-Z0-9]+', '[REDACTED]'),
]

for f in files:
    with open(f) as fh:
        content = fh.read()
    for pat, repl in patterns:
        content = re.sub(pat, repl, content)
    with open(f, 'w') as fh:
        fh.write(content)
    print(f'Redated: {f}')