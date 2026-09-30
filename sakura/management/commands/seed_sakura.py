"""Populate the database with 90 original heroines and 12 sakura cases."""

from __future__ import annotations

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from sakura.models import Case, CaseDrop, Element, Girl, Rarity, Series

# (name, series, element, title, quote)
GIRLS: list[tuple[str, str, str, str, str]] = [
    # ---------------- SAKURA LEGEND ----------------
    ("Юкино Ханари", "hana", "sakura", "Цвету, даже не глядя", "Цвету, даже если на меня не смотрят."),
    ("Ария Куросаки", "moonlight", "moon", "Лунный лепесток", "Луна отдала мне свет — я поделюсь им с тобой."),
    ("Рэн Акаи", "vermilion", "fire", "Алый веер судьбы", "Один взмах — и твоя история уже другая."),
    ("Кирин Цукинами", "halo", "star", "Нимб из лепестков", "Я пришла благословить твоё новолуние."),
    ("Момоно Сакурай", "azure", "sakura", "Королева весеннего сада", "Весь сад замолкает, когда я прохожу мимо."),
    ("Сильвия Хакусэ", "abyss", "dark", "Душа цветения", "Даже тьма расцветает, если смотреть достаточно долго."),
    # ---------------- MYTHIC ----------------
    ("Химеко Юкигара", "snowfall", "snow", "Снежная принцесса", "Мой снег падает тише, чем твои мысли."),
    ("Аоки Рин", "lumen", "star", "Хранительница звезды", "Я сорвала звезду, чтобы осветить тебе дорогу."),
    ("Курокава Рин", "moonlight", "rain", "Ночная флейтистка", "Дождь играет мою мелодию, если слушать внимательно."),
    ("Ичико Мари", "lumen", "sea", "Приливная принцесса", "Волны зовут меня по имени каждую ночь."),
    ("Широ Кагура", "forge", "fire", "Кузнец вдохновения", "Я кую из искр то, что ты только что задумал."),
    ("Нанами Аоки", "forge", "dream", "Повелительница грёз", "Твои сны приходят ко мне на проверку."),
    ("Рейна Куробути", "neon", "dream", "Неоновая саки", "Мой свет не гаснет, пока ты смотришь."),
    ("Юми Такэда", "orchid", "forest", "Тихая жрица леса", "Лес говорит со мной. Я почти отвечаю."),
    ("Никко Адзума", "vermilion", "fire", "Пламя веера", "Осторожно: я горячая, но обнимать можно."),
    ("Миюки Хосе", "lumen", "dream", "Сон на ладони", "Смотри, твой сон только что сел ко мне на ладонь."),
    ("Эрика Сибата", "abyss", "dark", "Полуночный тотем", "Тишина — это тоже музыка. Я её играю."),
    ("Ханаби Кимура", "orchid", "sea", "Девушка приливов", "Прилив вернулся — значит, я уже рядом."),
    # ---------------- EPIC ----------------
    ("Карин Мидзуки", "azure", "rain", "Капелька дождя", "Маленькая капля, но я самая громкая."),
    ("Сиори Накамура", "halo", "moon", "Лунный дирижёр", "Я задаю такт — небо играет само."),
    ("Марико Фудзи", "orchid", "forest", "Хранительница мха", "Не трогай мой мох. Он помнит всё."),
    ("Юна Ватанабэ", "snowfall", "snow", "Хрустальный иней", "Мой иней ломается, если сказать моё имя."),
    ("Рина Кимура", "vermilion", "fire", "Пламень-капля", "Я грею тебя ровно настолько, насколько нужно."),
    ("Мэй Ито", "lumen", "dream", "Мечта в рукаве", "У меня в рукаве целая вселенная. Найдёшь? Нет."),
    ("Сабина Рэй", "neon", "star", "Неоновая звезда", "Я загораюсь только от одного: от твоего внимания."),
    ("Аои Таки", "lumen", "sea", "Солёная слеза", "В моих слезах столько соли, сколько было скуки."),
    ("Хинамари", "abyss", "moon", "Лунная тень", "Тень тоже бывает красивой. Особенно в луну."),
    ("Кира Ибараки", "forge", "fire", "Пламя идола", "Сцена — мой алтарь, микрофон — мой меч."),
    ("Нао Киригами", "halo", "star", "Падающая звезда", "Я упала с неба и решила остаться."),
    ("Синдзиро Каваси", "forge", "dream", "Кукловод грёз", "У каждого сна есть швы. Я их вижу."),
    ("Аои Ходзуми", "neon", "star", "Звёздное плечо", "На моём плече всегда кто-то падает. Я не устаю."),
    ("Мицуба Хаяси", "orchid", "forest", "Шёпот бамбука", "Бамбук растёт медленно. Я — тоже."),
    ("Ханадзуки", "hana", "sakura", "Лепестковый дождь", "Я падаю сверху и совсем не жалею."),
    ("Сейра Нисимура", "lumen", "sea", "Буйный прибой", "Не пытайся меня удержать. Я сама приду."),
    ("Юкико Осаки", "snowfall", "snow", "Тихий снег", "Я падаю так тихо, что ты и не заметишь."),
    ("Рэн Цуки", "moonlight", "moon", "Лунный странник", "Я шла два года, чтобы найти тебя."),
    # ---------------- RARE ----------------
    ("Аюми Хаосэ", "hana", "sakura", "Первая краска", "Мой первый рисунок — это ты. Покажи? Ладно."),
    ("Кокоро Матэ", "halo", "moon", "Сердечко на ладони", "Береги меня, а я подарю тебе удачу."),
    ("Юна Каваси", "azure", "sea", "Голубая рябь", "Вода не помнит, но я помню."),
    ("Рин Магокоро", "lumen", "star", "Мерцание", "Смотри долго — начнёшь видеть звёзды в глазу."),
    ("Сидзуку", "orchid", "forest", "Тихая капель", "Я учусь у дерева терпению."),
    ("Мари Тоне", "vermilion", "fire", "Тёплый чай", "Завари меня и выдохни. Серьёзно."),
    ("Анами", "forge", "fire", "Пепельный снег", "После бури я падаю легче пепла."),
    ("Нобуэ", "snowfall", "snow", "Снежная королева снежинок", "Я считаю снежинки. Всегда получается разное число."),
    ("Саруна", "neon", "dream", "Пиксельная мечта", "Мой сон грузится, но красиво."),
    ("Тина Вале", "lumen", "star", "Алый дождь", "Красные капли — это тоже красиво, поверь."),
    ("Юри Кисараги", "moonlight", "rain", "Дождь на клавишах", "Я играю дождь на пианино."),
    ("Хаку", "abyss", "dark", "Белая тень", "Меня почти не видно. Это не баг, это фича."),
    ("Мицуки Аоки", "azure", "rain", "Окно после бури", "За мной всегда окно, за которым дождь."),
    ("Сэрафина Ито", "forge", "dream", "Печь снов", "В моей печи плавятся не руды, а сюжеты."),
    ("Каэдзуки", "hana", "sakura", "Дождь из лепестков", "Закрой глаза, сейчас будет красиво."),
    ("Рим", "halo", "star", "Облако с характером", "Я похожа на облако, но кусаюсь."),
    ("Аяна Гудо", "lumen", "moon", "Луна в кармане", "Я спрятала луну в кармане. Не спрашивай зачем."),
    ("Миако", "orchid", "forest", "Лесная нимфа", "Я появляюсь только там, где растёт мох."),
    ("Эмеи", "vermilion", "fire", "Алый иней", "Мороз у меня бывает алым. Проверишь? Не надо."),
    ("Ичига", "moonlight", "moon", "Сонная луна", "Я не спала сто лет. Зато как спала!"),
    ("Юу", "neon", "star", "Свет из окна", "Мой свет — это свет из окна, в котором горит звезда."),
    ("Рин Кагура", "forge", "fire", "Уголь и лепесток", "Уголь я держу, лепесток — в другой руке."),
    ("Сузу", "snowfall", "snow", "Белая нить", "Я сплетаю снег в нить, а нить — в историю."),
    ("Фуку", "abyss", "dark", "Тихая бездна", "Тишина без дна. Загляни осторожно."),
    # ---------------- COMMON ----------------
    ("Аса", "hana", "sakura", "Лепесток", "Я просто лепесток. Но тёплый."),
    ("Кокоро", "halo", "moon", "Сердечко", "Любовь — это круг. Я в центре."),
    ("Йоши", "azure", "sea", "Морской ветер", "Я пахну морем и слегка йодом."),
    ("Хане", "lumen", "star", "Утренняя звезда", "Я появляюсь на рассвете. Опоздай — ищи в полдень."),
    ("Мидори", "orchid", "forest", "Зелёный чай", "Крепкий, но приятный. Как я."),
    ("Котонэ", "vermilion", "fire", "Тёплое место", "В моём свитере всегда есть дырка для друга."),
    ("Суна", "forge", "fire", "Тёплая искра", "Маленькая, но жжёт по-настоящему."),
    ("Юки", "snowfall", "snow", "Снежинка", "Я падаю медленно, чтобы ты успел рассмотреть."),
    ("Пика", "neon", "dream", "Пиксель", "Я всего один пиксель, но важный."),
    ("Аона", "lumen", "star", "Синий огонёк", "Я светю синим, когда стыдно."),
    ("Марико", "moonlight", "rain", "Дождь в городе", "Город пахнет мной после дождя."),
    ("Хакунэ", "abyss", "dark", "Тихий силуэт", "Меня зовут так же, как мой секрет."),
    ("Юка", "azure", "rain", "Холодный чай", "Остываю за минуту. К счастью, нет."),
    ("Нина", "orchid", "forest", "Сосновая смола", "Я пахну лесом даже в городе."),
    ("Сэйлор Юна", "halo", "star", "Сияние", "Сияю? Нет, просто отражаю. Ну да, сияю."),
    ("Мури", "forge", "dream", "Керамика", "Меня обожгли, но я стала красивой."),
    ("Аэри", "lumen", "sea", "Соль и ветер", "Я на вкус как море. Не пробуй."),
    ("Куна", "hana", "sakura", "Два лепестка", "У меня в косичке ровно два цветка."),
    ("Мирай", "moonlight", "moon", "Лунный камень", "Я тяжелее, чем выгляжу."),
    ("Токо", "vermilion", "fire", "Карамель", "Липкая. В хорошем смысле."),
    ("Юи", "snowfall", "snow", "Морозный узор", "Мой узор не повторяется. Никогда."),
    ("Сэро", "neon", "star", "Экран", "Внутри меня — сорок вкладок и немного счастья."),
    ("Мэйо", "orchid", "forest", "Мох", "Я медленная, но я всегда рядом."),
    ("Хакуби", "abyss", "dark", "Белое пятно", "Говорят, я — выброс. Я считаю это комплиментом."),
    ("Суку", "hana", "sakura", "Снежинка сакуры", "Цвету один раз. Потом — только память."),
    ("Рину", "lumen", "sea", "Прибой", "Я прихожу и ухожу, но всегда по расписанию волн."),
    ("Тицу", "snowfall", "snow", "Хрусталь", "Хрупкая. Поэтому и красивая."),
    ("Ичи", "moonlight", "moon", "Первая луна", "Первая луна месяца — самая тонкая."),
    ("Юури", "forge", "fire", "Искра", "Маленькая, но упрямая."),
    ("Наги", "vermilion", "fire", "Жар", "Сначала тепло. Потом — как в Москве в июле."),
    ("Хонока", "orchid", "forest", "Цветение", "Цвету не по расписанию. По настроению."),
]

LORE_OPEN = [
    "Её нашли в {place}, где {weather}.",
    "Говорят, она появляется только в {weather2} и только для тех, кто {verb}.",
    "Она не помнит, откуда пришла. Только помнит запах {smell}.",
    "Её имя знают в одном районе, где всегда {weather}.",
    "Она пришла из {place}, оставив после себя только {smell}.",
    "С тех пор, как она появилась, {weather2} пахнет по-другому.",
]

PLACES = ["цветущем саду", "заброшенной школе", "на старой станции", "у подножия горы",
          "в книжном магазине", "на крыше небоскрёба", "в ночном переулке", "у озера"]
WEATHER = ["лепестки летели до самой крыши", "небо было розовым до заката", "шёл тихий снег",
           "ветер пах сладким", "дождь звучал как музыка", "воздух светился"]
WEATHER2 = ["сакура цветёт", "идёт дождь из лепестков", "снег идёт второй месяц",
            "в городе горит неон", "по ночам светится море", "всё пахнет жасмином"]
VERBS = ["умеет ждать", "не отводит глаз", "улыбается первым", "верит в чудеса", "не сдаётся"]
SMELL = ["жасмина", "мокрого камня", "сахарной ваты", "дождя по асфальту", "белых лилий"]

CASES = [
    # (name, slug, art_key, price, accent, accent2, tagline, series_focus, tier)
    ("Сакура Ирэн", "sakura-iren", "sakura", 400, "#ff8fb8", "#ffd6e7",
     "Первый лепесток, который учит ждать", "hana", 0),
    ("Лунный Син-эн", "lunno-syn", "moon", 750, "#a5b4fc", "#e0e7ff",
     "Полночный набор для тех, кто не спит", "moonlight", 1),
    ("Ханаби Котоба", "hanabi-kotoba", "kagura", 1000, "#fda4af", "#ffe4e6",
     "Свет фонарей, что зовут по имени", "lumen", 1),
    ("Алый Веер", "akagi-ougi", "fan", 1400, "#fb7185", "#ffe4e6",
     "Один взмах меняет расклад", "vermilion", 1),
    ("Голубой Сад", "aoi-niwa", "lotus", 1900, "#7dd3fc", "#e0f2fe",
     "Тишина, которая звенит", "azure", 1),
    ("Неоновый Токио", "neon-tokio", "neon", 2600, "#c084fc", "#fae8ff",
     "Город, который не выключается никогда", "neon", 2),
    ("Снегопад", "setsugata", "frost", 3400, "#bae6fd", "#f0f9ff",
     "Холодно, красиво, и никто не звонит", "snowfall", 2),
    ("Хвост Кицуне", "kitsune-o", "kitsune", 4400, "#fbbf24", "#fff7ed",
     "Лисы уже считают тебя своим", "abyss", 2),
    ("Оригами", "origami", "origami", 5600, "#f0abfc", "#fdf4ff",
     "Сложи меня, если сможешь", "forge", 2),
    ("Нимб", "haloo", "moon", 7200, "#67e8f9", "#ecfeff",
     "Свет над головой и счастье в кармане", "halo", 3),
    ("Кузня Снов", "kugi-yume", "fan", 9500, "#f472b6", "#fce7f3",
     "Здесь куют сюжеты, а не руды", "forge", 3),
    ("Бездна", "fukaimu", "abyss", 15000, "#818cf8", "#eef2ff",
     "Дно есть у всего. У этого — легенда", "abyss", 4),
]

# case tier -> {rarity: exact percent of the pool that rarity represents}
TIER_BIAS = {
    0: {"sakura": 0.0, "mythic": 0.0, "epic": 4.0, "rare": 26.0, "common": 70.0},
    1: {"sakura": 0.0, "mythic": 2.0, "epic": 12.0, "rare": 30.0, "common": 56.0},
    2: {"sakura": 1.0, "mythic": 5.0, "epic": 19.0, "rare": 32.0, "common": 43.0},
    3: {"sakura": 3.0, "mythic": 10.0, "epic": 25.0, "rare": 30.0, "common": 32.0},
    4: {"sakura": 6.0, "mythic": 16.0, "epic": 27.0, "rare": 28.0, "common": 23.0},
}

# case tier -> how many distinct girls of each rarity live in the pool
TIER_POOL = {
    0: {"sakura": 0, "mythic": 0, "epic": 3, "rare": 6, "common": 9},
    1: {"sakura": 0, "mythic": 2, "epic": 5, "rare": 7, "common": 10},
    2: {"sakura": 1, "mythic": 3, "epic": 6, "rare": 8, "common": 11},
    3: {"sakura": 2, "mythic": 4, "epic": 7, "rare": 8, "common": 11},
    4: {"sakura": 3, "mythic": 5, "epic": 8, "rare": 9, "common": 11},
}



def make_lore(rng: random.Random, name: str, element: str, rarity: str) -> str:
    tpl = rng.choice(LORE_OPEN)
    text = tpl.format(
        place=rng.choice(PLACES),
        weather=rng.choice(WEATHER),
        weather2=rng.choice(WEATHER2),
        verb=rng.choice(VERBS),
        smell=rng.choice(SMELL),
    )
    tail = {
        Rarity.SAKURA: " Её появление совпало с цветением, которое не помнит ни один садовник.",
        Rarity.MYTHIC: " Те, кто видел её дважды, больше не скучают.",
        Rarity.EPIC: " Кто-то увеличил и забыл про пароль.",
        Rarity.RARE: " Она обещает встречу, но не даёт адреса.",
        Rarity.COMMON: " Она просто есть, и это уже хорошо.",
    }[rarity]
    return f"{text}{tail}"


def make_stats(rng: random.Random, rarity: str) -> tuple[int, int, int, int]:
    base = {Rarity.SAKURA: 92, Rarity.MYTHIC: 82, Rarity.EPIC: 70, Rarity.RARE: 58, Rarity.COMMON: 44}[rarity]
    spread = rng.randint(-6, 6)
    def roll(weight):
        return max(12, min(99, base + rng.randint(spread - 4, spread + 4) + weight))
    return roll(4), roll(0), roll(2), roll(-2)


class Command(BaseCommand):
    help = "Seed sakura cases and heroines"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="delete existing data first")

    def handle(self, *args, **options):
        rng = random.Random(20260930)
        if options["flush"]:
            CaseDrop.objects.all().delete()
            Case.objects.all().delete()
            Girl.objects.all().delete()
            self.stdout.write("cleared")

        series_of = {
            "hana": Series.HANA, "moonlight": Series.MOONLIGHT, "vermilion": Series.VERMILION,
            "halo": Series.HALO, "azure": Series.AZURE, "abyss": Series.ABYSS,
            "snowfall": Series.SNOWFALL, "lumen": Series.LUMEN, "orchid": Series.ORCHID,
            "neon": Series.NEON, "forge": Series.FORGE,
        }

        # rarity assignment by position in the curated list
        bounds = [(0, 6, Rarity.SAKURA), (6, 18, Rarity.MYTHIC), (18, 36, Rarity.EPIC),
                  (36, 60, Rarity.RARE), (60, len(GIRLS), Rarity.COMMON)]
        rarity_of = {}
        for a, b, r in bounds:
            for i in range(a, b):
                rarity_of[i] = r

        girls: list[Girl] = []
        for i, (name, sname, ename, title, quote) in enumerate(GIRLS):
            rarity = rarity_of[i]
            p, c, e, s = make_stats(rng, rarity)
            g = Girl.objects.create(
                name=name,
                slug=slugify(f"{name}-{i}")[:100],
                series=series_of[sname],
                rarity=rarity,
                element=ename,
                title=title,
                quote=quote,
                origin=rng.choice(["Япония · Токио", "Япония · Киото", "Север · Хоккайдо",
                                   "Граница · Острова", "Город · Порт"]),
                image_seed=1000 + i * 37,
                power=p, cuteness=c, elegance=e, spirit=s,
                lore=make_lore(rng, name, ename, rarity),
            )
            girls.append(g)

        by_rarity: dict[str, list[Girl]] = {}
        for g in girls:
            by_rarity.setdefault(g.rarity, []).append(g)

        cases: list[Case] = []
        for idx, (name, cslug, art, price, a1, a2, tagline, focus, tier) in enumerate(CASES):
            bias = TIER_BIAS[tier]
            sizes = TIER_POOL[tier]
            pool: list[Girl] = []
            plan: list[tuple[Girl, str]] = []

            for rarity in (Rarity.SAKURA, Rarity.MYTHIC, Rarity.EPIC, Rarity.RARE, Rarity.COMMON):
                want = sizes.get(rarity, 0)
                cands = by_rarity.get(rarity, [])
                if not want or not cands:
                    continue
                take = min(want, len(cands))
                chosen = rng.sample(cands, take)
                pool.extend(chosen)
                plan.extend((g, rarity) for g in chosen)

            # the case's signature series is always represented
            for fg in [g for g in girls if g.series == series_of[focus]][:2]:
                if fg not in pool:
                    pool.append(fg)
                    plan.append((fg, fg.rarity))

            case = Case.objects.create(
                name=name, slug=cslug, art_key=art, price=price, accent=a1, accent2=a2,
                tagline=tagline, sort=idx * 10, badge="НОВЫЙ" if idx >= len(CASES) - 2 else "",
                is_new=idx >= len(CASES) - 2,
                description=(
                    f"{name} — {len(pool)} персонажей, собранных вокруг вселенной "
                    f"«{Series(focus).label}». Чем дороже кейс, тем щедрее шанс на Легенду сакуры. "
                    f"Гарант: легенда выпадает не позже чем через 60 открытий подряд."
                ),
            )
            cases.append(case)

            # split each rarity's exact percentage across the girls of that rarity
            by_r: dict[str, list[Girl]] = {}
            for g, r in plan:
                by_r.setdefault(r, []).append(g)

            for rarity, group in by_r.items():
                budget = bias.get(rarity, 0.0)
                if budget <= 0 or not group:
                    continue
                jittered = [rng.uniform(0.72, 1.32) for _ in group]
                jsum = sum(jittered)
                weights = [budget * j / jsum for j in jittered]
                acc = 0.0
                for i, g in enumerate(group):
                    w = weights[i] if i < len(group) - 1 else budget - acc
                    acc += w
                    CaseDrop.objects.create(case=case, girl=g, weight=Decimal(f"{w:.2f}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: {Girl.objects.count()} девочек, {Case.objects.count()} кейсов, "
                f"{CaseDrop.objects.count()} дропов"
            )
        )
