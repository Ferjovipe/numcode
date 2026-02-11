# NumCode

**A Universal Numeric Protocol for Tokenized Text Transmission**

NumCode is an open protocol for encoding tokenized text as numeric IDs derived from language-specific frequency dictionaries. It is not an AI model and does not generate or translate text.

Round-trip decoding is lossless for the canonical token stream, provided the same dictionary version and tokenization rules are used. IDs can be transmitted as binary or represented as sparse patterns in a 10×20 ideogram grid (Protocol Spec v6.8).

A photonic extension (TFD) can project these ideograms as spatial light states over a CW carrier — see [The Vision](#the-vision) for details.

**Six languages. One protocol. 100% round-trip token accuracy.**

---

## How It Works

```
TEXT             →  NumCode        →  Ideogram Grid    →  NumCode        →  TEXT
"El agua"         →  15b 383b       →  ·: ·:·           →  15b 383b       →  "El agua"
"水是生命"        →  211b 4b 50b    →  · ·: ·           →  211b 4b 50b    →  "水是生命"
"knowledge"       →  505b           →  ·::              →  505b           →  "Knowledge"
```

**Note on canonicalization:** The tokenizer normalizes text to lowercase before encoding. The decoder capitalizes the first letter of each sentence. Round-trip accuracy is lossless with respect to the normalized token stream.

## The Protocol

Each token is encoded as `[ID][suffix]`:

| Suffix | Meaning | Example | Decoding Rule |
|--------|---------|---------|---------------|
| `b` | Concept — dictionary lookup | `383b` → "agua" (ES) | Look up ID in language dictionary |
| `n` | Literal number — no dictionary | `2026n` → 2026 | Output the number as-is |
| `r` | Repetition — total count including first | `7r` → repeat previous token 7× total | Output previous token N total times (including the already-emitted one) |
| `s` | Sparse — null padding for alignment | `200s` → 200 null positions | Insert N empty positions in stream |

### Repetition Example

```
Input: "amor amor amor amor amor amor amor" (7 times)
Without compression: 319b 319b 319b 319b 319b 319b 319b → 7 ideograms
With repetition:     319b 7r → 2 ideograms (71% reduction)

Decoding 319b 7r: emit "amor" (from 319b), then 7r means 7 total → emit 6 more "amor" = 7 total.
```

---

## The Ideogram Grid (Protocol Spec v6.8)

Each numeric ID is encoded as a pattern of active cells in a 10×20 grid (200 cells). The grid is read by position:

```
     Col1   Col2   Col3   Col4   Col5  Col6   Col7   Col8   Col9   Col10
R1  [    ] [    ] [    ] [    ] [ ar ] [ zh ] [ fr ] [ pt ] [ es ] [eng ]  ← Language
R2  [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ]  ← Reserved
R3                                      900K   90K    9K    900
R4                                      800K   80K    8K    800
R5                                      700K   70K    7K    700
R6                                      600K   60K    6K    600
R7                                      500K   50K    5K    500
R8                                      400K   40K    4K    400
R9  [ *?] [ 9B ] [900M] [90M] [ 9M]   300K   30K    3K    300
R10 [*E8] [ 8B ] [800M] [80M] [ 8M]   200K   20K    2K    200
R11 [*E7] [ 7B ] [700M] [70M] [ 7M]   100K   10K    1K    100
R12 [*E6] [ 6B ] [600M] [60M] [ 6M]    60     70     80     90
R13 [*E5] [ 5B ] [500M] [50M] [ 5M]    50   [ s  ] [ r  ] [ n  ]        ← Suffixes
R14 [*E4] [ 4B ] [400M] [40M] [ 4M]    40      9      8      7
R15 [*E3] [ 3B ] [300M] [30M] [ 3M]    30      6      5      4          ← Units
R16 [*E2] [ 2B ] [200M] [20M] [ 2M]    20      3      2      1            (3×3)
R17 [*10] [ 1B ] [100M] [10M] [ 1M]    10                     0
R18 [INF] [    ] [    ] [    ] [    ] [bin ] [enc ] [ so ] [ im ] [    ]  ← Data Type
R19 [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ]  ← Reserved
R20 [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ] [    ]  ← Reserved
```

### Grid Zones

| Zone | Location | Purpose |
|------|----------|---------|
| Language selector | Row 1, Cols 5–10 | Indicates which GOLD dictionary the receiver should load |
| Data type | Row 18, Cols 6–9 | `bin` = binary, `enc` = encrypted, `so` = sound, `im` = image. No marker = text (default) |
| Multipliers | Column 1, Rows 9–17 | Extend range: ×10, ×100, ... ×100000000. Row 9 = ×? (reserved for larger) |
| Suffixes | Row 13, Cols 7–9 | `s` = sparse, `r` = repetition, `n` = number |
| Units | Rows 14–16, Cols 7–9 | 3×3 inverted block: 9,8,7 / 6,5,4 / 3,2,1 |
| Zero | Row 17, Col 9 | The value 0 |
| Tens (low) | Col 6, Rows 13–17 | 10, 20, 30, 40, 50 |
| Tens (high) | Row 12, Cols 6–9 | 60, 70, 80, 90 |
| Hundreds | Col 7, Rows 3–11 | 100–900 (ascending) |
| Thousands | Col 8, Rows 3–11 | 1K–9K (ascending) |
| Ten-thousands | Col 9, Rows 3–11 | 10K–90K (ascending) |
| Hundred-thousands | Col 6, Rows 3–11 | 100K–900K (ascending) |
| Millions+ | Cols 5,4,3,2 ascending | 1M–9B (ascending per column) |
| Infinity | Row 18, Col 1 | Represents infinity |
| Reserved | Rows 2, 17(cols 7-8), 19, 20 | Future expansion |

### Reading Example: ID 383 ("agua" in Spanish)

```
383 = 300 + 80 + 3

  300 → Row 9, Col 7   (Hundreds: column 7, ascending from row 11)
   80 → Row 12, Col 8  (Tens high: row 12)
    3 → Row 16, Col 7  (Units: 3×3 block position)

Active cells: 3 out of 200 = extremely sparse pattern
```

Lower IDs (frequent words) activate fewer cells. This is a natural property of frequency-based numbering: the most common words produce the simplest patterns.

---

## Compression Results

Typical savings of ~60–65% vs UTF-8 were observed in our February 2026 tests under the defined binary encoding and tokenization settings.

| Test | Original (UTF-8) | NumCode Binary | Savings |
|------|-------------------|----------------|---------|
| Short Spanish phrase (37 chars) | 37 bytes | 14 bytes | 62% |
| English paragraph (134 chars) | 134 bytes | 47 bytes | 65% |
| Literary Spanish text (514 chars) | 514 bytes | 193 bytes | 62% |
| Chinese text (77 tokens) | 231 bytes | ~90 bytes | 61% |

These results correspond to the binary wire format of NumCode IDs. Ideogram (visual) encoding has different size characteristics depending on grid resolution.

---

## Dictionaries

NumCode uses native-frequency dictionaries built exclusively from real human text. No machine translations. No synthetic data. Each dictionary is independent — IDs are assigned per language based on that language's own corpus frequency.

### Community Release (for GitHub/HuggingFace)

| Language | Unique Tokens | Sources |
|----------|---------------|---------|
| Spanish (ES) | 7,000,000 | Wikipedia ES + OpenSubtitles ES |
| English (EN) | 9,618,282 | Wikipedia EN (6.4M articles) + OpenSubtitles EN (441M lines) |
| Arabic (AR) | 4,800,903 | OpenSubtitles AR + Wikipedia AR + Multilingual supplement |
| Chinese (ZH) | 2,271,472 | mC4 ZH + OpenSubtitles ZH + Multilingual supplement |
| Portuguese (PT) | 1,777,661 | OpenSubtitles PT + Wikipedia PT + Multilingual supplement |
| French (FR) | 1,710,392 | OpenSubtitles FR + Wikipedia FR + Multilingual supplement |

**Community total: 26+ million unique tokens across 6 languages.**

A full research build with 34.7M Spanish tokens (including mC4 ES) is available separately.

### Dictionary Format

```
ID	TOKEN	COUNT
1	.	640043295
2	de	585251977
3	,	477755862
```

Tab-separated. Sorted by descending frequency. ID 1 is always the most common token in that language.

### Important Note on IDs

IDs are per-language, not universal. ID 383 maps to "agua" in the Spanish dictionary and to a different word in English. The ideogram's language selector (Row 1) tells the receiver which dictionary to use. **This is a transmission protocol, not a translation system.**

### Download

Dictionaries are hosted on HuggingFace:

🔗 **[HuggingFace: NumCode Dictionaries](https://huggingface.co/datasets/thehive-numcode/dictionaries)**

### Corpus Attribution

The dictionaries contain only tokens and their frequency counts — no original text is distributed. Source corpora include:

- Wikipedia — CC BY-SA 3.0
- OpenSubtitles — via OPUS project
- mC4 — via AllenAI/C4, derived from Common Crawl

---

## Quick Start

### Requirements

```bash
pip install Pillow
```

### Run

```bash
python numcode.py
```

The system loads all 6 dictionaries and provides an interactive prompt:

```
=== NUMCODE v4 ===
Loading dictionaries...
  es: 6,999,977 tokens
  eng: 9,618,282 tokens
  fr: 1,710,392 tokens
  pt: 1,777,661 tokens
  zh: 2,271,472 tokens
  ar: 4,800,903 tokens

Ready. 6 languages loaded.

> El agua es vida. La tierra es hogar. El fuego es energía.
  Language: es
  Tokens: 15
  NumCode: 15b 383b 35b 176b 1b 9b 617b 35b 1521b 1b 15b 1374b 35b 991b 1b
  Strip: strip.png (16 blocks)
  Decoded: El agua es vida. La tierra es hogar. El fuego es energía.
  Verification: 100% PERFECT

> 知识就是力量
  Language: zh
  Tokens: 6
  NumCode: 138b 683b 53b 4b 157b 331b
  Strip: strip.png (7 blocks)
  Decoded: 知识就是力量
  Verification: 100% PERFECT

> amor amor amor amor amor amor amor
  Language: es
  Tokens: 2
  NumCode: 319b 7r
  Strip: strip.png (3 blocks)
  Decoded: Amor amor amor amor amor amor amor.
  Verification: 100% PERFECT
```

### Commands

| Command | Description |
|---------|-------------|
| Any text | Auto-detects language, encodes, generates ideogram strip, decodes, verifies |
| `leer` / `read` | Reads the last generated strip from disk |
| `salir` / `quit` | Exit |

---

## Verified Test Results

Every test below was executed on February 10–11, 2026 using numcode.py v4 with the Community dictionaries. All achieved 100% round-trip accuracy on the canonical token stream:

| Language | Input | Tokens | Result |
|----------|-------|--------|--------|
| Spanish | "El agua es vida. La tierra es hogar. El fuego es energía." | 15 | ✅ 100% |
| English | "The future belongs to those who believe in the beauty of their dreams" | 13 | ✅ 100% |
| Chinese | "知识就是力量" (Knowledge is power) | 6 | ✅ 100% |
| Arabic | "العلم نور والجهل ظلام" (Science is light, ignorance is darkness) | 4 | ✅ 100% |
| French | "L'imagination est plus importante que le savoir" | 8 | ✅ 100% |
| Spanish (repetition) | "amor amor amor amor amor amor amor" | 2 (compressed) | ✅ 100% |
| Spanish (number) | "2026" | 1 | ✅ 100% |
| Spanish (multi-sentence) | "El atletico de madrid será campeon de europa." | 9 | ✅ 100% |

---

## Versioning

NumCode uses separate version numbers for protocol and implementation:

| Component | Version | Description |
|-----------|---------|-------------|
| Protocol Spec | v6.8 | Grid layout, suffix definitions, encoding rules |
| Reference Implementation | v4 | Python encoder/decoder (numcode.py) |
| Dictionaries | 2026-02-10 | Community release, 6 languages |

---

## Repository Structure

```
numcode/
├── README.md                ← This file
├── numcode.py               ← Complete encoder/decoder (Reference Implementation v4)
├── emisor_puntos_v2.py      ← Standalone ideogram strip generator
├── receptor_lector_v2.py    ← Standalone ideogram strip reader
└── dictionaries/            ← Download from HuggingFace
    ├── GOLD_ES.txt          ← Spanish (7M tokens)
    ├── GOLD_EN.txt          ← English (9.6M tokens)
    ├── GOLD_AR.txt          ← Arabic (4.8M tokens)
    ├── GOLD_ZH.txt          ← Chinese (2.3M tokens)
    ├── GOLD_PT.txt          ← Portuguese (1.8M tokens)
    └── GOLD_FR.txt          ← French (1.7M tokens)
```

---

## The Vision

NumCode is the foundation layer of a larger architecture:

**v4 — Numeric Protocol** ✅
Words become numbers. Numbers have suffixes. Frequency determines ID assignment.

**v5 — Native Dictionaries** ✅
Each language gets its own clean dictionary built from millions of authentic texts.

**v6 — Ideographic Encoding** ✅
Numbers become geometric patterns on a 10×20 grid. Visual round-trip transmission verified with 100% accuracy.

**v7 — Photonic Transmission** (R&D)
The ideogram grid becomes a physical mask. A continuous-wave (CW) laser projects through it. No direct laser on/off keying at the source — a CW carrier is modulated by selecting spatial states (masks) via ultrafast electro-optic photonic switching. One flash = one complete concept. Theoretical latency: sub-30 picoseconds per symbol.

**v8 — Fractal Information Architecture** (Conceptual)
Visual objects composed of their own semantic definition. An image of water where every pixel contains the ID for "water". Zoom in: more detail reveals more IDs. Information where form and content are the same thing.

---

## What NumCode Is NOT

- **Not a translator.** Each language encodes and decodes to itself using its own independent dictionary. IDs are per-language, not universal concept IDs.
- **Not an AI model.** No neural networks. No training. No hallucinations. Deterministic lookup tables built from real human text.
- **Not lossy compression.** Every token in the canonical stream is recovered exactly. 100% round-trip accuracy on the normalized token sequence.

---

## About

NumCode is part of **THE HIVE** project — a deterministic natural language processing system designed to eliminate hallucinations through evidence-based responses.

- 🌐 Website: [aithehive.com](https://aithehive.com)
- 💻 Code: [GitHub](https://github.com/thehive-numcode)
- 📦 Dictionaries: [HuggingFace](https://huggingface.co/datasets/thehive-numcode/dictionaries)

**Created by Fernando · Madrid, Spain · February 2026**

Patent pending — OEPM application filed February 11, 2026.

---

## License

**Code:** MIT License — use it, modify it, build on it.

**Dictionaries:** Released for research and non-commercial use. Derived from publicly available corpora (Wikipedia CC BY-SA 3.0, OpenSubtitles via OPUS, mC4 via AllenAI). Only token frequency data is distributed; no original text content is included.
