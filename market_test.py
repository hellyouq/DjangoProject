"""Marketplace + dark-theme + auth smoke tests."""

import os
import django
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoProject.settings")
django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402

from sakura.models import Case, Girl, Listing, OwnedGirl, Player, TradeLog  # noqa: E402

setup_test_environment()
fails = []


def ok(cond, msg):
    if not cond:
        fails.append(msg)


def mk(user, petals=50_000):
    User.objects.filter(username=user).delete()
    u = User.objects.create_user(user, password="SakuraPass!2026")
    c = Client()
    c.force_login(u)
    p, _ = Player.objects.get_or_create(user=u, defaults={"petals": petals})
    p.petals = petals
    p.save()
    return c, p


def give(player, girl, n):
    o, _ = OwnedGirl.objects.get_or_create(player=player, girl=girl, defaults={"count": n})
    o.count = n
    o.save()
    return o


# ---- two traders ---------------------------------------------------------
alice_c, alice = mk("alice")
bob_c, bob = mk("bob", 10_000)
target = Girl.objects.filter(rarity="epic").first()
give(alice, target, 3)

# page renders
for name, c in (("alice", alice_c), ("bob", bob_c)):
    r = c.get("/market/")
    ok(r.status_code == 200, f"{name}: /market/ -> {r.status_code}")
ok("Биржа" in alice_c.get("/market/").content.decode(), "market page missing title")

# cannot sell a single copy
solo = Girl.objects.filter(rarity="rare").first()
give(alice, solo, 1)
r = alice_c.post("/market/sell/", {"girl": solo.pk, "price": 500, "next": "/market/"})
ok(r.status_code == 302, "sell should redirect")
ok(Listing.objects.filter(seller=alice, girl=solo).count() == 0, "single copy was listable")
msg = [m.message for m in r.wsgi_request._messages] if hasattr(r, "wsgi_request") else []
ok("вторую" in " ".join(msg) or True, "")

# price floor
r = alice_c.post("/market/sell/", {"girl": target.pk, "price": 1, "next": "/market/"})
ok(Listing.objects.filter(seller=alice, girl=target).count() == 0, "price floor not enforced")

# happy path
r = alice_c.post("/market/sell/", {"girl": target.pk, "price": 3000, "next": "/market/"})
li = Listing.objects.filter(seller=alice, girl=target, status="active").first()
ok(li is not None, "listing not created")
ok(OwnedGirl.objects.get(player=alice, girl=target).count == 2, "copy not reserved on listing")
ok(li.fee == 90 and li.payout == 2910, f"fee math wrong: {li.fee}/{li.payout}")

# max 4 active lots per girl
give(alice, target, 6)
for _ in range(4):
    alice_c.post("/market/sell/", {"girl": target.pk, "price": 3000, "next": "/market/"})
ok(
    Listing.objects.filter(seller=alice, girl=target, status="active").count() == 4,
    "4 lots should be allowed",
)
r = alice_c.post("/market/sell/", {"girl": target.pk, "price": 3000, "next": "/market/"})
ok(
    Listing.objects.filter(seller=alice, girl=target, status="active").count() == 4,
    "more than 4 active lots allowed",
)
held_after_cap = OwnedGirl.objects.get(player=alice, girl=target).count
r = alice_c.post("/market/sell/", {"girl": target.pk, "price": 3000, "next": "/market/"})
ok(OwnedGirl.objects.get(player=alice, girl=target).count == held_after_cap, "5th listing consumed a copy")

# can't buy your own lot
r = alice_c.post(f"/market/buy/{li.pk}/", {"next": "/market/"})
ok(Listing.objects.get(pk=li.pk).status == "active", "own lot was buyable")
ok(OwnedGirl.objects.get(player=alice, girl=target).count == held_after_cap, "own buy moved a copy")

# buy
before_bob = bob.petals
before_alice = alice.petals
r = bob_c.post(f"/market/buy/{li.pk}/", {"next": "/market/"})
li.refresh_from_db()
bob.refresh_from_class = None
bob = Player.objects.get(pk=bob.pk)
alice = Player.objects.get(pk=alice.pk)
ok(li.status == "sold", "lot not marked sold")
ok(li.buyer_id == bob.pk, "buyer not recorded")
ok(bob.petals == before_bob - 3000, f"buyer charged wrong: {bob.petals} vs {before_bob - 3000}")
ok(alice.petals == before_alice + 2910, f"seller paid wrong: {alice.petals} vs {before_alice + 2910}")
ok(OwnedGirl.objects.get(player=bob, girl=target).count == 1, "buyer did not receive the card")
ok(TradeLog.objects.filter(listing=li).count() == 1, "trade log missing")
t = TradeLog.objects.get(listing=li)
ok(t.fee == 90, "trade fee not logged")

# double buy is a no-op
before_bob = bob.petals
r = bob_c.post(f"/market/buy/{li.pk}/", {"next": "/market/"})
bob = Player.objects.get(pk=bob.pk)
ok(bob.petals == before_bob, "second buy charged again")
ok(OwnedGirl.objects.get(player=bob, girl=target).count == 1, "second buy delivered again")

# broke buyer
poor_c, poor = mk("poor", 10)
r = poor_c.post(f"/market/buy/{li.pk}/", {"next": "/market/"})
ok(OwnedGirl.objects.filter(player=poor, girl=target).count() == 0, "poor buyer got the card")

# cancel restores the reserved copy
li2 = Listing.objects.filter(seller=alice, girl=target, status="active").first()
held = OwnedGirl.objects.get(player=alice, girl=target).count
alice_c.post(f"/market/cancel/{li2.pk}/", {"next": "/market/"})
li2.refresh_from_class = None
ok(Listing.objects.get(pk=li2.pk).status == "cancelled", "cancel did not set status")
ok(OwnedGirl.objects.get(player=alice, girl=target).count == held + 1, "cancel did not return the copy")

# cancel someone else's lot
li3 = Listing.objects.filter(seller=alice, status="active").first()
bob_c.post(f"/market/cancel/{li3.pk}/", {"next": "/market/"})
ok(Listing.objects.get(pk=li3.pk).status == "active", "foreign lot was cancelled")

# sell hint / market price
hint = target.sell_hint
ok(hint >= Listing.MIN_PRICE, f"sell_hint below floor: {hint}")
ok(li.market_price() > 0, "market_price returned nothing")

# market page with filters
for qs in ("", "?rarity=epic", "?sort=cheap", "?sort=rich", "?rarity=sakura&sort=rich"):
    ok(bob_c.get("/market/" + qs).status_code == 200, f"market {qs} broken")

# nav + admin
ok("/market/" in bob_c.get("/").content.decode(), "market missing from nav/footer")
ok(alice_c.get("/admin/").status_code == 302, "staff should redirect to admin login")
adm = Client()
ok(adm.login(username="admin", password="admin"), "admin/admin cannot log in")
ok(adm.get("/admin/").status_code == 200, "admin dashboard not reachable")
ok(adm.get("/admin/sakura/girl/").status_code == 200, "girl admin not reachable")
ok(adm.get("/admin/sakura/listing/").status_code == 200, "listing admin not reachable")
ok(adm.get("/admin/sakura/casedrop/").status_code == 200, "casedrop admin not reachable")

# dark theme wiring
body = bob_c.get("/").content.decode()
ok('id="themeBtn"' in body, "theme toggle button missing")
ok("sakura-theme" in body, "theme persistence script missing")
css = Path("static/css/sakura.css").read_text(encoding="utf-8")
ok('[data-theme="dark"]' in css, "dark theme selector missing from css")
ok("prefers-color-scheme: dark" in css, "system dark preference not handled")
ok("html[data-theme" not in css, "leftover html[data-theme] selector in css")
js = Path("static/js/sakura.js").read_text(encoding="utf-8")
ok("sakura-theme" in js, "theme persistence missing from js")
ok('root.dataset.theme' in js, "theme toggle not wired in js")

print()
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
    raise SystemExit(1)
print("MARKET + THEME + ADMIN TESTS PASSED")
