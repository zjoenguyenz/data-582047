#!/usr/bin/env python3
"""Publish 582047.m3u from the base list only. Stdlib only.

Since 2026-11-14 (owner order) the TV list carries NO football: the
dabanh mirror merge was removed and the base itself was cleaned of
football-streaming groups. The football links live in the dabanh
playlist only.
"""
import re, sys, collections

BASE = "582047-base.m3u"
OUT = "582047.m3u"
SENSITIVE = re.compile(r'(mac=[0-9A-Fa-f:]{17}|play_token=|tpninosaga|dropboxusercontent)', re.I)

def decode_escapes(s):
    """Decode literal backslash-u escape sequences some sources ship
    un-decoded in titles (e.g. BLV names), combining surrogate pairs."""
    s = re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), s)
    s = re.sub(r'\\[uU]([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
    out, i = [], 0
    while i < len(s):
        o = ord(s[i])
        if 0xD800 <= o <= 0xDBFF and i + 1 < len(s) and 0xDC00 <= ord(s[i + 1]) <= 0xDFFF:
            out.append(chr(0x10000 + ((o - 0xD800) << 10) + (ord(s[i + 1]) - 0xDC00))); i += 2
        elif 0xD800 <= o <= 0xDFFF:
            out.append('\ufffd'); i += 1
        else:
            out.append(s[i]); i += 1
    return ''.join(out)

def parse_text(text):
    entries, cur = [], None
    for line in text.splitlines():
        if line.startswith('#EXTINF'):
            cur = {'extinf': line, 'opts': [], 'url': None}
        elif line.startswith('#') and cur is not None:
            cur['opts'].append(line)
        elif line.strip() and cur is not None:
            cur['url'] = line.strip(); entries.append(cur); cur = None
    return entries

def group_of(e):
    m = re.search(r'group-title="([^"]*)"', e['extinf'])
    return m.group(1) if m else 'Khác'

def main():
    base = parse_text(decode_escapes(open(BASE, encoding='utf-8', errors='ignore').read()))
    entries = [e for e in base if not SENSITIVE.search(e['url'])]
    PRIORITY = ['LIVE EVENTS 🔴', 'KÊNH ĐẶC SẮC', 'KÊNH TRONG NƯỚC & ĐỊA PHƯƠNG', 'KÊNH TIN TỨC',
                'KÊNH PHIM TRUYỆN', 'Quốc Tế', 'Địa phương', 'KÊNH TRONG NƯỚC', 'Radio',
                'KÊNH RADIO NƯỚC NGOÀI']
    groups = collections.OrderedDict()
    for e in entries: groups.setdefault(group_of(e), []).append(e)
    ordered = [g for g in PRIORITY if g in groups] + sorted(
        [g for g in groups if g not in PRIORITY], key=lambda g: -len(groups[g]))
    lines = ['#EXTM3U url-tvg="https://lichphatsong.io.vn/epg.xml"']
    n = 0
    for g in ordered:
        for e in groups[g]:
            lines.append(e['extinf']); lines.extend(e['opts']); lines.append(e['url']); n += 1
    new = '\n'.join(lines) + '\n'
    try:
        old = open(OUT, encoding='utf-8', errors='ignore').read()
    except FileNotFoundError:
        old = None
    if old == new:
        print("no change:", n, "entries"); return 0
    open(OUT, 'w', encoding='utf-8').write(new)
    print("updated:", n, "entries (base only)")
    return 0

if __name__ == '__main__':
    sys.exit(main())
