"""Validate packaged assets or an exported emoji without relying on absolute paths."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_bundle():
    manifest = json.loads((ROOT / 'assets/checksums.json').read_text(encoding='utf-8'))
    for relative, expected in manifest.items():
        if digest((ROOT / relative).read_bytes()) != expected:
            raise ValueError(f'Asset checksum mismatch: {relative}')
    catalog = json.loads((ROOT / 'assets/catalog.json').read_text(encoding='utf-8'))
    if len(catalog) != 22 or len({item['id'] for item in catalog}) != 22:
        raise ValueError('Expected 22 unique example entries')
    for item in catalog:
        for key in ['scene', 'foreground', 'preview']:
            if not (ROOT / 'assets' / item[key]).is_file():
                raise ValueError(f'Missing catalog asset: {item[key]}')
    return {'assets_verified': len(manifest), 'examples': len(catalog)}


def verify_output(output):
    record = json.loads(Path(str(output) + '.json').read_text(encoding='utf-8'))
    for suffix, expected in record['files'].items():
        if digest(Path(str(output) + suffix).read_bytes()) != expected:
            raise ValueError(f'Output checksum mismatch: {suffix}')
    svg = Path(str(output) + '.svg').read_text(encoding='utf-8')
    ET.fromstring(svg)
    embedded = re.findall(r'data:image/svg\+xml;base64,([^\"]+)', svg)
    master = (ROOT / 'assets/body/master.svg').read_bytes()
    if len(embedded) != 1 or base64.b64decode(embedded[0]) != master:
        raise ValueError('Output must embed exactly one complete shared body master')
    if record['body_master_sha256'] != digest(master):
        raise ValueError('Recorded body master differs from installed body master')
    foregrounds = re.findall(r'data:image/png;base64,([^\"]+)', svg)
    if not foregrounds or any(digest(base64.b64decode(data)) != record['foreground_sha256'] for data in foregrounds):
        raise ValueError('Embedded foreground differs from recorded source')
    with Image.open(Path(str(output) + '.png')) as image:
        if image.mode != 'RGBA' or list(image.size) != record['canvas']:
            raise ValueError('Output canvas or RGBA mode is incorrect')
        low, high = image.getchannel('A').getextrema()
        if low != 0 or high < 240:
            raise ValueError('Expected both transparent background and opaque artwork')
    return {'shared_body_master': 'verified', 'foreground': 'verified', 'alpha': 'verified', 'canvas': record['canvas']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--bundle', action='store_true')
    group.add_argument('--output', type=Path, help='Output basename without extension')
    args = parser.parse_args()
    try:
        report = verify_bundle() if args.bundle else verify_output(args.output)
    except (ValueError, KeyError, OSError, ET.ParseError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
