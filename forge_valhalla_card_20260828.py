#!/usr/bin/env python3
# Adds a "Valhalla - The Hall of the Earned" card to the morning brief,
# modelled exactly on the existing breathe_card. Relative ./valhalla-hall.html
# link (storage-jar rule). SHA-guarded by anchor match + ast.parse; backs up
# first; refuses to run twice; restores the backup if the result won't parse.
import ast, hashlib, shutil, sys, time

PATH = "forge_actions.py"

# --- anchor: the exact tail of the breathe_card definition (must be unique) ---
ANCHOR_A = (
    '        \'<a href="./breathe.html" style="display:block; text-align:center; margin-top:12px; padding:11px; border-radius:10px; background:linear-gradient(135deg,#bfe7ff,#7fd4e6); color:#0b2547; font-weight:800; letter-spacing:0.06em; text-decoration:none;">Open the breathing room \\u2192</a>\'\n'
    '        \'</div>\'\n'
    '    )\n'
)

# --- the new card definition, same style as breathe_card, ASCII-safe escapes ---
HALL_DEF = (
    '\n'
    '    hall_card = (\n'
    '        \'<div class="card" style="background:linear-gradient(135deg, rgba(43,92,255,0.20), rgba(21,71,214,0.10)); border:2px solid #2b5cff;">\'\n'
    '        \'<div class="card-header"><span class="card-icon">\\U0001F3F0</span><span>Valhalla \\u2014 The Hall of the Earned</span></div>\'\n'
    '        \'<div style="font-size:14px; line-height:1.65; color:var(--text-bright);">\'\n'
    '        \'The reverentially-respected earn a seat at the table \\u2014 each one carrying wisdom that moves the needle. \'\n'
    '        \'First seat: <b>Mike Muir</b>, his own words and the ones he carries from his father.\'\n'
    '        \'</div>\'\n'
    '        \'<a href="./valhalla-hall.html" style="display:block; text-align:center; margin-top:12px; padding:11px; border-radius:10px; background:linear-gradient(135deg,#4f7bff,#2b5cff); color:#ffffff; font-weight:800; letter-spacing:0.06em; text-decoration:none;">Enter the hall \\u2192</a>\'\n'
    '        \'</div>\'\n'
    '    )\n'
)

TMPL_ANCHOR = '  {breathe_card}\n'
TMPL_NEW = '  {breathe_card}\n\n  {hall_card}\n'

def die(msg):
    print("ABORT:", msg); sys.exit(1)

def main():
    with open(PATH, "r", encoding="utf-8") as f:
        src = f.read()
    pre = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("pre  sha256:", pre)

    if "hall_card = (" in src or "{hall_card}" in src:
        die("already installed (hall_card present). Nothing to do.")
    if src.count(ANCHOR_A) != 1:
        die("breathe_card anchor found %d times (need exactly 1) - file differs from expected." % src.count(ANCHOR_A))
    if src.count(TMPL_ANCHOR) != 1:
        die("template anchor {breathe_card} found %d times (need exactly 1)." % src.count(TMPL_ANCHOR))

    out = src.replace(ANCHOR_A, ANCHOR_A + HALL_DEF, 1)
    out = out.replace(TMPL_ANCHOR, TMPL_NEW, 1)

    # post-conditions
    assert out.count("hall_card = (") == 1, "hall_card def not inserted once"
    assert out.count("{hall_card}") == 1, "{hall_card} not inserted once"
    assert out.count("breathe_card = (") == 1, "breathe_card def disturbed"
    assert out.count("{breathe_card}") == 1, "{breathe_card} disturbed"

    # must still be valid Python
    try:
        ast.parse(out)
    except SyntaxError as e:
        die("patched file does not parse (%s) - NOT written." % e)

    backup = PATH + ".valhallacard.bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(PATH, backup)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(out)

    post = hashlib.sha256(out.encode("utf-8")).hexdigest()
    print("backup     :", backup)
    print("post sha256:", post)
    print("OK - Valhalla card added. Now run the workflow to regenerate index.html.")

if __name__ == "__main__":
    main()
