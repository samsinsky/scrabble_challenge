#!/usr/bin/env python3
"""
Scrabble Board Generator and Renderer - Muth Test Challenge
Generates a valid Scrabble board with all 100 tiles placed,
then renders it as a high-resolution image.
"""

import os
import random
import math
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

GRID = 15

TILE_DIST = {
    'A': (9, 1), 'B': (2, 3), 'C': (2, 3), 'D': (4, 2),
    'E': (12, 1), 'F': (2, 4), 'G': (3, 2), 'H': (2, 4),
    'I': (9, 1), 'J': (1, 8), 'K': (1, 5), 'L': (4, 1),
    'M': (2, 3), 'N': (6, 1), 'O': (8, 1), 'P': (2, 3),
    'Q': (1, 10), 'R': (6, 1), 'S': (4, 1), 'T': (6, 1),
    'U': (4, 1), 'V': (2, 4), 'W': (2, 4), 'X': (1, 8),
    'Y': (2, 4), 'Z': (1, 10), '_': (2, 0),
}
POINTS = {ch: v for ch, (_, v) in TILE_DIST.items()}

# 0=normal, 1=DL, 2=DW, 3=TL, 4=TW, 5=center star
SQUARE_MAP = [
    [4,0,0,1,0,0,0,4,0,0,0,1,0,0,4],
    [0,2,0,0,0,3,0,0,0,3,0,0,0,2,0],
    [0,0,2,0,0,0,1,0,1,0,0,0,2,0,0],
    [1,0,0,2,0,0,0,1,0,0,0,2,0,0,1],
    [0,0,0,0,2,0,0,0,0,0,2,0,0,0,0],
    [0,3,0,0,0,3,0,0,0,3,0,0,0,3,0],
    [0,0,1,0,0,0,1,0,1,0,0,0,1,0,0],
    [4,0,0,1,0,0,0,5,0,0,0,1,0,0,4],
    [0,0,1,0,0,0,1,0,1,0,0,0,1,0,0],
    [0,3,0,0,0,3,0,0,0,3,0,0,0,3,0],
    [0,0,0,0,2,0,0,0,0,0,2,0,0,0,0],
    [1,0,0,2,0,0,0,1,0,0,0,2,0,0,1],
    [0,0,2,0,0,0,1,0,1,0,0,0,2,0,0],
    [0,2,0,0,0,3,0,0,0,3,0,0,0,2,0],
    [4,0,0,1,0,0,0,4,0,0,0,1,0,0,4],
]

SQUARE_LABELS = {
    0: None,
    1: ['DOUBLE', 'LETTER', 'SCORE'],
    2: ['DOUBLE', 'WORD', 'SCORE'],
    3: ['TRIPLE', 'LETTER', 'SCORE'],
    4: ['TRIPLE', 'WORD', 'SCORE'],
    5: None,  # star drawn separately
}

# Official two-letter Scrabble words
TWO_LETTER = {
    'AA','AB','AD','AE','AG','AH','AI','AL','AM','AN','AR','AS','AT','AW','AX','AY',
    'BA','BE','BI','BO','BY','DA','DE','DO',
    'ED','EF','EH','EL','EM','EN','ER','ES','ET','EW','EX',
    'FA','FE','GI','GO','HA','HE','HI','HM','HO',
    'ID','IF','IN','IS','IT','JO','KA','KI','LA','LI','LO',
    'MA','ME','MI','MM','MO','MU','MY',
    'NA','NE','NO','NU',
    'OD','OE','OF','OH','OI','OK','OM','ON','OO','OP','OR','OS','OW','OX','OY',
    'PA','PE','PI','PO','QI','RE','SH','SI','SO',
    'TA','TI','TO','UH','UM','UN','UP','US','UT',
    'WE','WO','XI','YA','YE','YO','ZA',
}

# ============================================================
# WORD LIST
# ============================================================

def load_word_list(max_len=10):
    """Load word list from TWL06 (official North American Scrabble dictionary)."""
    words = set(TWO_LETTER)
    # Use TWL06 dictionary (Tournament Word List, North American Scrabble)
    twl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'twl06.txt')
    if os.path.exists(twl_path):
        with open(twl_path) as f:
            for line in f:
                w = line.strip().upper()
                if 2 <= len(w) <= max_len and w.isalpha():
                    words.add(w)
    else:
        raise FileNotFoundError(
            f"TWL06 dictionary not found at {twl_path}. "
            "Please ensure twl06.txt is in the same directory as this script."
        )
    return words


# ============================================================
# BOARD
# ============================================================

class Board:
    def __init__(self):
        self.grid = [[None]*GRID for _ in range(GRID)]
        self.blanks = set()
        self.bag = {ch: cnt for ch, (cnt, _) in TILE_DIST.items() if ch != '_'}
        self.blank_count = 2

    def place(self, r, c, letter, is_blank=False):
        if not (0 <= r < GRID and 0 <= c < GRID):
            return
        self.grid[r][c] = letter
        if is_blank:
            self.blanks.add((r, c))
            self.blank_count -= 1
        else:
            self.bag[letter] -= 1

    def get(self, r, c):
        return self.grid[r][c] if 0 <= r < GRID and 0 <= c < GRID else None

    def tiles_remaining(self):
        return sum(self.bag.values()) + self.blank_count

    def count_tiles(self):
        return sum(1 for r in range(GRID) for c in range(GRID) if self.grid[r][c] is not None)

    def get_all_words(self):
        words = []
        for r in range(GRID):
            c = 0
            while c < GRID:
                if self.grid[r][c]:
                    s = c
                    w = ''
                    while c < GRID and self.grid[r][c]:
                        w += self.grid[r][c]; c += 1
                    if len(w) >= 2: words.append(('H', r, s, w))
                else: c += 1
        for c in range(GRID):
            r = 0
            while r < GRID:
                if self.grid[r][c]:
                    s = r
                    w = ''
                    while r < GRID and self.grid[r][c]:
                        w += self.grid[r][c]; r += 1
                    if len(w) >= 2: words.append(('V', s, c, w))
                else: r += 1
        return words

    def validate(self, word_set):
        invalid = [(d,r,c,w) for d,r,c,w in self.get_all_words() if w not in word_set]
        lc = Counter()
        bc = 0
        for r in range(GRID):
            for c in range(GRID):
                if self.grid[r][c]:
                    if (r,c) in self.blanks: bc += 1
                    else: lc[self.grid[r][c]] += 1
        errs = []
        for ch, (exp, _) in TILE_DIST.items():
            if ch == '_':
                if bc != exp: errs.append(f'Blank: expected {exp}, got {bc}')
            else:
                act = lc.get(ch, 0)
                if act != exp: errs.append(f'{ch}: expected {exp}, got {act}')
        return invalid, errs

    def print_board(self):
        print('    ' + ' '.join(f'{c:2d}' for c in range(GRID)))
        for r in range(GRID):
            s = f'{r:2d}: '
            for c in range(GRID):
                ch = self.grid[r][c]
                if ch is None: s += ' . '
                elif (r,c) in self.blanks: s += f' {ch.lower()} '
                else: s += f' {ch} '
            print(s)


# ============================================================
# CROSSWORD GENERATOR
# ============================================================

class Generator:
    def __init__(self, word_set):
        self.ws = word_set
        self.board = Board()
        self.idx = {}
        for w in word_set:
            l = len(w)
            for i, ch in enumerate(w):
                k = (l, i, ch)
                if k not in self.idx: self.idx[k] = []
                self.idx[k].append(w)

    def cross_word(self, r, c, d, ch):
        """Get cross-word formed perpendicular to d when placing ch at (r,c)."""
        b = self.board
        if d == 'H':
            t, bt = r, r
            while t > 0 and b.get(t-1, c): t -= 1
            while bt < GRID-1 and b.get(bt+1, c): bt += 1
            if t == bt: return None
            return ''.join(ch if rr == r else b.get(rr, c) for rr in range(t, bt+1))
        else:
            l, rt = c, c
            while l > 0 and b.get(r, l-1): l -= 1
            while rt < GRID-1 and b.get(r, rt+1): rt += 1
            if l == rt: return None
            return ''.join(ch if cc == c else b.get(r, cc) for cc in range(l, rt+1))

    def find_plays(self, r, c, d):
        b = self.board
        ch = b.get(r, c)
        if not ch: return []
        plays = []
        for wl in range(2, 11):  # Max word length 10
            for pos in range(wl):
                if d == 'H':
                    sc = c - pos; ec = sc + wl - 1
                    if sc < 0 or ec >= GRID: continue
                    if sc > 0 and b.get(r, sc-1): continue
                    if ec < GRID-1 and b.get(r, ec+1): continue
                    pat = []; npos = []
                    for i in range(wl):
                        ex = b.get(r, sc+i)
                        pat.append(ex);
                        if ex is None: npos.append((i, r, sc+i))
                else:
                    sr = r - pos; er = sr + wl - 1
                    if sr < 0 or er >= GRID: continue
                    if sr > 0 and b.get(sr-1, c): continue
                    if er < GRID-1 and b.get(er+1, c): continue
                    pat = []; npos = []
                    for i in range(wl):
                        ex = b.get(sr+i, c)
                        pat.append(ex)
                        if ex is None: npos.append((i, sr+i, c))
                if not npos: continue
                for w in self.idx.get((wl, pos, ch), []):
                    ok = all(pat[i] is None or w[i] == pat[i] for i in range(wl))
                    if not ok: continue
                    need = Counter(w[i] for i, _, _ in npos)
                    bn = sum(max(0, cnt - b.bag.get(c2, 0)) for c2, cnt in need.items())
                    if bn > b.blank_count: continue
                    xok = all(
                        (cw := self.cross_word(rr, cc, d, w[i])) is None or cw in self.ws
                        for i, rr, cc in npos
                    )
                    if not xok: continue
                    plays.append({'word': w, 'row': sr if d=='V' else r,
                                  'col': sc if d=='H' else c, 'dir': d,
                                  'need': need, 'bn': bn, 'nc': len(npos)})
        return plays

    def score(self, p):
        s = p['nc'] * 10 + len(p['word']) * 2 - p['bn'] * 100
        rare = {'J':50,'K':30,'Q':50,'X':40,'Z':50,'V':15,'W':10}
        for ch, cnt in p['need'].items(): s += rare.get(ch, 0) * cnt
        return s + random.random() * 3

    def execute(self, p):
        b = self.board
        w, r, c, d = p['word'], p['row'], p['col'], p['dir']
        for i, ch in enumerate(w):
            rr = r + (i if d == 'V' else 0)
            cc = c + (i if d == 'H' else 0)
            if b.get(rr, cc) is None:
                if b.bag.get(ch, 0) > 0: b.place(rr, cc, ch)
                else: b.place(rr, cc, ch, is_blank=True)

    def generate(self, seed=20251213):
        random.seed(seed)
        b = self.board
        # Find good starting words through center
        cands = []
        for wl in range(5, 11):
            for pos in range(wl):
                sc = 7 - pos
                if sc < 0 or sc + wl - 1 >= GRID:
                    continue
                for ch in 'AEIOURSTLN':
                    for w in self.idx.get((wl, pos, ch), []):
                        need = Counter(w)
                        if all(b.bag.get(c2,0) >= cnt for c2, cnt in need.items()):
                            rare = sum(1 for c2 in w if c2 in 'JKQXZVW')
                            cands.append((rare, len(w), w, pos))
        cands.sort(reverse=True)
        best_board, best_n = None, 0
        for att in range(min(20, len(cands))):
            _, _, sw, pos = cands[att]
            self.board = Board(); b = self.board
            sc = 7 - pos
            if sc < 0 or sc + len(sw) - 1 >= GRID:
                continue
            for i, ch in enumerate(sw): b.place(7, sc+i, ch)
            print(f'  Try {att+1}: "{sw}" at col {sc}')
            for _ in range(800):
                if b.tiles_remaining() == 0: break
                all_p = []
                seen = set()
                for r in range(GRID):
                    for c in range(GRID):
                        if b.get(r, c):
                            for d in ['H', 'V']:
                                for p in self.find_plays(r, c, d):
                                    k = (p['word'], p['row'], p['col'], p['dir'])
                                    if k not in seen: seen.add(k); all_p.append(p)
                if not all_p: break
                nb = [p for p in all_p if p['bn'] == 0]
                if nb: all_p = nb
                all_p.sort(key=self.score, reverse=True)
                self.execute(all_p[0])
            n = b.count_tiles()
            print(f'    → {n}/100 tiles')
            if n > best_n: best_n = n; best_board = b
            if n == 100: break
        self.board = best_board
        return self.board


# ============================================================
# RENDERER
# ============================================================

class Renderer:
    # True-to-life Scrabble board colors
    BG = (26, 96, 52)              # Dark green felt/board
    SQ_COLORS = {
        0: (222, 201, 162),         # Beige normal
        1: (162, 206, 226),         # Light blue - DL
        2: (224, 164, 164),         # Pink - DW
        3: (42, 100, 170),          # Dark blue - TL
        4: (180, 36, 36),           # Red - TW
        5: (224, 164, 164),         # Center (same as DW)
    }
    LABEL_COLORS = {
        0: (0,0,0),
        1: (18, 55, 110),           # Dark blue text on light blue
        2: (145, 35, 35),           # Dark red text on pink
        3: (230, 238, 255),         # White text on dark blue
        4: (255, 240, 240),         # White text on red
        5: (145, 35, 35),
    }
    TILE_FACE = (237, 214, 168)     # Light maple
    TILE_HI = (248, 236, 205)       # Highlight edge
    TILE_LO = (192, 164, 118)       # Shadow edge
    BLACK = (22, 22, 22)

    def __init__(self, board):
        self.board = board

    def _fonts(self, sq):
        paths_b = ['/System/Library/Fonts/Supplemental/Georgia Bold.ttf',
                    '/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf']
        paths_r = ['/System/Library/Fonts/Supplemental/Georgia.ttf',
                    '/System/Library/Fonts/Supplemental/Times New Roman.ttf']
        bp = next((p for p in paths_b if os.path.exists(p)), None)
        rp = next((p for p in paths_r if os.path.exists(p)), None)
        def mk(path, sz):
            return ImageFont.truetype(path, sz) if path else ImageFont.load_default()
        self.f_letter = mk(bp, int(sq * 0.50))
        self.f_pts = mk(bp, int(sq * 0.19))
        self.f_label = mk(bp, int(sq * 0.125))
        self.f_label_s = mk(rp or bp, int(sq * 0.105))
        self.f_star = mk(bp, int(sq * 0.50))

    def render(self, path, size=8192):
        board = self.board
        margin = int(size * 0.032)
        sq = (size - 2 * margin) // GRID
        bsz = sq * GRID
        total = bsz + 2 * margin
        self._fonts(sq)
        gap = max(3, sq // 40)   # thicker grid lines

        img = Image.new('RGB', (total, total), self.BG)
        draw = ImageDraw.Draw(img)

        # Draw each square
        for r in range(GRID):
            for c in range(GRID):
                x0 = margin + c * sq
                y0 = margin + r * sq

                st = SQUARE_MAP[r][c]
                col = self.SQ_COLORS[st]

                # Square background with slight 3D inset
                inner = gap
                draw.rectangle([x0+inner, y0+inner, x0+sq-inner, y0+sq-inner], fill=col)

                # Subtle inner border for depth
                ib = max(1, gap // 2)
                # top/left lighter
                for i in range(ib):
                    c1 = tuple(min(255, v + 20) for v in col)
                    draw.line([(x0+inner+i, y0+inner+i), (x0+sq-inner-i, y0+inner+i)], fill=c1)
                    draw.line([(x0+inner+i, y0+inner+i), (x0+inner+i, y0+sq-inner-i)], fill=c1)
                # bottom/right darker
                for i in range(ib):
                    c2 = tuple(max(0, v - 25) for v in col)
                    draw.line([(x0+inner+i, y0+sq-inner-i), (x0+sq-inner-i, y0+sq-inner-i)], fill=c2)
                    draw.line([(x0+sq-inner-i, y0+inner+i), (x0+sq-inner-i, y0+sq-inner-i)], fill=c2)

                if board.grid[r][c] is not None:
                    self._tile(draw, x0, y0, sq, inner, r, c)
                else:
                    self._label(draw, x0+inner, y0+inner, sq-2*inner, st, r, c)

        # Board outer border with 3D effect
        bw = max(6, sq // 15)
        for i in range(bw):
            f = i / bw
            cr = int(18 + f * 15)
            cg = int(70 + f * 20)
            cb = int(40 + f * 10)
            draw.rectangle([margin-bw+i, margin-bw+i,
                            margin+bsz+bw-i, margin+bsz+bw-i],
                           outline=(cr, cg, cb))

        img.save(path, 'PNG', quality=100)
        print(f'Saved {path} ({total}x{total}px)')

    def _tile(self, draw, x, y, sq, gap, r, c):
        """Draw a photorealistic wooden tile with beveled edges."""
        inset = max(4, sq // 16)
        tx = x + gap + inset
        ty = y + gap + inset
        tw = sq - 2 * gap - 2 * inset
        bev = max(4, tw // 12)
        rad = max(2, tw // 30)  # corner rounding

        # Cast shadow (offset down-right, slightly transparent effect via darker color)
        shd = max(2, bev // 2)
        draw.rounded_rectangle([tx+shd, ty+shd, tx+tw+shd, ty+tw+shd],
                                radius=rad, fill=(140, 115, 75))

        # Outer bevel ring - dark bottom/right
        draw.rounded_rectangle([tx, ty, tx+tw, ty+tw],
                                radius=rad, fill=self.TILE_LO)

        # Light bevel top/left
        draw.rounded_rectangle([tx, ty, tx+tw-bev, ty+tw-bev],
                                radius=rad, fill=self.TILE_HI)

        # Main face
        draw.rounded_rectangle([tx+bev, ty+bev, tx+tw-bev, ty+tw-bev],
                                radius=max(1, rad-1), fill=self.TILE_FACE)

        # Subtle grain highlight band near top
        gh = max(1, bev // 2)
        draw.rectangle([tx+bev+gh, ty+bev+gh, tx+tw-bev-gh, ty+bev+gh*4],
                        fill=(242, 225, 188))

        letter = self.board.grid[r][c]
        is_blank = (r, c) in self.board.blanks

        if not is_blank:
            # Letter: centered horizontally, shifted up slightly
            bb = self.f_letter.getbbox(letter)
            lw, lh = bb[2] - bb[0], bb[3] - bb[1]
            lx = tx + (tw - lw) // 2
            ly = ty + int(tw * 0.12)
            draw.text((lx, ly), letter, fill=self.BLACK, font=self.f_letter)

            # Point value: southeast corner
            pts = str(POINTS.get(letter, 0))
            pb = self.f_pts.getbbox(pts)
            pw, ph = pb[2] - pb[0], pb[3] - pb[1]
            px = tx + tw - bev - pw - int(tw * 0.06)
            py = ty + tw - bev - ph - int(tw * 0.03)
            draw.text((px, py), pts, fill=self.BLACK, font=self.f_pts)

    def _label(self, draw, x, y, w, st, r, c):
        """Draw label on uncovered special squares."""
        if st == 5:
            # Center star
            star = '\u2605'
            bb = self.f_star.getbbox(star)
            sw, sh = bb[2] - bb[0], bb[3] - bb[1]
            sx = x + (w - sw) // 2
            sy = y + int(w * 0.05)
            draw.text((sx, sy), star, fill=self.LABEL_COLORS[5], font=self.f_star)
            # Label below star
            font = self.f_label_s
            color = self.LABEL_COLORS[5]
            labels = ['DOUBLE', 'WORD', 'SCORE']
            start_y = y + int(w * 0.58)
            for line in labels:
                bb2 = font.getbbox(line)
                lw2 = bb2[2] - bb2[0]
                draw.text((x + (w - lw2) // 2, start_y), line, fill=color, font=font)
                start_y += int(w * 0.12)
            return

        labels = SQUARE_LABELS.get(st)
        if not labels:
            return

        color = self.LABEL_COLORS[st]
        font = self.f_label

        # Measure all lines
        heights, widths = [], []
        for line in labels:
            bb = font.getbbox(line)
            widths.append(bb[2] - bb[0])
            heights.append(bb[3] - bb[1])

        sp = int(w * 0.04)
        total_h = sum(heights) + sp * (len(labels) - 1)
        sy = y + (w - total_h) // 2

        for i, line in enumerate(labels):
            lx = x + (w - widths[i]) // 2
            draw.text((lx, sy), line, fill=color, font=font)
            sy += heights[i] + sp


# ============================================================
# MAIN
# ============================================================

def main():
    print('Loading words...')
    ws = load_word_list(max_len=10)
    print(f'  {len(ws)} words')

    print('Generating board...')
    gen = Generator(ws)
    board = gen.generate(seed=20251213)

    print(f'\nBoard ({board.count_tiles()}/100):')
    board.print_board()

    print('\nValidating...')
    inv, errs = board.validate(ws)
    if inv:
        print(f'  INVALID words ({len(inv)}):')
        for d,r,c,w in inv: print(f'    {d}({r},{c}): {w}')
    else: print('  All words valid!')
    if errs:
        for e in errs: print(f'  {e}')
    else: print('  Tile counts correct!')

    print('\nWords:')
    for d,r,c,w in board.get_all_words():
        print(f'  {d}({r},{c}): {w}')

    print('\nRendering...')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scrabble_board.png')
    Renderer(board).render(out, size=8192)
    print('Done!')

if __name__ == '__main__':
    main()
