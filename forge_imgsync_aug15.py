#!/usr/bin/env python3
"""
forge_imgsync_aug15.py  -  cloud backup + restore for the three Paramount Protocol
images (Terrain / Tempo / Presence).

WHAT IT DOES (patches forge_actions.py, the GENERATOR -> needs a workflow run):
  1. After a successful local image save, pushes the image to the forge-sync Worker
     under its existing key (forge-img-terrain / -tempo / -presence). A FAILED backup
     shows a visible note - it never lies about success.
  2. On page load, for any image slot that is EMPTY locally but present in the cloud,
     restores it and repaints. A present local image is NEVER overwritten.

SAFETY:
  - Refuses to run unless forge_actions.py matches the expected PRE hash.
  - Backs up the original before writing; restores it on any post-check failure.
  - Second run refuses (PRE hash no longer matches) - cannot double-apply.

REQUIRES ONE CLOUDFLARE PASTE FIRST/ALONGSIDE: the three forge-img-* keys must be
added to the forge-sync Worker KEYS allowlist or the push returns 400 and the note
shows the failure (image still saved locally - no data loss, just no backup yet).
"""
import hashlib, sys, os, subprocess, tempfile, datetime

TARGET   = "forge_actions.py"
PRE_SHA  = "c7f073796546143f8d2437e24c83ef49f4d3e96c8c596bbd4521a8dece5c19c2"

# ---- anchors (each must occur EXACTLY once) ----------------------------------
A_OLD = (
"  var n2 = document.getElementById('pimg-note');\n"
"  if (n2) n2.textContent = '';\n"
"  pimgPaint();\n"
"}}"
)
A_NEW = (
"  var n2 = document.getElementById('pimg-note');\n"
"  if (n2) n2.textContent = '';\n"
"  pimgPaint();\n"
"  pimgPush(slot, dataUrl);\n"
"}}"
)

# two new functions inserted immediately before pimgLoad
B_OLD = "function pimgLoad(ev) {{"
B_NEW = (
"function pimgPush(slot, dataUrl) {{\n"
"  try {{\n"
"    fetch(SYNC_URL + '/' + encodeURIComponent(pimgKey(slot)), {{\n"
"      method: 'PUT', headers: {{ 'Content-Type': 'application/json' }},\n"
"      body: JSON.stringify(dataUrl)\n"
"    }}).then(function(r) {{\n"
"      var n = document.getElementById('pimg-note');\n"
"      if (!r.ok && n) n.textContent = 'Saved on this device - cloud backup failed (' + r.status + ').';\n"
"    }}).catch(function() {{\n"
"      var n = document.getElementById('pimg-note');\n"
"      if (n) n.textContent = 'Saved on this device - cloud backup offline.';\n"
"    }});\n"
"  }} catch(e) {{}}\n"
"}}\n"
"function pimgPull() {{\n"
"  for (var i = 0; i < PIMG_SLOTS.length; i++) {{\n"
"    (function(k) {{\n"
"      var haveLocal = false;\n"
"      try {{ haveLocal = !!localStorage.getItem(pimgKey(k)); }} catch(e) {{}}\n"
"      if (haveLocal) return;\n"
"      fetch(SYNC_URL + '/' + encodeURIComponent(pimgKey(k)))\n"
"        .then(function(r) {{ if (!r.ok) throw new Error(r.status); return r.json(); }})\n"
"        .then(function(v) {{\n"
"          if (typeof v === 'string' && v.indexOf('data:image') === 0) {{\n"
"            var still = false;\n"
"            try {{ still = !!localStorage.getItem(pimgKey(k)); }} catch(e) {{}}\n"
"            if (still) return;\n"
"            try {{ localStorage.setItem(pimgKey(k), v); pimgPaint(); }} catch(e) {{}}\n"
"          }}\n"
"        }})\n"
"        .catch(function() {{}});\n"
"    }})(PIMG_SLOTS[i]);\n"
"  }}\n"
"}}\n"
"function pimgLoad(ev) {{"
)

C_OLD = "  pimgPaint(); setInterval(tick, 1000);"
C_NEW = "  pimgPaint(); pimgPull(); setInterval(tick, 1000);"

def die(msg):
    print("ABORT:", msg); sys.exit(1)

def main():
    if not os.path.exists(TARGET):
        die(f"{TARGET} not found - run this from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, "r", encoding="utf-8").read()
    got = hashlib.sha256(orig.encode("utf-8")).hexdigest()
    if got != PRE_SHA:
        die(f"{TARGET} PRE hash mismatch.\n  expected {PRE_SHA}\n  got      {got}\n"
            "This installer targets the current live generator only. Do not force it.")
    for name, old in [("A", A_OLD), ("B", B_OLD), ("C", C_OLD)]:
        c = orig.count(old)
        if c != 1:
            die(f"anchor {name} found {c} times (expected 1) - refusing to guess")
    new = orig.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW).replace(C_OLD, C_NEW)

    # write backup
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.imgsync.bak-{stamp}"
    open(bak, "w", encoding="utf-8").write(orig)

    open(TARGET, "w", encoding="utf-8").write(new)

    def restore(why):
        open(TARGET, "w", encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored from memory, backup at {bak}")

    # post-check 1: python still compiles
    r = subprocess.run([sys.executable, "-m", "py_compile", TARGET], capture_output=True, text=True)
    if r.returncode != 0:
        restore("py_compile: " + r.stderr.strip()[:300])

    # post-check 2: markers present
    for marker in ("function pimgPush(", "function pimgPull(",
                   "pimgPush(slot, dataUrl);", "pimgPaint(); pimgPull(); setInterval"):
        if marker not in new:
            restore(f"marker missing: {marker}")

    post = hashlib.sha256(new.encode("utf-8")).hexdigest()
    print("OK  forge_actions.py patched.")
    print("    backup :", bak)
    print("    PRE    :", PRE_SHA)
    print("    POST   :", post)
    print("    bytes  :", len(orig.encode()), "->", len(new.encode()))
    print("\nNext: git pull --rebase ; stage forge_actions.py + this installer ; commit ; push ; run the workflow.")

if __name__ == "__main__":
    main()
