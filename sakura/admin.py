from django.contrib import admin
from django.utils.html import format_html

from sakura.models import Case, CaseDrop, Girl, Listing, OpenLog, OwnedGirl, Player, TradeLog


class CaseDropInline(admin.TabularInline):
    model = CaseDrop
    extra = 0
    autocomplete_fields = ["girl"]


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "art_key", "is_active", "is_new", "sort", "preview")
    list_editable = ("is_active", "is_new", "sort")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CaseDropInline]

    def preview(self, obj):
        return format_html(
            '<img src="/art/case/{}.svg?a={}&b={}" style="height:48px;border-radius:8px">',
            obj.art_key, obj.accent, obj.accent2,
        )


@admin.register(Girl)
class GirlAdmin(admin.ModelAdmin):
    list_display = ("name", "rarity", "element", "series", "power", "cuteness", "elegance", "spirit", "art")
    list_filter = ("rarity", "element", "series")
    search_fields = ("name", "title", "quote")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("art",)

    def art(self, obj):
        return format_html(
            '<img src="{}" onerror="this.src=\'/art/avatar/{}.svg\'" style="width:56px;height:56px;'
            'border-radius:10px;object-fit:cover">',
            obj.image_url, obj.image_seed,
        )


@admin.register(OpenLog)
class OpenLogAdmin(admin.ModelAdmin):
    list_display = ("player", "girl", "case", "was_new", "created_at")
    list_filter = ("was_new", "girl__rarity")
    date_hierarchy = "created_at"


@admin.register(OwnedGirl)
class OwnedGirlAdmin(admin.ModelAdmin):
    list_display = ("player", "girl", "count", "shards", "last_at")
    list_filter = ("girl__rarity",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("display_name", "petals", "total_opens", "legendaries", "pity_counter", "last_daily")
    list_filter = ("user",)
    search_fields = ("nickname", "user__username", "guest_key")


@admin.register(CaseDrop)
class CaseDropAdmin(admin.ModelAdmin):
    list_display = ("case", "girl", "weight")
    list_filter = ("case",)
    autocomplete_fields = ["girl"]
    list_editable = ("weight",)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("girl", "seller", "price", "fee", "status", "buyer", "created_at")
    list_filter = ("status", "girl__rarity")
    search_fields = ("girl__name", "seller__username", "buyer__username")
    autocomplete_fields = ("girl", "seller", "buyer")
    readonly_fields = ("fee", "payout", "created_at", "sold_at")
    list_editable = ("status",)


@admin.register(TradeLog)
class TradeLogAdmin(admin.ModelAdmin):
    list_display = ("listing", "seller", "buyer", "girl", "price", "fee", "created_at")
    list_filter = ("created_at",)
    search_fields = ("seller__username", "buyer__username", "listing__girl__name")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in TradeLog._meta.fields]
