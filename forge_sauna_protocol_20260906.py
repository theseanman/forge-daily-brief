#!/usr/bin/env python3
"""
forge_sauna_protocol_20260906.py

Adds The Sauna Protocol to the Forge OS.

  Writes   : sauna.html      (NEW hand-maintained page, live on push, NO workflow)
  Edits    : protocols.html  (one card appended to Available protocols)
  New keys : forge-img-sauna -- LOCAL ONLY, device-bound, never synced.
             NOTHING to add to the Cloudflare allowlist.

  sauna.html SHA      : b80b5e64f9c303a1d2a2195c747504dbf4c9d2c072d0f9703bb103130abad546
  protocols.html pre  : 96b682428841aad77b74ce86db263210d5580924aaeb32311cc10f1acd658f64
  protocols.html post : 987811c9e5cd104140ef0d985bda2e358e90f2cb209840d23c684fb375c98dfb

Deliberately carries no streak, log or tally: the timer already records whether
the pre-set number was hit, and scoring the practice would reintroduce exactly
the self-monitoring it exists to remove.

Health claims are graded honestly and stay consistent with longevity.html, which
already calls sauna garnish rather than medicine. No claim on the page is graded
A, because none of the sauna evidence earns it.

Run from inside the repo, on gh-pages:
    python3 forge_sauna_protocol_20260906.py
"""
import base64, gzip, hashlib, os, shutil, sys
PAGE="sauna.html"; PROTO="protocols.html"
PAGE_SHA="b80b5e64f9c303a1d2a2195c747504dbf4c9d2c072d0f9703bb103130abad546"; PROTO_PRE="96b682428841aad77b74ce86db263210d5580924aaeb32311cc10f1acd658f64"; PROTO_POST="987811c9e5cd104140ef0d985bda2e358e90f2cb209840d23c684fb375c98dfb"
BACKUP="protocols.html.bak-sauna-20260906"
PAGE_B64="""
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
kpxgLT4AAA==
"""
ANCHOR_B64="""
H4sIALkbnmoC/32OwU4DMQxE73zFaA89FfoBu+QPkBBU4mwl7iYiiVHsgvr3uFUP7AWfxtbM8yyp
fCNWUn2evh47NZ7CMTOOeTDjRRp3U7wOMYlSl4PbwwPus2zCiTVO4SOXmPFZeoKcYLl01ysI7cZC
pFoVJxnYtUSaZ/cwVjLe4yLnAS12JivSFVQHU7pAZRinPcihhFRo7aJW4g1zjUtndUEGGowu9vRv
0ybedQrvjvUWJSWxGW/+apPaLhsAjSE/U9gNF/Mf33Kgq7hffgEGd7KIXAEAAA==
"""
CARD_B64="""
H4sIALkbnmoC/31QQU4DMQy89xVWDj2V3Qd0mzcg6Ae8iSGRkngVO13194QFVbQCfBp5ZjwjAwBM
CC6hyMkslZUdJwOh0tvJDKNgKzgEzcnYHWwz+Xi5GZ40tDwbO419+7tiZn+9mR/JgpmMPQeC188k
eP5ucHfv0eRJ3Jep9HCqEAWEFLipRE+gnanMGfbZo4Qj6MqwhIpCctjYFAvBTLoSFSgchQCLB4nv
BdNhw2tA3bSBOqBLP1xclzltmNIVpC0LV5Xh36qZe1ljXwj9/Yv+/hfWyqux+9rB8YduGtHuPgBT
PEAJsAEAAA==
"""
def unpack(b): return gzip.decompress(base64.b64decode("".join(b.split()))).decode("utf-8")
def die(m):
    print("ABORT: "+m); print("Nothing was written."); sys.exit(1)
def main():
    force="--force" in sys.argv
    if not os.path.exists(PROTO): die(PROTO+" not found. Run from inside the repo.")
    if os.path.exists(PAGE) and not force:
        cur=hashlib.sha256(open(PAGE,encoding="utf-8").read().encode("utf-8")).hexdigest()
        if cur==PAGE_SHA: die(PAGE+" already exists and is identical. Nothing to do.")
        die(PAGE+" already exists and differs. Re-run with --force to overwrite.")
    page=unpack(PAGE_B64); anchor=unpack(ANCHOR_B64); card=unpack(CARD_B64)
    if hashlib.sha256(page.encode("utf-8")).hexdigest()!=PAGE_SHA:
        die("carried page failed its integrity check.")
    print("  ok  page payload intact")
    src=open(PROTO,encoding="utf-8").read()
    pre=hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("protocols.html pre-image : "+pre)
    if pre==PROTO_POST: die("the Sauna card is already in "+PROTO+".")
    if pre!=PROTO_PRE:
        die("protocols.html does not match its pre-image. Expected "+PROTO_PRE+".\n       Rebuild - do not force.")
    if "sauna.html" in src: die("a sauna link is already present in "+PROTO+".")
    if src.count(anchor)!=1:
        die("anchor matched "+str(src.count(anchor))+" times, expected 1.")
    print("  ok  anchor unique")
    out=src.replace(anchor, anchor.replace("</a>\n  </div>\n","</a>\n"+card+"  </div>\n"),1)
    checks=[("card count 14 -> 15", src.count('<a class="protocol')==14 and out.count('<a class="protocol')==15),
            ("new card sits after four-moments", out.index("sauna.html")>out.index("four-moments.html")),
            ("every existing protocol link survives",
                all(h in out for h in ["morning.html","evening.html","getting-paid.html","charisma.html",
                                       "posture-reset.html","capital.html","fantasy.html","longevity.html",
                                       "sleep.html","selfdefense.html","resilience.html",
                                       "mental-strength.html","second-nature.html","four-moments.html"])),
            ("div balance unchanged", out.count("<div")-out.count("</div>")==src.count("<div")-src.count("</div>")),
            ("anchor tag balance", out.count("<a class=")==out.count("</a>")),
            ("page carries no sync url", "forge-sync" not in page),
            ("both phrases present", "The timer decides." in page and "Not relevant. Skin, breath, count." in page),
            ("reuses the existing cue, not a new one", "Noise. Skin, breath, count." not in page),
            ("scope boundary stated", "NEVER on the second" in page and "load-bearing" in page),
            ("safety line present", "Words are noise. Body is signal." in page),
            ("no streak or tally", "No streak, no log, no tally" in page),
            ("stays consistent with longevity", "garnish, not medicine" in page),
            ("no A grade claimed", 'ev a' not in page)]
    for n,p in checks:
        if not p: die("post-check failed: "+n)
        print("  ok  "+n)
    post=hashlib.sha256(out.encode("utf-8")).hexdigest()
    if post!=PROTO_POST: die("protocols.html post-image is "+post+", expected "+PROTO_POST+".")
    print("  ok  protocols.html post-image SHA matches")
    shutil.copy2(PROTO,BACKUP); open(PROTO,"w",encoding="utf-8").write(out)
    if hashlib.sha256(open(PROTO,encoding="utf-8").read().encode("utf-8")).hexdigest()!=PROTO_POST:
        shutil.copy2(BACKUP,PROTO); die("protocols.html bytes wrong. Restored from "+BACKUP+".")
    open(PAGE,"w",encoding="utf-8").write(page)
    if hashlib.sha256(open(PAGE,encoding="utf-8").read().encode("utf-8")).hexdigest()!=PAGE_SHA:
        die(PAGE+" bytes wrong after write. Restore "+PROTO+" from "+BACKUP+".")
    print("  ok  "+PAGE+" written and verified")
    print(""); print("WRITTEN   : "+PAGE+" (new, "+str(len(page))+" chars)")
    print("UPDATED   : "+PROTO); print("BACKUP    : "+BACKUP)
    print(""); print("Both hand-maintained. Commit and push - NO workflow run, NO Cloudflare paste.")
if __name__=="__main__": main()
