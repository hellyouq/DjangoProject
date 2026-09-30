from __future__ import annotations

import secrets

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from sakura import art
from sakura.models import (
    ELEMENT_META,
    Girl,
    Listing,
    OwnedGirl,
    OpenLog,
    Player,
    RARITY_META,
    RARITY_ORDER,
    Case,
    CaseDrop,
    Rarity,
    TradeLog,
    buy_listing,
    cancel_listing,
    create_listing,
    roll_girl,
    give_girl,
)

GUEST_SESSION_KEY = "sakura_guest_key"


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def get_player(request) -> Player:
    """Return (and lazily create) the player for this session."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        player, _ = Player.objects.get_or_create(user=user)
        if player.user_id is None:
            player.user = user
            player.save(update_fields=["user"])
        return player

    key = request.session.get(GUEST_SESSION_KEY)
    if not key:
        key = secrets.token_hex(16)
        request.session[GUEST_SESSION_KEY] = key
    player, _ = Player.objects.get_or_create(
        guest_key=key, defaults={"petals": 2500}
    )
    return player


def _girl_payload(drop: CaseDrop, owned: OwnedGirl | None, was_new: bool) -> dict:
    """Post-pull state of a girl. `owned` is the row after this pull was granted."""
    girl = drop.girl
    meta = girl.meta
    return {
        "id": girl.pk,
        "name": girl.name,
        "slug": girl.slug,
        "title": girl.title,
        "rarity": girl.rarity,
        "rarity_label": girl.get_rarity_display(),
        "color": meta["color"],
        "glow": meta["glow"],
        "tier": meta["tier"],
        "element": girl.element,
        "element_label": girl.get_element_display(),
        "accent": girl.accent,
        "image": girl.image_url,
        "fallback": f"/art/avatar/{girl.image_seed}.svg",
        "count": owned.count if owned else 1,
        "owned": bool(owned),
        "is_new": was_new,
        "power": girl.power,
        "cuteness": girl.cuteness,
        "elegance": girl.elegance,
        "spirit": girl.spirit,
        "url": girl.get_absolute_url(),
    }


def _rarity_context() -> list[dict]:
    out = []
    for key in RARITY_ORDER:
        meta = RARITY_META[key]
        out.append({"key": key, "label": dict(Rarity.choices)[key], "color": meta["color"], "tier": meta["tier"]})
    return out


# --------------------------------------------------------------------------- #
#  generated art (offline fallback + case banners)
# --------------------------------------------------------------------------- #
def avatar_art(request, seed: int):
    accent = request.GET.get("accent", "#ff8fb8")
    svg = art.avatar_svg(int(seed), accent=accent)
    return HttpResponse(svg, content_type="image/svg+xml")


def case_art(request, art_key: str):
    accent = request.GET.get("a", "#ff8fb8")
    accent2 = request.GET.get("b", "#ffd6e7")
    seed = int(request.GET.get("s", "7"))
    svg = art.case_svg(art_key, accent, accent2, seed=seed)
    return HttpResponse(svg, content_type="image/svg+xml")


def logo(request):
    return HttpResponse(art.logo_svg(), content_type="image/svg+xml")


# --------------------------------------------------------------------------- #
#  pages
# --------------------------------------------------------------------------- #
def home(request):
    player = get_player(request)
    cases = list(Case.objects.filter(is_active=True).annotate(pool=Count("drops")))
    total_girls = Girl.objects.count()
    owned_ids = set(OwnedGirl.objects.filter(player=player).values_list("girl_id", flat=True))
    for c in cases:
        c.rarity_map = c.drop_rate_map()
        c.odds = c.odds_rows()
        c.pool_size = c.drops.count()
    legends = list(
        Girl.objects.filter(rarity__in=[Rarity.SAKURA, Rarity.MYTHIC])
        .annotate(owners=Count("owned_by"))
        .order_by("-rarity", "name")[:8]
    )
    recent = (
        OwnedGirl.objects.filter(player=player)
        .select_related("girl")
        .order_by("-last_at")[:8]
    )
    stats = {
        "girls": total_girls,
        "cases": len(cases),
        "opened": OpenLog.objects.count(),
        "legendaries": Girl.objects.filter(rarity=Rarity.SAKURA).count(),
    }
    return render(
        request,
        "home.html",
        {
            "player": player,
            "cases": cases,
            "legends": legends,
            "recent": recent,
            "owned_ids": owned_ids,
            "stats": stats,
            "rarities": _rarity_context(),
        },
    )


def cases_view(request):
    player = get_player(request)
    owned_ids = set(OwnedGirl.objects.filter(player=player).values_list("girl_id", flat=True))
    cases = list(Case.objects.filter(is_active=True).annotate(pool=Count("drops")))
    for c in cases:
        c.rarity_map = c.drop_rate_map()
        c.odds = c.odds_rows()
        c.pool_size = c.drops.count()
    return render(
        request,
        "cases.html",
        {"player": player, "cases": cases, "owned_ids": owned_ids, "rarities": _rarity_context()},
    )


def case_detail(request, slug):
    player = get_player(request)
    case = get_object_or_404(Case, slug=slug, is_active=True)
    drops = case.drops.select_related("girl").order_by("girl__rarity", "girl__name")
    owned_ids = set(OwnedGirl.objects.filter(player=player).values_list("girl_id", flat=True))
    rarity_map = case.drop_rate_map()
    odds = []
    for drop in drops:
        odds.append({"drop": drop, "prob": round(float(drop.weight) / 10, 2)})
    top_prizes = [
        g for g in (case.first_odds_of(r) for r in (Rarity.SAKURA, Rarity.MYTHIC, Rarity.EPIC)) if g
    ]
    return render(
        request,
        "case_detail.html",
        {
            "player": player,
            "case": case,
            "case_odds": case.odds_rows(),
            "drops": drops,
            "top_prizes": top_prizes,
            "owned_ids": owned_ids,
            "rarity_map": rarity_map,
            "odds": odds,
            "rarities": _rarity_context(),
        },
    )


def girl_detail(request, slug):
    player = get_player(request)
    girl = get_object_or_404(Girl, slug=slug)
    owned = OwnedGirl.objects.filter(player=player, girl=girl).first()
    dupes = Case.objects.filter(drops__girl=girl).distinct()
    same_rarity = (
        Girl.objects.filter(rarity=girl.rarity)
        .exclude(pk=girl.pk)
        .order_by("?")[:8]
    )
    return render(
        request,
        "girl.html",
        {
            "player": player,
            "girl": girl,
            "owned": owned,
            "in_cases": dupes,
            "related": same_rarity,
            "stats": [
                ("Сила", girl.power, girl.meta["color"]),
                ("Милота", girl.cuteness, girl.accent),
                ("Элегантность", girl.elegance, girl.accent),
                ("Дух", girl.spirit, girl.meta["color"]),
            ],
            "total_owneds": OwnedGirl.objects.filter(girl=girl).count(),
            "rarities": _rarity_context(),
        },
    )


def collection(request):
    player = get_player(request)
    owned = OwnedGirl.objects.filter(player=player).select_related("girl")
    total = Girl.objects.count()

    qs = Girl.objects.all()
    rarity = request.GET.get("rarity", "")
    element = request.GET.get("element", "")
    q = request.GET.get("q", "").strip()
    owned_filter = request.GET.get("owned", "")
    sort = request.GET.get("sort", "rarity")

    if rarity:
        qs = qs.filter(rarity=rarity)
    if element:
        qs = qs.filter(element=element)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(title__icontains=q) | Q(series__icontains=q))
    if owned_filter == "have":
        qs = qs.filter(id__in=owned.values_list("girl_id", flat=True))
    elif owned_filter == "missing":
        qs = qs.exclude(id__in=owned.values_list("girl_id", flat=True))

    ordering = {
        "rarity": ["rarity", "name"],
        "name": ["name"],
        "power": ["-power"],
        "new": ["-released"],
    }.get(sort, ["rarity", "name"])
    qs = qs.order_by(*ordering)

    owned_map = {o.girl_id: o for o in owned}
    grid = [{"girl": g, "owned": owned_map.get(g.pk)} for g in qs]

    by_rarity = []
    for key in RARITY_ORDER:
        meta = RARITY_META[key]
        sub = Girl.objects.filter(rarity=key)
        have = owned.filter(girl__rarity=key).count()
        by_rarity.append(
            {
                "key": key,
                "label": dict(Rarity.choices)[key],
                "color": meta["color"],
                "total": sub.count(),
                "have": have,
                "pct": round(have * 100 / sub.count()) if sub.count() else 0,
            }
        )

    elements = [
        {"key": k, "label": v[1], "color": v[0], "n": Girl.objects.filter(element=k).count()}
        for k, v in ELEMENT_META.items()
    ]

    return render(
        request,
        "collection.html",
        {
            "player": player,
            "grid": grid,
            "by_rarity": by_rarity,
            "elements": elements,
            "total": total,
            "have": owned.count(),
            "rarity": rarity,
            "element": element,
            "q": q,
            "owned_filter": owned_filter,
            "sort": sort,
            "rarities": _rarity_context(),
        },
    )


def profile(request):
    player = get_player(request)
    owned = OwnedGirl.objects.filter(player=player).select_related("girl")
    logs = OpenLog.objects.filter(player=player).select_related("girl", "case")[:30]
    rarity_hits = (
        OpenLog.objects.filter(player=player)
        .values("girl__rarity")
        .annotate(n=Count("id"))
    )
    hits = {r["girl__rarity"]: r["n"] for r in rarity_hits}
    top = sorted(owned, key=lambda o: o.count, reverse=True)[:8]
    luck = 0
    if player.total_opens:
        luck = round(hits.get(Rarity.SAKURA, 0) * 100 / player.total_opens * 1000)
    labels = dict(Rarity.choices)
    hit_rows = [
        {
            "key": key,
            "label": labels[key],
            "color": RARITY_META[key]["color"],
            "n": hits.get(key, 0),
            "pct": round(hits.get(key, 0) * 100 / player.total_opens) if player.total_opens else 0,
        }
        for key in RARITY_ORDER
    ]
    return render(
        request,
        "profile.html",
        {
            "player": player,
            "owned": owned,
            "have": owned.count(),
            "logs": logs,
            "hits": hits,
            "hit_rows": hit_rows,
            "top": top,
            "total": Girl.objects.count(),
            "luck": luck,
            "rarities": _rarity_context(),
        },
    )


def hall(request):
    board = (
        Player.objects.filter(user__isnull=False)
        .select_related("user")
        .order_by("-legendaries", "-total_opens")[:24]
    )
    mine = None
    if request.user.is_authenticated:
        p = get_player(request)
        mine = p
    return render(request, "hall.html", {"board": board, "player": mine, "rarities": _rarity_context()})


# --------------------------------------------------------------------------- #
#  opening
# --------------------------------------------------------------------------- #
@require_POST
def open_case(request, slug):
    case = get_object_or_404(Case, slug=slug, is_active=True)
    player = get_player(request)

    try:
        amount = int(request.POST.get("amount", "1"))
    except ValueError:
        amount = 1
    amount = max(1, min(10, amount))

    cost = case.price * amount
    if player.petals < cost:
        return JsonResponse(
            {"ok": False, "error": "Не хватает лепестков", "need": cost - player.petals, "petals": player.petals},
            status=402,
        )

    drops = list(case.drops.select_related("girl"))
    if not drops:
        return JsonResponse({"ok": False, "error": "Кейс пуст"}, status=500)

    case._pity = player.pity_counter
    results = []
    legendary_hit = False
    for _ in range(amount):
        drop = roll_girl(case)
        girl = drop.girl
        owned, was_new = give_girl(player, girl)
        if girl.rarity == Rarity.SAKURA:
            legendary_hit = True
            player.pity_counter = 0
        elif player.pity_counter < Player.PITY_LIMIT:
            player.pity_counter += 1
        OpenLog.objects.create(player=player, girl=girl, case=case, was_new=was_new)
        results.append(_girl_payload(drop, owned, was_new))

    player.petals -= cost
    player.total_opens += amount
    if legendary_hit:
        player.legendaries += 1
    player.save(update_fields=["petals", "total_opens", "legendaries", "pity_counter"])

    return JsonResponse(
        {
            "ok": True,
            "results": results,
            "petals": player.petals,
            "pity": player.pity_counter,
            "pity_max": Player.PITY_LIMIT,
            "legendary": legendary_hit,
        }
    )


def timezone_now():
    from django.utils import timezone

    return timezone.now()


@require_POST
def claim_daily(request):
    player = get_player(request)
    if player.reset_daily_if_needed():
        return JsonResponse({"ok": True, "petals": player.petals, "gain": Player.DAILY_AMOUNT})
    return JsonResponse({"ok": False, "error": "Завтра", "petals": player.petals})


# --------------------------------------------------------------------------- #
#  exchange / marketplace
# --------------------------------------------------------------------------- #
MARKET_SORTS = {
    "new": ("Сначала новые", lambda li: li.created_at),
    "cheap": ("Сначала дешёвые", lambda li: li.price),
    "rich": ("Сначала дорогие", lambda li: -li.price),
    "rarity": ("По редкости", lambda li: (li.girl.meta["tier"], -li.price)),
}



def market(request):
    player = get_player(request)
    listings = (
        Listing.objects.filter(status="active")
        .select_related("girl", "seller", "seller__user")
        .order_by("-created_at")[:80]
    )
    rarity = request.GET.get("rarity", "")
    sort = request.GET.get("sort", "new")
    if rarity:
        listings = [li for li in listings if li.girl.rarity == rarity]
    if sort in MARKET_SORTS:
        listings = sorted(listings, key=MARKET_SORTS[sort][1])

    sellable = [
        o
        for o in OwnedGirl.objects.filter(player=player, count__gte=2).select_related("girl")
    ]
    mine = (
        Listing.objects.filter(seller=player)
        .select_related("girl", "buyer")
        .order_by("-created_at")[:24]
    )
    sold_total = TradeLog.objects.count()
    return render(
        request,
        "market.html",
        {
            "player": player,
            "listings": listings,
            "sellable": sellable,
            "mine": mine,
            "rarity": rarity,
            "sort": sort,
            "sorts": MARKET_SORTS,
            "sold_total": sold_total,
            "min_price": Listing.MIN_PRICE,
            "fee": int(Listing.SELL_FEE * 100),
            "rarities": _rarity_context(),
        },
    )


@require_POST
def sell(request):
    player = get_player(request)
    girl = get_object_or_404(Girl, pk=request.POST.get("girl", 0))
    try:
        price = int(request.POST.get("price", "0"))
    except ValueError:
        price = 0
    listing, message = create_listing(player, girl, price)
    if listing is None:
        messages.error(request, message)
    else:
        messages.success(request, f"{message}: {girl.name} за {price} 🌸")
    return redirect(request.POST.get("next") or "market")


@require_POST
def buy(request, pk):
    player = get_player(request)
    listing = get_object_or_404(Listing, pk=pk)
    ok, message = buy_listing(player, listing)
    (messages.success if ok else messages.error)(request, message)
    return redirect(request.POST.get("next") or "market")


@require_POST
def cancel(request, pk):
    player = get_player(request)
    listing = get_object_or_404(Listing, pk=pk)
    ok, message = cancel_listing(player, listing)
    (messages.success if ok else messages.error)(request, message)
    return redirect(request.POST.get("next") or "market")


# --------------------------------------------------------------------------- #
#  auth
# --------------------------------------------------------------------------- #
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        Player.objects.update_or_create(user=user, defaults={"petals": 3000})
        messages.success(request, "Добро пожаловать в сад! Лепестки уже твои 🌸")
        return redirect("home")
    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(request.GET.get("next") or "home")
    return render(request, "auth/login.html", {"form": form, "next": request.GET.get("next", "")})


def logout_view(request):
    auth_logout(request)
    return redirect("home")
