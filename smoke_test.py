"""End-to-end smoke test: every route renders and the open API behaves."""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoProject.settings")
django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

from sakura.models import Case, Girl, OwnedGirl, OpenLog, Player  # noqa: E402

setup_test_environment()
c = Client()
fails = []


def check(label, resp, expect=200):
    ok = resp.status_code == expect
    if not ok:
        fails.append(f"{label} -> {resp.status_code} (want {expect})")
    body = resp.content.decode("utf-8", "replace")
    if expect == 200 and len(body) < 400:
        fails.append(f"{label} -> suspiciously short body ({len(body)}b)")
    return body


case = Case.objects.first()
girl = Girl.objects.first()

# ---- pages ---------------------------------------------------------------
check("home", c.get("/"))
check("cases", c.get("/cases/"))
body = check(f"case detail {case.slug}", c.get(f"/case/{case.slug}/"))
assert "pool" in body, "roulette pool missing from case page"
check(f"girl {girl.slug}", c.get(f"/girl/{girl.slug}/"))
check("collection", c.get("/collection/"))
check("collection+rarity", c.get("/collection/?rarity=sakura"))
check("collection+element", c.get("/collection/?element=moon"))
check("collection+search", c.get("/collection/?q=%D1%81%D0%B0%D0%BA%D1%83"))
check("collection+missing", c.get("/collection/?owned=missing&sort=power"))
check("profile", c.get("/profile/"))
check("hall", c.get("/hall/"))
check("login", c.get("/login/"))
check("register", c.get("/register/"))
check("404 case", c.get("/case/nope/"), 404)

# ---- generated art -------------------------------------------------------
for key in ("sakura", "torii", "kitsune", "abyss", "neon", "origami", "frost", "moon", "koi"):
    r = c.get(f"/art/case/{key}.svg?a=%23ff8fb8&b=%23ffd6e7&s=3")
    if r.status_code != 200 or not r.content.startswith(b"<svg"):
        fails.append(f"art case {key} broken")
    if b"</svg>" not in r.content:
        fails.append(f"art case {key} truncated")
r = c.get("/art/avatar/1337.svg?accent=%23ff8fb8")
if r.status_code != 200 or b"</svg>" not in r.content:
    fails.append("art avatar broken")
r = c.get("/art/logo.svg")
if r.status_code != 200 or b"</svg>" not in r.content:
    fails.append("logo broken")

# ---- auth + opening ------------------------------------------------------
check("login post", c.post("/login/", {"username": "no_such_user", "password": "x"}), 200)

from django.contrib.auth.models import User  # noqa: E402

User.objects.filter(username="tester").delete()
c.post("/register/", {"username": "tester", "password1": "SakuraPass!2026", "password2": "SakuraPass!2026"})
p = Player.objects.get(user__username="tester")
print(f"  player after register: {p.petals} petals")

resp = c.post(f"/case/{case.slug}/open/", {"amount": "1"})
check("open x1", resp)
d = resp.json()
assert d["ok"], d
assert len(d["results"]) == 1
fresh = Player.objects.get(pk=p.pk)
assert fresh.petals == 3000 - case.price, (fresh.petals, case.price)
print(f"  x1  -> {d['results'][0]['name']} ({d['results'][0]['rarity']}), petals {d['petals']}")

cheap = Case.objects.order_by("price").first()
p.petals = 100000
p.save()
before = p.petals
resp = c.post(f"/case/{cheap.slug}/open/", {"amount": "10"})
d = resp.json()
assert d["ok"] and len(d["results"]) == 10, d
assert d["petals"] == before - cheap.price * 10
print(f"  x10 -> {len(d['results'])} pulls, spent {before - d['petals']}")

# empty wall
p.petals = 0
p.save()
resp = c.post(f"/case/{case.slug}/open/", {"amount": "1"})
if resp.status_code != 402:
    fails.append(f"insufficient funds should be 402, got {resp.status_code}")
else:
    print("  broke player -> 402 with reason:", resp.json()["error"])

# amount clamping
p.petals = 10_000_000
p.save()
d = c.post(f"/case/{case.slug}/open/", {"amount": "9999"}).json()
if len(d.get("results", [])) != 10:
    fails.append(f"amount not clamped to 10, got {len(d.get('results', []))}")

# ---- pity system ---------------------------------------------------------
top_case = Case.objects.filter(drops__girl__rarity="sakura").distinct().last()
p.petals = 10_000_000
p.pity_counter = 59
p.save()
hits = 0
counter_after_hit = None
for _ in range(6):
    d = c.post(f"/case/{top_case.slug}/open/", {"amount": "1"}).json()
    if d["results"][0]["rarity"] == "sakura":
        hits += 1
        counter_after_hit = d["pity"]
if hits == 0:
    fails.append("pity: no legendary forced within 6 pulls from 59")
else:
    print(f"  pity forced legendary {hits}/6 pulls from {top_case.name}; counter -> {counter_after_hit}")
    if counter_after_hit != 0:
        fails.append(f"pity counter was {counter_after_hit} right after a legendary, want 0")

# a case with no legendaries must never claim a guarantee
cheap_case = Case.objects.exclude(drops__girl__rarity="sakura").first()
if cheap_case:
    forced = 0
    for _ in range(30):
        d = c.post(f"/case/{cheap_case.slug}/open/", {"amount": "1"}).json()
        forced += d["results"][0]["rarity"] == "sakura"
    if forced:
        fails.append("case without legendaries produced one")
    else:
        print(f"  {cheap_case.name}: 30 pulls, 0 legends (as designed)")

# ---- pull payload reports the post-pull state ----------------------------
# a first pull must report is_new=True/count=1, a repeat is_new=False/count=2
OwnedGirl.objects.filter(player=p).delete()
p.petals = 500_000
p.save()
seen = {}
for _ in range(8):
    r = c.post(f"/case/{cheap_case.slug}/open/", {"amount": "1"}).json()["results"][0]
    seen.setdefault(r["name"], 0)
    seen[r["name"]] += 1
    if r["is_new"] != (seen[r["name"]] == 1) or r["count"] != seen[r["name"]]:
        fails.append(
            f"payload wrong for {r['name']}: is_new={r['is_new']} count={r['count']} (pull #{seen[r['name']]})"
        )
print(f"  pull payload consistent across {len(seen)} girls / 8 pulls")

# ---- collection bookkeeping ---------------------------------------------
owned = OwnedGirl.objects.filter(player=p)
print(f"  collection: {owned.count()} unique, {owned.aggregate(s=__import__('django.db.models', fromlist=['Sum']).Sum('count'))['s']} total copies")
if owned.count() < 2:
    fails.append("collection not growing")
if OpenLog.objects.filter(player=p).count() == 0:
    fails.append("no open history logged")

dupes = [o for o in OwnedGirl.objects.filter(player=p).values("girl_id").annotate(n=__import__("django.db.models", fromlist=["Count"]).Count("id")).filter(n__gt=1)]
print(f"  duplicate girls in wallet: {len(dupes)}")

# ---- template hygiene ----------------------------------------------------
for url in ("/", "/cases/", f"/case/{case.slug}/", "/collection/", "/profile/", "/hall/"):
    b = c.get(url).content.decode()
    for bad in ("{%", "{{", "}}", "None", "[]"):
        if bad in b:
            fails.append(f"{url}: leaked template artefact {bad!r}")

print()
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
    raise SystemExit(1)
print("ALL SMOKE TESTS PASSED")
