"""Compose a transparent foreground with the shared, immutable body master."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rectangle(values, name):
    if not isinstance(values, list) or len(values) != 4:
        raise ValueError(f'{name} requires [x, y, width, height]')
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise ValueError(f'{name} requires finite numbers')
    if values[2] <= 0 or values[3] <= 0:
        raise ValueError(f'{name} width and height must be positive')
    return values


def load_scene(path):
    scene = json.loads(path.read_text(encoding='utf-8'))
    allowed = {'foreground', 'body_box_norm', 'rotation', 'body_clip_y_norm', 'behind_body_rects'}
    unknown = set(scene) - allowed
    if unknown:
        raise ValueError(f'Unknown scene fields: {sorted(unknown)}')
    rectangle(scene['body_box_norm'], 'body_box_norm')
    for key, default in [('rotation', 0), ('body_clip_y_norm', 1)]:
        value = scene.setdefault(key, default)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f'{key} must be finite')
    if not 0 < scene['body_clip_y_norm'] <= 1:
        raise ValueError('body_clip_y_norm must be within (0, 1]')
    for item in scene.setdefault('behind_body_rects', []):
        rectangle(item, 'behind_body_rects item')
    foreground = (path.parent / scene['foreground']).resolve()
    with Image.open(foreground) as image:
        image.load()
        if image.format != 'PNG' or image.mode != 'RGBA':
            raise ValueError('Foreground must be an RGBA PNG')
        low, high = image.getchannel('A').getextrema()
        if low != 0 or high == 0:
            raise ValueError('Foreground must contain both transparent and visible pixels')
        size = image.size
    return scene, foreground.read_bytes(), size


def compose_svg(scene, foreground, size, master):
    width, height = size
    nx, ny, nw, nh = scene['body_box_norm']
    x, y, body_width, body_height = nx * width, ny * height, nw * width, nh * height
    encoded_master = base64.b64encode(master).decode('ascii')
    encoded_foreground = base64.b64encode(foreground).decode('ascii')
    foreground_image = f'width="{width}" height="{height}" href="data:image/png;base64,{encoded_foreground}"'
    back_layer = ''
    front_clip = ''
    if scene['behind_body_rects']:
        holes = []
        for rx, ry, rw, rh in scene['behind_body_rects']:
            rx, ry, rw, rh = rx * width, ry * height, rw * width, rh * height
            holes.append(f'M{rx} {ry} v{rh} h{rw} v{-rh} Z')
        path = ' '.join(holes)
        back_layer = f'''<defs>
<clipPath id="back_limbs"><path d="{path}"/></clipPath>
<clipPath id="front_visible"><path d="M0 0 H{width} V{height} H0 Z {path}"/></clipPath>
</defs><image id="BACK_LIMBS" clip-path="url(#back_limbs)" {foreground_image}/>'''
        front_clip = 'clip-path="url(#front_visible)"'
    clip_y = scene['body_clip_y_norm'] * height
    rotation = scene['rotation']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
{back_layer}
<defs><clipPath id="body_visible"><rect width="{width}" height="{clip_y}"/></clipPath></defs>
<g clip-path="url(#body_visible)">
<g id="BODY_INSTANCE" transform="rotate({rotation} {x + body_width/2} {y + body_height/2})">
<image id="SHARED_BODY_MATERIAL" x="{x}" y="{y}" width="{body_width}" height="{body_height}" preserveAspectRatio="none" href="data:image/svg+xml;base64,{encoded_master}"/>
</g></g>
<image id="EXPRESSION_AND_PROPS" {front_clip} {foreground_image}/>
</svg>'''


def render(config, output, force=False):
    scene, foreground, size = load_scene(config.resolve())
    master = (ROOT / 'assets/body/master.svg').read_bytes()
    geometry = json.loads((ROOT / 'assets/body/geometry.json').read_text(encoding='utf-8'))
    if digest(master) != geometry['master_sha256']:
        raise ValueError('Body master checksum mismatch. Check the installed asset version.')
    suffixes = ['.png', '.svg', '.preview.png', '.json']
    output = output.resolve()
    targets = {suffix: output.parent / (output.name + suffix) for suffix in suffixes}
    existing = [path.name for path in targets.values() if path.exists()]
    if existing and not force:
        raise FileExistsError(f'Output exists: {existing}. Choose a new name or use --force.')
    try:
        import cairosvg
    except (ImportError, OSError) as error:
        raise RuntimeError('Install requirements.txt and system Cairo as described in README.md') from error
    svg = compose_svg(scene, foreground, size, master)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ibi-render-', dir=output.parent) as temporary:
        staging = Path(temporary)
        (staging / 'art.svg').write_text(svg, encoding='utf-8')
        cairosvg.svg2png(bytestring=svg.encode('utf-8'), write_to=str(staging / 'art.png'))
        with Image.open(staging / 'art.png') as image:
            preview = Image.new('RGB', image.size, '#e4e8ee')
            preview.paste(image, (0, 0), image)
            preview.thumbnail((1200, 1200))
            preview.save(staging / 'art.preview.png')
        record = {
            'schema_version': 1,
            'canvas': size,
            'body_master_sha256': digest(master),
            'foreground_sha256': digest(foreground),
            'scene': {**scene, 'foreground': Path(scene['foreground']).name},
            'files': {},
        }
        for suffix in suffixes[:-1]:
            record['files'][suffix] = digest((staging / ('art' + suffix)).read_bytes())
        (staging / 'art.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        for suffix, target in targets.items():
            (staging / ('art' + suffix)).replace(target)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--example', type=int, choices=range(1, 23))
    source.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='Output basename without extension')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    config = args.config if args.config else ROOT / f'assets/examples/{args.example:02}.json'
    try:
        targets = render(config, args.output, args.force)
    except (ValueError, KeyError, OSError, RuntimeError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(json.dumps({key: str(value) for key, value in targets.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
