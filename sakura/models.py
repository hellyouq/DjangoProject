from __future__ import annotations

import random

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone


class Rarity(models.TextChoices):
    SAKURA = "sakura", "\U0001f338 Р›РµРіРµРЅРґР° СЃР°РєСѓСЂС‹"
    MYTHIC = "mythic", "\U0001f49e РњРёС„РёС‡РµСЃРєР°СЏ"
    EPIC = "epic", "\U0001f48e Р­РїРёС‡РµСЃРєР°СЏ"
    RARE = "rare", "\U0001f499 Р РµРґРєР°СЏ"
    COMMON = "common", "\U0001f343 РћР±С‹С‡РЅР°СЏ"


RARITY_ORDER = [Rarity.SAKURA, Rarity.MYTHIC, Rarity.EPIC, Rarity.RARE, Rarity.COMMON]

RARITY_META = {
    Rarity.SAKURA: {
        "color": "#ff5fa2",
        "glow": "rgba(255,95,162,.55)",
        "tier": 0,
        "weight": 0.5,
    },
    Rarity.MYTHIC: {
        "color": "#8b5cf6",
        "glow": "rgba(139,92,246,.45)",
        "tier": 1,
        "weight": 2.0,
    },
    Rarity.EPIC: {
        "color": "#2563eb",
        "glow": "rgba(37,99,235,.35)",
        "tier": 2,
        "weight": 8.0,
    },
    Rarity.RARE: {
        "color": "#0ea5a4",
        "glow": "rgba(14,165,164,.28)",
        "tier": 3,
        "weight": 20.0,
    },
    Rarity.COMMON: {
        "color": "#94a3b8",
        "glow": "rgba(148,163,184,.22)",
        "tier": 4,
        "weight": 69.5,
    },
}


class Element(models.TextChoices):
    SAKURA = "sakura", "РЎР°РєСѓСЂР°"
    MOON = "moon", "Р›СѓРЅР°"
    STAR = "star", "Р—РІС‘Р·РґС‹"
    SNOW = "snow", "РЎРЅРµРі"
    RAIN = "rain", "Р”РѕР¶РґСЊ"
    FIRE = "fire", "РџР»Р°РјСЏ"
    FOREST = "forest", "Р›РµСЃ"
    SEA = "sea", "РњРѕСЂРµ"
    DREAM = "dream", "РЎРѕРЅ"
    DARK = "dark", "РўРµРЅСЊ"


ELEMENT_META = {
    Element.SAKURA: ("#ff8fb8", "СЃР°РєСѓСЂР°"),
    Element.MOON: ("#a5b4fc", "Р»СѓРЅР°"),
    Element.STAR: ("#fcd34d", "Р·РІС‘Р·РґС‹"),
    Element.SNOW: ("#bae6fd", "СЃРЅРµРі"),
    Element.RAIN: ("#7dd3fc", "РґРѕР¶РґСЊ"),
    Element.FIRE: ("#fb923c", "РїР»Р°РјСЏ"),
    Element.FOREST: ("#86efac", "Р»РµСЃ"),
    Element.SEA: ("#67e8f9", "РјРѕСЂРµ"),
    Element.DREAM: ("#f0abfc", "СЃРѕРЅ"),
    Element.DARK: ("#94a3b8", "С‚РµРЅСЊ"),
}


class Series(models.TextChoices):
    AZURE = "azure", "Р“РѕР»СѓР±РѕР№ СЃР°Рґ"
    HANA = "hana", "Р¦РІРµС‚РµРЅРёРµ РҐР°РЅР°"
    KITSUNE = "kitsune", "РҐРІРѕСЃС‚ РљРёС†СѓРЅРµ"
    SNOWFALL = "snowfall", "РЎРЅРµРіРѕРїР°Рґ"
    NEON = "neon", "РќРµРѕРЅРѕРІС‹Р№ РўРѕРєРёРѕ"
    ABYSS = "abyss", "Р‘РµР·РґРЅР°"
    LUMEN = "lumen", "РЎРІРµС‚"
    VERMILION = "vermilion", "РђР»С‹Р№ РІРµРµСЂ"
    ORCHID = "orchid", "РћСЂС…РёРґРµСЏ"
    HALO = "halo", "РќРёРјР±"
    MOONLIGHT = "moonlight", "Р›СѓРЅРЅС‹Р№ СЃРІРµС‚"
    FORGE = "forge", "РљСѓР·РЅСЏ СЃРЅРѕРІ"


class Girl(models.Model):
    name = models.CharField("РРјСЏ", max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    series = models.CharField(max_length=20, choices=Series.choices)
    rarity = models.CharField(max_length=12, choices=Rarity.choices, default=Rarity.COMMON)
    element = models.CharField(max_length=12, choices=Element.choices, default=Element.SAKURA)

    title = models.CharField("РўРёС‚СѓР»", max_length=120, blank=True)
    quote = models.CharField("Р¦РёС‚Р°С‚Р°", max_length=200, blank=True)
    origin = models.CharField("РџСЂРѕРёСЃС…РѕР¶РґРµРЅРёРµ", max_length=120, blank=True)

    image_seed = models.PositiveIntegerField(default=1, unique=True)
    art_style = models.PositiveSmallIntegerField(default=0)

    power = models.PositiveSmallIntegerField("РЎРёР»Р°", default=50)
    cuteness = models.PositiveSmallIntegerField("РњРёР»РѕС‚Р°", default=50)
    elegance = models.PositiveSmallIntegerField("Р­Р»РµРіР°РЅС‚РЅРѕСЃС‚СЊ", default=50)
    spirit = models.PositiveSmallIntegerField("Р”СѓС…", default=50)

    lore = models.TextField("РСЃС‚РѕСЂРёСЏ", blank=True)
    released = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "РђРЅРёРјРµ-РґРµРІРѕС‡РєР°"
        verbose_name_plural = "РђРЅРёРјРµ-РґРµРІРѕС‡РєРё"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("girl", kwargs={"slug": self.slug})

    @property
    def meta(self) -> dict:
        return RARITY_META.get(self.rarity, RARITY_META[Rarity.COMMON])

    @property
    def accent(self) -> str:
        return ELEMENT_META.get(self.element, ELEMENT_META[Element.SAKURA])[0]

    @property
    def image_url(self) -> str:
        return f"https://thisanimedoesnotexist.ai/results/psi-1.0/seed{self.image_seed:05d}.png"

    @property
    def is_top_rarity(self) -> bool:
        return self.rarity in (Rarity.SAKURA, Rarity.MYTHIC)

    def stat_total(self) -> int:
        return self.power + self.cuteness + self.elegance + self.spirit

    @property
    def base_value(self) -> int:
        """Reference price used when there is no market history yet."""
        return {
            Rarity.COMMON: 400,
            Rarity.RARE: 1000,
            Rarity.EPIC: 2800,
            Rarity.MYTHIC: 7500,
            Rarity.SAKURA: 26000,
        }[self.rarity]

    @property
    def sell_hint(self) -> int:
        """Median of active listings, falling back to the base value."""
        prices = list(
            Listing.objects.filter(girl=self, status="active")
            .order_by("price")
            .values_list("price", flat=True)[:20]
        )
        if not prices:
            return self.base_value
        return max(Listing.MIN_PRICE, prices[len(prices) // 2])


class Case(models.Model):
    name = models.CharField("РќР°Р·РІР°РЅРёРµ", max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    tagline = models.CharField("РЎР»РѕРіР°РЅ", max_length=160, blank=True)
    description = models.TextField("РћРїРёСЃР°РЅРёРµ", blank=True)
    price = models.PositiveIntegerField("Р¦РµРЅР°", default=500)
    art_key = models.CharField(max_length=40, default="sakura")
    accent = models.CharField(max_length=9, default="#ff8fb8")
    accent2 = models.CharField(max_length=9, default="#ffd6e7")
    badge = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    is_new = models.BooleanField(default=False)
    sort = models.PositiveSmallIntegerField(default=100)
    background = models.URLField(blank=True)

    class Meta:
        verbose_name = "РљРµР№СЃ"
        verbose_name_plural = "РљРµР№СЃС‹"
        ordering = ["sort", "price"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("case", kwargs={"slug": self.slug})

    @property
    def gradient(self) -> str:
        return f"linear-gradient(135deg, {self.accent} 0%, {self.accent2} 100%)"

    def drop_rate_map(self) -> dict:
        rates: dict = {}
        for drop in self.drops.select_related("girl"):
            meta = drop.girl.meta
            rates[meta["tier"]] = round(rates.get(meta["tier"], 0) + float(drop.weight), 2)
        return dict(sorted(rates.items()))

    def odds_rows(self) -> list[dict]:
        """Rarity breakdown ready for the template."""
        rates = self.drop_rate_map()
        labels = dict(Rarity.choices)
        rows = []
        for key in RARITY_ORDER:
            meta = RARITY_META[key]
            pct = rates.get(meta["tier"], 0.0)
            if pct <= 0:
                continue
            rows.append(
                {
                    "key": key,
                    "tier": meta["tier"],
                    "color": meta["color"],
                    "label": labels[key],
                    "pct": round(pct, 2),
                }
            )
        return rows

    def first_odds_of(self, rarity: str) -> Girl | None:
        drop = self.drops.filter(girl__rarity=rarity).select_related("girl").order_by("-weight").first()
        return drop.girl if drop else None

    @property
    def has_legend(self) -> bool:
        return self.drops.filter(girl__rarity=Rarity.SAKURA).exists()


class CaseDrop(models.Model):
    case = models.ForeignKey(Case, related_name="drops", on_delete=models.CASCADE)
    girl = models.ForeignKey(Girl, related_name="drops", on_delete=models.CASCADE)
    weight = models.DecimalField("Р’РµСЃ %", max_digits=6, decimal_places=2, default=1)

    class Meta:
        verbose_name = "Р”СЂРѕРї РёР· РєРµР№СЃР°"
        verbose_name_plural = "Р”СЂРѕРїС‹ РёР· РєРµР№СЃРѕРІ"
        unique_together = ("case", "girl")

    def __str__(self) -> str:
        return f"{self.case} в†’ {self.girl}"


class Player(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="player", on_delete=models.CASCADE,
        null=True, blank=True,
    )
    guest_key = models.CharField(max_length=64, blank=True, db_index=True)
    nickname = models.CharField(max_length=40, blank=True)
    petals = models.PositiveIntegerField("Р›РµРїРµСЃС‚РєРё", default=2500)
    total_opens = models.PositiveIntegerField("Р’СЃРµРіРѕ РѕС‚РєСЂС‹С‚РёР№", default=0)
    legendaries = models.PositiveIntegerField("Р›РµРіРµРЅРґ РІС‹Р±РёС‚Рѕ", default=0)
    pity_counter = models.PositiveIntegerField("Р”Рѕ РіР°СЂР°РЅС‚Р°", default=0)
    last_daily = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    PITY_LIMIT = 60
    DAILY_AMOUNT = 500

    class Meta:
        verbose_name = "РРіСЂРѕРє"
        verbose_name_plural = "РРіСЂРѕРєРё"

    def __str__(self) -> str:
        return f"{self.user.username if self.user else self.nickname or 'РіРѕСЃС‚СЊ'} В· {self.petals} рџЊё"

    @property
    def display_name(self) -> str:
        if self.user:
            return self.user.username
        return self.nickname or f"Р“РѕСЃС‚СЊ-{str(self.pk or 0)[:4]}"

    @property
    def pity_left(self) -> int:
        return max(0, self.PITY_LIMIT - self.pity_counter)

    @property
    def pity_pct(self) -> int:
        return int(self.pity_counter * 100 / self.PITY_LIMIT)

    @property
    def rank_title(self) -> str:
        if self.legendaries >= 12:
            return "РҐСЂР°РЅРёС‚РµР»СЊРЅРёС†Р° РІРµСЃРЅС‹"
        if self.legendaries >= 6:
            return "РџРѕРІРµР»РёС‚РµР»СЊРЅРёС†Р° СЃР°РєСѓСЂС‹"
        if self.legendaries >= 3:
            return "Р¦РІРµС‚СѓС‰РёР№ СЃР°РґРѕРІРЅРёРє"
        if self.legendaries >= 1:
            return "РЎС‡Р°СЃС‚Р»РёРІР°СЏ РЅР°С…РѕРґРєР°"
        if self.total_opens >= 40:
            return "Р’РµС‚СЂРµРЅР°СЏ"
        if self.total_opens >= 10:
            return "РќР°С‡РёРЅР°СЋС‰РёР№ РёСЃРєР°С‚РµР»СЊ"
        return "РќРѕРІРёС‡РѕРє РІРµСЃРЅС‹"

    def reset_daily_if_needed(self) -> bool:
        now = timezone.now()
        if not self.last_daily:
            self.last_daily = now
            self.save(update_fields=["last_daily"])
            return True
        if (now - self.last_daily).total_seconds() >= 20 * 60 * 60:
            self.last_daily = now
            self.petals += 500
            self.save(update_fields=["last_daily", "petals"])
            return True
        return False

    def collection_percent(self) -> int:
        total = Girl.objects.count()
        if not total:
            return 0
        return round(self.owned_girls.count() * 100 / total)

    @property
    def is_daily_ready(self) -> bool:
        if not self.last_daily:
            return True
        return (timezone.now() - self.last_daily).total_seconds() >= 20 * 60 * 60


class OwnedGirl(models.Model):
    player = models.ForeignKey(Player, related_name="owned_girls", on_delete=models.CASCADE)
    girl = models.ForeignKey(Girl, related_name="owned_by", on_delete=models.CASCADE)
    count = models.PositiveIntegerField("РљРѕРїРёР№", default=1)
    shards = models.PositiveIntegerField("РћСЃРєРѕР»РєРё", default=0)
    first_at = models.DateTimeField(auto_now_add=True)
    last_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Р’ РєРѕР»Р»РµРєС†РёРё"
        verbose_name_plural = "Р’ РєРѕР»Р»РµРєС†РёРё"
        unique_together = ("player", "girl")
        ordering = ["-count"]

    def __str__(self) -> str:
        return f"{self.girl} x{self.count}"


class OpenLog(models.Model):
    player = models.ForeignKey(Player, related_name="logs", on_delete=models.CASCADE)
    girl = models.ForeignKey(Girl, on_delete=models.CASCADE)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    was_new = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "РСЃС‚РѕСЂРёСЏ РѕС‚РєСЂС‹С‚РёР№"
        verbose_name_plural = "РСЃС‚РѕСЂРёСЏ РѕС‚РєСЂС‹С‚РёР№"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.player} РІС‹Р±РёР» {self.girl}"


class Listing(models.Model):
    """A duplicate card offered on the exchange."""

    STATUS = [("active", "РђРєС‚РёРІРЅРѕ"), ("sold", "РџСЂРѕРґР°РЅРѕ"), ("cancelled", "РћС‚РјРµРЅРµРЅРѕ")]
    SELL_FEE = 0.03
    MIN_PRICE = 50

    seller = models.ForeignKey(Player, related_name="listings", on_delete=models.CASCADE)
    girl = models.ForeignKey(Girl, related_name="listings", on_delete=models.CASCADE)
    price = models.PositiveIntegerField("Р¦РµРЅР°", default=MIN_PRICE)
    status = models.CharField(max_length=10, choices=STATUS, default="active")
    buyer = models.ForeignKey(
        Player, related_name="bought", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Р›РѕС‚ РЅР° Р±РёСЂР¶Рµ"
        verbose_name_plural = "Р›РѕС‚С‹ РЅР° Р±РёСЂР¶Рµ"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.girl} Р·Р° {self.price} рџЊё ({self.status})"

    @property
    def fee(self) -> int:
        return int(self.price * self.SELL_FEE)

    @property
    def payout(self) -> int:
        return self.price - self.fee

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def market_price(self) -> int:
        """Median price of comparable active listings, used as a price hint."""
        qs = (
            Listing.objects.filter(girl=self.girl, status="active")
            .exclude(pk=self.pk)
            .order_by("price")
        )
        prices = list(qs.values_list("price", flat=True)[:20])
        if not prices:
            base = {"common": 380, "rare": 950, "epic": 2600, "mythic": 7200, "sakura": 24000}[
                self.girl.rarity
            ]
            return base
        return prices[len(prices) // 2]


class TradeLog(models.Model):
    """Immutable audit of every completed exchange."""

    listing = models.OneToOneField(Listing, related_name="trade", on_delete=models.CASCADE)
    seller = models.ForeignKey(Player, related_name="sold", on_delete=models.CASCADE)
    buyer = models.ForeignKey(Player, related_name="purchased", on_delete=models.CASCADE)
    girl = models.ForeignKey(Girl, on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    fee = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "РЎРґРµР»РєР°"
        verbose_name_plural = "РЎРґРµР»РєРё"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.buyer} РєСѓРїРёР» {self.girl} Сѓ {self.seller} Р·Р° {self.price}"


def give_girl(player: Player, girl: Girl) -> tuple[OwnedGirl, bool]:
    """Grant one copy of `girl` to `player`. Returns (owned_row, was_new)."""
    owned = OwnedGirl.objects.filter(player=player, girl=girl).first()
    if owned:
        owned.count += 1
        owned.shards += 1
        owned.last_at = timezone.now()
        owned.save(update_fields=["count", "shards", "last_at"])
        return owned, False
    return OwnedGirl.objects.create(player=player, girl=girl, count=1, shards=1), True


def create_listing(seller: Player, girl: Girl, price: int) -> tuple[Listing | None, str]:
    if price < Listing.MIN_PRICE:
        return None, f"РњРёРЅРёРјР°Р»СЊРЅР°СЏ С†РµРЅР° вЂ” {Listing.MIN_PRICE} рџЊё"
    owned = OwnedGirl.objects.filter(player=seller, girl=girl).first()
    if not owned or owned.count < 2:
        return None, "РџСЂРѕРґР°С‚СЊ РјРѕР¶РЅРѕ С‚РѕР»СЊРєРѕ РІС‚РѕСЂСѓСЋ Рё РїРѕСЃР»РµРґСѓСЋС‰РёРµ РєРѕРїРёРё"
    active = Listing.objects.filter(seller=seller, girl=girl, status="active").count()
    if active >= 4:
        return None, "РќРµ Р±РѕР»СЊС€Рµ 4 Р°РєС‚РёРІРЅС‹С… Р»РѕС‚РѕРІ РЅР° РѕРґРЅСѓ РґРµРІРѕС‡РєСѓ"
    listing = Listing.objects.create(seller=seller, girl=girl, price=price)
    # reserve one copy so it cannot be re-listed or eaten by the pity system
    owned.count -= 1
    owned.save(update_fields=["count"])
    return listing, "Р›РѕС‚ РІС‹СЃС‚Р°РІР»РµРЅ"


def buy_listing(buyer: Player, listing: Listing) -> tuple[bool, str]:
    if not listing.is_active:
        return False, "Р›РѕС‚ СѓР¶Рµ РєСѓРїР»РµРЅ"
    if listing.seller_id == buyer.pk:
        return False, "РќРµР»СЊР·СЏ РєСѓРїРёС‚СЊ СЃРІРѕР№ Р¶Рµ Р»РѕС‚"
    if buyer.petals < listing.price:
        return False, "РќРµ С…РІР°С‚Р°РµС‚ Р»РµРїРµСЃС‚РєРѕРІ"

    with transaction.atomic():
        locked = Listing.objects.select_for_update().filter(pk=listing.pk, status="active").first()
        if locked is None:
            return False, "Р›РѕС‚ СѓР¶Рµ РєСѓРїР»РµРЅ"
        if buyer.petals < locked.price:
            return False, "РќРµ С…РІР°С‚Р°РµС‚ Р»РµРїРµСЃС‚РєРѕРІ"

        buyer.petals -= locked.price
        buyer.save(update_fields=["petals"])
        give_girl(buyer, locked.girl)

        locked.seller.petals += locked.payout
        locked.seller.save(update_fields=["petals"])

        locked.status = "sold"
        locked.buyer = buyer
        locked.sold_at = timezone.now()
        locked.save(update_fields=["status", "buyer", "sold_at"])
        TradeLog.objects.create(
            listing=locked,
            seller=locked.seller,
            buyer=buyer,
            girl=locked.girl,
            price=locked.price,
            fee=locked.fee,
        )
    return True, f"РљСѓРїР»РµРЅРѕ: {locked.girl.name}"


def cancel_listing(seller: Player, listing: Listing) -> tuple[bool, str]:
    if not listing.is_active or listing.seller_id != seller.pk:
        return False, "Р›РѕС‚ РЅРµРґРѕСЃС‚СѓРїРµРЅ"
    with transaction.atomic():
        locked = Listing.objects.select_for_update().filter(pk=listing.pk, status="active").first()
        if locked is None:
            return False, "Р›РѕС‚ СѓР¶Рµ РєСѓРїР»РµРЅ"
        owned = OwnedGirl.objects.filter(player=seller, girl=locked.girl).first()
        if owned:
            owned.count += 1
            owned.save(update_fields=["count"])
        else:
            OwnedGirl.objects.create(player=seller, girl=locked.girl, count=1)
        locked.status = "cancelled"
        locked.save(update_fields=["status"])
    return True, "Р›РѕС‚ СЃРЅСЏС‚, РєРѕРїРёСЏ РІРµСЂРЅСѓР»Р°СЃСЊ"


def roll_girl(case: Case, rng: random.Random | None = None) -> CaseDrop:
    """Weighted pick honouring the legendary pity system."""
    rng = rng or random.SystemRandom()
    player_pity = getattr(case, "_pity", 0) or 0
    if player_pity >= Player.PITY_LIMIT - 1:
        top = [d for d in case.drops.all() if d.girl.rarity == Rarity.SAKURA]
        if top:
            return rng.choice(top)
    pool = list(case.drops.all())
    total = sum(float(d.weight) for d in pool)
    pick = rng.uniform(0, total)
    upto = 0.0
    for drop in pool:
        upto += float(drop.weight)
        if pick <= upto:
            return drop
    return pool[-1]
