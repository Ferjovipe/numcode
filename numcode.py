#!/usr/bin/env python3
"""
NumCode v4 — Universal Numeric Protocol for Tokenized Text Transmission
Reference Implementation · Protocol Spec v6.8

Encodes text as numeric IDs from native frequency dictionaries.
Generates 10×20 ideogram strips. 100% round-trip token accuracy.

Usage:
    python numcode.py

Requires: pip install Pillow
Dictionaries: Place GOLD_*.txt files in ./dictionaries/

Created by Fernando · THE HIVE Project · February 2026
License: MIT
"""

import os
import re
try:
    from PIL import Image
except ImportError:
    Image = None
    print("Warning: Pillow not installed. Ideogram strips disabled.")
    print("Install with: pip install Pillow")

# ---- CONFIGURATION ----

DICT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dictionaries')

LANG_FILES = {
    'es': 'GOLD_ES.txt', 'eng': 'GOLD_EN.txt', 'fr': 'GOLD_FR.txt',
    'zh': 'GOLD_ZH.txt', 'ar': 'GOLD_AR.txt', 'pt': 'GOLD_PT.txt'
}

# Grid coordinates (Protocol Spec v6.8)
LANG_CELLS = {'ar':(1,5),'zh':(1,6),'fr':(1,7),'pt':(1,8),'es':(1,9),'eng':(1,10)}
LANG_CELLS_INV = {v:k for k,v in LANG_CELLS.items()}
DATA_TYPES = {'bin':(18,6),'enc':(18,7),'so':(18,8),'im':(18,9)}
DATA_TYPES_INV = {v:k for k,v in DATA_TYPES.items()}
SUFFIXES = {'s':(13,7),'r':(13,8),'n':(13,9)}
SUFFIXES_INV = {v:k for k,v in SUFFIXES.items()}

PUNCT_ATTACH_RIGHT = {'.', ',', ';', ':', '!', '?', ')', '"', "'", '-'}

# ---- LOAD DICTIONARIES ----

print("=== NUMCODE v4 ===")
print("Loading dictionaries...", flush=True)

dicts_encode = {}
dicts_decode = {}

for lang, filename in LANG_FILES.items():
    path = os.path.join(DICT_DIR, filename)
    if not os.path.exists(path):
        continue
    enc = {}
    dec = {}
    with open(path, 'r', encoding='utf-8') as f:
        f.readline()  # skip header
        for line in f:
            p = line.strip().split('\t')
            if len(p) >= 3:
                token = p[1].strip()
                tid = int(p[0])
                enc[token] = tid
                dec[tid] = token
    dicts_encode[lang] = enc
    dicts_decode[lang] = dec
    print(f"  {lang}: {len(enc):,} tokens", flush=True)

print(f"\nReady. {len(dicts_encode)} languages loaded.\n")

# ---- TOKENIZER ----

def tokenize(text, lang):
    """Split text into tokens based on language."""
    if lang == 'zh':
        return list(text.replace(' ', ''))
    elif lang == 'ar':
        return re.findall(
            r"[\u0600-\u06FF\u0750-\u077F]+|[0-9]+|[a-zA-Z']+|[.,;:!?()\"'\-]", text)
    else:
        return re.findall(
            r"[a-zA-Z\u00e0-\u024f\u00c0-\u024f']+|[0-9]+|[.,;:!?()\"'\-]", text.lower())

# ---- ENCODER ----

def encode(text, lang):
    """Encode text to NumCode sequence. Returns list of ID+suffix strings."""
    if lang not in dicts_encode:
        return []
    enc = dicts_encode[lang]
    tokens = tokenize(text, lang)

    # Phase 1: raw encoding
    raw = []
    not_found = []
    for t in tokens:
        if re.match(r'^[0-9]+$', t):
            raw.append(f"{t}n")
        else:
            t_lower = t.lower() if lang != 'zh' else t
            if t_lower in enc:
                raw.append(f"{enc[t_lower]}b")
            elif t in enc:
                raw.append(f"{enc[t]}b")
            else:
                not_found.append(t)
    if not_found:
        print(f"  Not found ({len(not_found)}): {', '.join(not_found[:10])}")

    # Phase 2: repetition compression
    result = []
    i = 0
    while i < len(raw):
        count = 1
        while i + count < len(raw) and raw[i + count] == raw[i]:
            count += 1
        result.append(raw[i])
        if count > 1:
            result.append(f"{count}r")
        i += count

    return result

# ---- DECODER ----

def decode(numcode_str, lang):
    """Decode NumCode string back to text."""
    if lang not in dicts_decode:
        return ""
    dec = dicts_decode[lang]
    tokens = numcode_str.split()
    words = []

    for token in tokens:
        suffix = None
        num_str = ''
        for ch in token:
            if ch.isdigit():
                num_str += ch
            elif ch in 'bnsr':
                suffix = ch
        if not num_str:
            continue
        tid = int(num_str)

        if suffix == 'n':
            words.append(str(tid))
        elif suffix == 'r':
            if words:
                last = words[-1]
                for _ in range(tid - 1):
                    words.append(last)
        elif suffix == 's':
            pass  # sparse padding, skip
        else:  # 'b' or default
            if tid in dec:
                words.append(dec[tid])
            else:
                words.append(f"[?{tid}]")

    # Reconstruct text with proper punctuation
    if lang == 'zh':
        return ''.join(words)

    if not words:
        return ""

    parts = []
    for i, w in enumerate(words):
        if i == 0:
            parts.append(w)
        elif w in PUNCT_ATTACH_RIGHT:
            parts.append(w)
        elif parts and parts[-1] and parts[-1][-1] in ('(',):
            parts.append(w)
        else:
            parts.append(' ' + w)

    text = ''.join(parts)

    # Capitalize first letter of each sentence
    if text:
        text = text[0].upper() + text[1:]
        text = re.sub(
            r'([.!?])\s+([a-záéíóúàèìòùâêîôûäëïöüç])',
            lambda m: m.group(1) + ' ' + m.group(2).upper(), text)

    return text

# ---- IDEOGRAM GRID ----

def id_to_cells(number):
    """Convert numeric ID to list of active cell coordinates (row, col)."""
    cells = []
    # Units (3×3 block, rows 14-16, cols 7-9, inverted spiral)
    u = number % 10
    if u > 0:
        pos = {9:(14,7),8:(14,8),7:(14,9),6:(15,7),5:(15,8),4:(15,9),
               3:(16,7),2:(16,8),1:(16,9)}
        cells.append(pos[u])
    # Tens
    d = (number // 10) % 10
    if d > 0:
        if d <= 5:
            pos = {1:(17,6),2:(16,6),3:(15,6),4:(14,6),5:(13,6)}
            cells.append(pos[d])
        else:
            pos = {6:(12,6),7:(12,7),8:(12,8),9:(12,9)}
            cells.append(pos[d])
    # Hundreds through Billions
    for place, col in [(100,7),(1000,8),(10000,9),(100000,6),(1000000,5),
                        (10000000,4),(100000000,3),(1000000000,2)]:
        digit = (number // place) % 10
        if digit > 0:
            cells.append((11-(digit-1), col))
    return cells

def create_strip(token_list, lang=None, data_type=None, filename="strip.png"):
    """Generate ideogram strip as PNG image."""
    if Image is None:
        return 0
    has_header = lang or data_type
    total = len(token_list) + (1 if has_header else 0)
    img = Image.new('1', (10 * total, 20), color=1)

    # Header block
    if has_header:
        header = Image.new('1', (10, 20), color=1)
        px = header.load()
        if lang and lang in LANG_CELLS:
            r, c = LANG_CELLS[lang]
            px[c-1, r-1] = 0
        if data_type and data_type in DATA_TYPES:
            r, c = DATA_TYPES[data_type]
            px[c-1, r-1] = 0
        img.paste(header, (0, 0))

    offset = 1 if has_header else 0
    for i, token in enumerate(token_list):
        block = Image.new('1', (10, 20), color=1)
        px = block.load()
        num_str = ''.join(ch for ch in token if ch.isdigit())
        suffix = None
        for ch in token:
            if ch in 'snrSNR':
                suffix = ch.lower()
        if not num_str:
            continue
        cells = id_to_cells(int(num_str))
        if suffix and suffix in SUFFIXES:
            cells.append(SUFFIXES[suffix])
        for row, col in cells:
            if 0 <= row-1 < 20 and 0 <= col-1 < 10:
                px[col-1, row-1] = 0
        img.paste(block, ((i + offset) * 10, 0))

    img.save(filename)
    return total

def read_cell(pixels, block_x, row, col):
    """Check if a cell is active in the strip."""
    return pixels[block_x*10+(col-1), row-1] == 0

def read_header(pixels, block_x):
    """Read language and data type from header block."""
    lang = None
    dtype = None
    for (r,c), l in LANG_CELLS_INV.items():
        if read_cell(pixels, block_x, r, c):
            lang = l
            break
    for (r,c), t in DATA_TYPES_INV.items():
        if read_cell(pixels, block_x, r, c):
            dtype = t
            break
    return lang, dtype

def read_block(pixels, block_x):
    """Read a single ideogram block and return (number, suffix)."""
    number = 0
    suffix = 'b'

    # Units
    pos_u = {9:(14,7),8:(14,8),7:(14,9),6:(15,7),5:(15,8),4:(15,9),
             3:(16,7),2:(16,8),1:(16,9)}
    for v,(r,c) in pos_u.items():
        if read_cell(pixels, block_x, r, c):
            number += v
            break

    # Tens high
    found = False
    for v,(r,c) in {6:(12,6),7:(12,7),8:(12,8),9:(12,9)}.items():
        if read_cell(pixels, block_x, r, c):
            number += v*10
            found = True
            break
    if not found:
        for v,(r,c) in {1:(17,6),2:(16,6),3:(15,6),4:(14,6),5:(13,6)}.items():
            if read_cell(pixels, block_x, r, c):
                number += v*10
                break

    # Hundreds through Billions
    for place, col in [(100,7),(1000,8),(10000,9),(100000,6),(1000000,5),
                        (10000000,4),(100000000,3),(1000000000,2)]:
        for v in range(1,10):
            row = 11-(v-1)
            if place == 100000 and row >= 12:
                continue
            if read_cell(pixels, block_x, row, col):
                number += v*place
                break

    # Suffix
    for (r,c), s in SUFFIXES_INV.items():
        if read_cell(pixels, block_x, r, c):
            suffix = s
            break

    return number, suffix

def read_strip(filename="strip.png"):
    """Read an ideogram strip file. Returns (lang, data_type, numcode_string)."""
    if Image is None:
        return None, None, ""
    img = Image.open(filename).convert('1')
    pixels = img.load()
    num_blocks = img.size[0] // 10
    if num_blocks == 0:
        return None, None, ""

    lang, dtype = read_header(pixels, 0)
    start = 1 if (lang or dtype) else 0

    result = []
    for i in range(start, num_blocks):
        n, s = read_block(pixels, i)
        result.append(f"{n}{s}")

    return lang, dtype, ' '.join(result)

# ---- LANGUAGE DETECTION ----

def detect_language(text):
    """Auto-detect language from text content."""
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ar'
    if re.search(r'\b(the|is|are|was|were|have|has|will|would|could)\b', text.lower()):
        return 'eng'
    if re.search(r'\b(le|les|une|est|sont|avec|pour|dans|qui|mais)\b', text.lower()):
        return 'fr'
    # Portuguese detection is limited; defaults to Spanish for similar Romance text
    return 'es'

# ---- INTERACTIVE MODE ----

def main():
    print("=" * 50)
    print("NUMCODE v4 — 6 languages (es/eng/fr/zh/ar/pt)")
    print("  Punctuation attached to words")
    print("  Sentence capitalization")
    print("  Type text in any language")
    print("  'leer' / 'read' = read last strip")
    print("  'salir' / 'quit' = exit")
    print("=" * 50)

    while True:
        print()
        entrada = input("> ").strip()
        if not entrada:
            continue
        if entrada.lower() in ('salir', 'quit', 'exit'):
            print("Goodbye!")
            break
        if entrada.lower() in ('leer', 'read'):
            if os.path.exists('strip.png'):
                lang, dtype, content = read_strip('strip.png')
                print(f"  Language: {lang}")
                if dtype:
                    print(f"  Data type: {dtype}")
                print(f"  NumCode: {content}")
                if lang:
                    text = decode(content, lang)
                    print(f"  Decoded: {text}")
            else:
                print("  No strip found")
            continue

        # Detect language
        lang = detect_language(entrada)

        # Encode
        ids = encode(entrada, lang)
        if not ids:
            print("  Could not encode")
            continue

        numcode_str = ' '.join(ids)
        print(f"  Language: {lang}")
        print(f"  Tokens: {len(ids)}")
        print(f"  NumCode: {numcode_str}")

        # Generate strip
        blocks = create_strip(ids, lang=lang)
        if blocks:
            print(f"  Strip: strip.png ({blocks} blocks)")

        # Verify round-trip
        lang_r, _, content_r = read_strip('strip.png') if blocks else (lang, None, numcode_str)
        if not lang_r:
            lang_r = lang
            content_r = numcode_str
        text_r = decode(content_r, lang_r)

        ok = numcode_str == content_r
        print(f"  Decoded: {text_r}")
        print(f"  Verification: {'100% PERFECT' if ok else 'ERROR - ' + content_r}")

if __name__ == '__main__':
    main()
