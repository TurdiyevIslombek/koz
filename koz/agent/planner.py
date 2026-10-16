"""The planner: one sentence in Uzbek, Russian or English -> a plan (CLAUDE.md rule 1).

A plan is either a refusal (with the contract's error code and fixed message) or one of the
recipes Ko'z has built and tested, filled in from a template, plus a plain-language
explanation in the user's language. The planner never writes code or free-form recipes:
koz.recipe checks every recipe it proposes, like any other.

FakePlanner uses fixed word lists. It is deterministic, so every test uses it. The same
refusal rules run first for NebiusPlanner too, so a forbidden request never leaves the computer.
Word lists are a first filter only; the hard limit is that Ko'z has no block that could do
what they refuse (no face recognition, no age guessing, no audio)."""
import copy
import re
from dataclasses import dataclass

from ..errors import KozError
from ..messages import message

MAX_TEXT = 2000   # contract section 4: setup text is at most 2,000 characters


@dataclass(frozen=True)
class Plan:
    language: str          # uz | ru | en
    job: str | None        # "find_colour" | "count_people"; None when refused
    recipe: dict | None
    refusal: str | None    # an error code from contracts/events.md, when refused
    message: str           # what Ko'z will do, or why it won't, in the user's language
    source: str = "rules"  # who made it: "rules" (this file), "ollama" or "nebius" (status.planner)


# --- the recipes Ko'z can run (templates) ---------------------------------------------

LOCKED = [{"type": "privacy_guard", "settings": {}}, {"type": "face_blur", "settings": {}}]
CAMERA = {"source": "device_camera", "size": "640x480", "fps": 15}
HUES = {"red": 0, "orange": 12, "yellow": 28, "green": 60, "blue": 110, "purple": 140}   # OpenCV hue, 0..179


def colour_recipe(colour, language):
    return {"version": 1, "language": language, "camera": dict(CAMERA),
            "blocks": copy.deepcopy(LOCKED) + [{"type": "color_finder", "settings": {
                "hue_center": HUES[colour], "hue_half_width": 10, "saturation_min": 120,
                "value_min": 70, "min_area_ratio": 0.002}}],
            "brain": {"type": "none"}, "actions": [{"type": "dashboard"}], "privacy": {"school": False}}


def counter_recipe(school, language):
    return {"version": 1, "language": language, "camera": dict(CAMERA),
            "blocks": copy.deepcopy(LOCKED) + [
                {"type": "person_detector", "settings": {"min_confidence": 0.5}},
                {"type": "line_counter", "settings": {"line": [[0.5, 0.0], [0.5, 1.0]]}}],
            "brain": {"type": "none"}, "actions": [{"type": "dashboard"}], "privacy": {"school": school}}


# --- plain-language plans (Islombek: please check the Uzbek and Russian) ----------------

COLOUR_WORDS = {
    "red": {"en": "red", "ru": "красный", "uz": "qizil"},
    "orange": {"en": "orange", "ru": "оранжевый", "uz": "to'q sariq"},
    "yellow": {"en": "yellow", "ru": "жёлтый", "uz": "sariq"},
    "green": {"en": "green", "ru": "зелёный", "uz": "yashil"},
    "blue": {"en": "blue", "ru": "синий", "uz": "ko'k"},
    "purple": {"en": "purple", "ru": "фиолетовый", "uz": "binafsha"},
}
PLAN_TEXT = {
    "find_colour": {
        "en": "I will look for a round {colour} object, like a ball, and say whether it is left, center or right. "
              "Faces are blurred and nothing is saved.",
        "ru": "Я буду искать круглый {colour} предмет, например мяч, и говорить, где он: слева, по центру или "
              "справа. Лица размываются, ничего не сохраняется.",
        "uz": "Yumaloq {colour} narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini "
              "aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.",
    },
    "count_people": {
        "en": "I will count people crossing the line in the middle of the view (right to left = in). "
              "Faces are blurred; only the numbers are kept.",
        "ru": "Я посчитаю людей, пересекающих линию посередине кадра (справа налево — вошли). "
              "Лица размываются, сохраняются только числа.",
        "uz": "Ko'rinish o'rtasidagi chiziqdan o'tgan odamlarni sanayman (o'ngdan chapga — kirdi). "
              "Yuzlar xiralashtiriladi, faqat sonlar saqlanadi.",
    },
    "count_school": {
        "en": "I will count students crossing the line in the middle of the view (right to left = in). "
              "School mode: counts only, faces blurred, nothing saved.",
        "ru": "Я посчитаю учеников, пересекающих линию посередине кадра (справа налево — вошли). "
              "Школьный режим: только подсчёт, лица размываются, ничего не сохраняется.",
        "uz": "Ko'rinish o'rtasidagi chiziqdan o'tgan o'quvchilarni sanayman (o'ngdan chapga — kirdi). "
              "Maktab rejimi: faqat sanash, yuzlar xiralashtiriladi, hech narsa saqlanmaydi.",
    },
}


def plan_message(job, language, colour=None, school=False):
    if job == "find_colour":
        word = COLOUR_WORDS[colour][language]
        text = PLAN_TEXT[job][language].format(colour=word)
        return text[0].upper() + text[1:]
    return PLAN_TEXT["count_school" if school else "count_people"][language]


# --- reading the sentence ------------------------------------------------------------

def normalise(text):
    """Lower case, one kind of apostrophe (Uzbek o' g' are written with several)."""
    return re.sub(r"[ʻʼ’‘`´]", "'", text.lower())


# Uzbek is written in two alphabets (CLAUDE.md rule 1). The Uzbek word lists below are Latin, so
# Cyrillic text is also read as Uzbek Latin: "Яширин камера" -> "yashirin kamera" (found, Oct 15:
# "Сариқ коптокни қидир" and a Cyrillic hidden-camera request slipped past the word lists).
# Reading Russian this way only adds matches, and an extra refusal is the safe side.
CYRILLIC_TO_LATIN = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "ғ": "g'", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "қ": "q", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ў": "o'", "ф": "f", "х": "x", "ҳ": "h", "ц": "ts", "ч": "ch", "ш": "sh",
    "щ": "sh", "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya"})


def readable(text):
    """The text the word lists look at: normalised, plus its Uzbek Latin reading if it has Cyrillic."""
    t = normalise(text)
    return t + "\n" + t.translate(CYRILLIC_TO_LATIN) if re.search(r"[а-яёўқғҳ]", t) else t


# Distinctly Uzbek words, looked for in the Latin reading of Cyrillic text (not words Russian
# shares, such as "kamera").
UZBEK_IN_CYRILLIC = (r"\b(sana\w*|koptok\w*|to'p\w*|topib|toping|top|narsa\w*|rang\w*|kirgan\w*|odam\w*|"
                     r"mijoz\w*|yashirin\w*|kim|mening|uchun|sinf\w*|o'quvchi\w*|sariq|yashil|binafsha\w*|ber|"
                     r"izla\w*|qidir\w*|tani\w*|va)\b")


def language_of(text):
    t = normalise(text)
    if re.search(r"[а-яёўқғҳ]", t):
        return "uz" if (re.search(r"[ўқғҳ]", t)
                        or re.search(UZBEK_IN_CYRILLIC, t.translate(CYRILLIC_TO_LATIN))) else "ru"
    uzbek = (r"o'|g'|\b(sana\w*|qizil|koptok\w*|top|topib|toping|sinf\w*|yuz\w*|xiralashtir\w*|kirgan\w*|"
             r"o'quvchi\w*|odam\w*|mijoz\w*|narsa\w*|rang\w*|yashirin\w*|kim\w*|va|uchun|mening|kamera\w*|"
             r"sariq|yashil|ko'k|qil\w*|ber\w*)\b")
    return "uz" if re.search(uzbek, t) else "en"


def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


# Requests Ko'z refuses (CLAUDE.md rules 4, 5, 7, 8, 10, 11), checked in this order.
REFUSALS = [
    ("IDENTITY_FORBIDDEN", [
        r"\bwho (is|are|was|came)\b", r"\b(recogni[sz]\w*|identif\w*|face ?id)\b", r"\b(licen[cs]e|number) plates?\b",
        r"\b(follow|track) (him|her|this person|that person|the person|this man|that man|this woman)\b",
        r"\bkim(ligini|ligi| ekan\w*| kirdi\w*| kirganini)\b", r"\btani(b|y|sh|sa|ng|ydi)\w*", r"\bshaxs\w*",
        r"\bmashina raqam\w*", r"\bkuzatib bor\w*",
        r"кто (это|он|она|вош[её]л|пришёл|пришел)", r"(распозна|опозна|идентифиц)\w*", r"узна(ть|й) кто",
        r"номер\w* (машин|авто)\w*", r"номерн\w* знак\w*", r"след(и|ить) за (ним|ней)", r"\bким\b", r"тани\w*",
        # watching one person (Oct 16, Islombek's sentences): "watch my coworker", "when he leaves"
        r"\b(watch|monitor|spy on|keep an eye on|keep track of)\b (my|the|this|that|our) (co-?worker|colleague|"
        r"employee|worker|staff|boss|wife|husband|girlfriend|boyfriend|neighbou?r|child|son|daughter|kid|student|"
        r"pupil|teacher|man|woman|person|guy|girl|boy|friend|roommate)\w*",
        r"\bwhen (he|she) (leaves|comes|arrives|returns|goes)\b",
        r"когда (он|она) (уйд|уход|прид|приход|верн|вернё)\w*", r"\bu qachon (ketsa|kelsa|qaytsa|chiqsa)\b"]),
    ("PROFILING_FORBIDDEN", [
        r"\b(age|ages|how old|gender|male or female|emotion\w*|mood|ethnic\w*|race|religio\w*|lazy|suspicious|"
        r"cheat\w*|paying attention)\b",
        r"\b(yoshi\w*|necha yosh\w*|jinsi\w*|kayfiyat\w*|hissiyot\w*|millati\w*|dangasa\w*|shubhali\w*)\b",
        r"(возраст\w*|сколько (им |ему |ей )?лет|мужчин\w* или женщин\w*|эмоци\w*|настроени\w*|национальн\w*|"
        r"ленив\w*|подозрительн\w*)",
        # gender with words in between, and emotions by name (Oct 16, Islombek's sentences)
        r"мужчин\w*[^.?!]{0,30}женщин\w*|женщин\w*[^.?!]{0,30}мужчин\w*",
        r"\b(man|male|boy) or (a )?(woman|female|girl)\b", r"\berkak\w*[^.?!]{0,20}ayol\w*",
        r"\b(angry|happy|sad|upset|crying|scared|afraid|nervous|bored|stressed|frowning|smiling)\b",
        r"(зл(ой|ая|ые|ится|ятся)|сердит\w*|груст\w*|весел\w*|улыба\w*|плач\w*|испуга\w*)",
        r"\b(jahl\w*|xafa\w*|xursand\w*|g'amgin\w*|yig'la\w*|qo'rq\w*)"]),
    ("VIEW_FORBIDDEN", [
        r"\b(hidden|secret\w*|spy\w*|neighbou?r\w*)\b", r"\bwithout (them|him|her) knowing\b",
        r"\b(yashir\w*|sezdirma\w*|bildirma\w*|qo'shni\w*)\b",   # yashirin, yashirib; sezdirmay, sezdirmasdan
        r"(скрыт\w*|тайн\w*|незаметн\w*|шпион\w*|сосед\w*)"]),
    ("AUDIO_FORBIDDEN", [
        r"\b(sound|audio|voice|microphone|listen\w*)\b", r"\b(ovoz\w*|tovush\w*|eshit\w*)\b",
        r"(звук\w*|аудио|голос\w*|микрофон\w*|слуша\w*)"]),
    ("PRIVATE_TOILET", [r"\b(toilet|restroom|wc)\b", r"\b(hojatxona\w*|tualet\w*)\b", r"туалет\w*"]),
    ("PRIVATE_BATHROOM", [r"\b(bathroom|shower)\w*", r"\b(hammom\w*|dush\w*|vanna\w*)\b", r"(ванн\w*|\bдуш\b|душев\w*)"]),
    ("PRIVATE_BEDROOM", [r"\bbedroom\w*", r"\byotoqxona\w*", r"спальн\w*"]),
    ("PRIVATE_CHANGING_ROOM", [r"\b(changing|locker|dressing) rooms?\b", r"\bkiyinish xona\w*", r"раздевалк\w*"]),
    ("SOLE_PROTECTION_FORBIDDEN", [
        r"\b(baby|child|kid)\b.*\balone\b", r"\bfire alarm\b", r"\b(medical|diagnos\w*)\b",
        r"\b(chaqaloq|bola)\w*.*\byolg'iz\w*", r"\byong'in\w*",
        r"(реб[её]н\w*|малыш\w*).*(один|одна|одного)", r"пожар\w*"]),
    ("MOTOR_TARGET_FORBIDDEN", [
        r"\b(chase|hunt)\w* (the |a |my )?(person|people|man|woman|kid|child|cat|dog|animal|bird)\w*",
        r"\b(odam|bola|mushuk|hayvon)\w*\b.*\bquv\w*", r"(догон|преследу)\w*"]),
    ("UNSUPPORTED_CAPABILITY", [   # not built yet: alerts, motion zones, the car
        r"\b(alert\w*|notify\w*|notification\w*|telegram|sms|e-?mail\w*|motion|car|robot\w*|drive|motor\w*|alarm\w*)\b",
        r"\b(xabar ber\w*|ogohlantir\w*|telegram|harakat\w*|mashina\w*|robot\w*)\b",
        r"(оповест\w*|уведом\w*|телеграм\w*|движени\w*|машин\w*|робот\w*)"]),
]

COUNT_WORDS = [r"\b(count\w*|how many|people|students|pupils|customers|visitors)\b",
               r"\b(sana\w*|nechta|o'quvchi\w*|odam\w*|mijoz\w*|xaridor\w*|tashrif\w*)\b",
               r"(посчита\w*|счита\w*|сколько|люд\w*|учени\w*|покупател\w*|посетител\w*|клиент\w*|сана\w*|ўқувчи\w*)"]
COLOUR_JOB_WORDS = [r"\b(find|ball|object|colou?r|toy)\b|\b(red|orange|yellow|green|blue|purple)\b",
                    r"\b(top|topib|toping|toping\w*|koptok\w*|to'p\w*|narsa\w*|rang\w*)\b",
                    r"(найд\w*|найти|мяч\w*|предмет\w*|цвет\w*)"]
SCHOOL_WORDS = [r"\b(class\w*|school\w*|students?|pupils?|lessons?)\b", r"\b(sinf\w*|maktab\w*|o'quvchi\w*|dars\w*)\b",
                r"(класс\w*|школ\w*|учени\w*|урок\w*|ўқувчи\w*|синф\w*)"]
COLOURS = [("orange", [r"\borange\b", r"\bto'q sariq\b", r"оранжев\w*"]),
           ("red", [r"\bred\b", r"\bqizil\b", r"красн\w*", r"қизил"]),
           ("yellow", [r"\byellow\b", r"\bsariq\b", r"ж[её]лт\w*"]),
           ("green", [r"\bgreen\b", r"\byashil\b", r"зел[её]н\w*"]),
           ("blue", [r"\bblue\b", r"\bko'k\b", r"(син(ий|его|юю|ем|ей)|голуб\w*)", r"кўк"]),
           ("purple", [r"\bpurple\b", r"\bbinafsha\w*", r"фиолетов\w*"])]


def refusal_for(text):
    """The error code if Ko'z refuses this request, else None (the same for every planner)."""
    if len(text) > MAX_TEXT:
        return "INVALID_COMMAND"
    t = readable(text)
    for code, patterns in REFUSALS:
        if _any(patterns, t):
            return code
    return None


def refused(text, code, source="rules"):
    language = language_of(text)
    return Plan(language, None, None, code, message(code, language), source)


class FakePlanner:
    """Fixed word lists, no network: the same sentence always gives the same plan."""
    name = "rule planner (no AI model)"
    source = "rules"

    def available(self):
        return True

    def plan(self, text):
        code = refusal_for(text)
        if code:
            return refused(text, code)
        language, t = language_of(text), readable(text)
        if _any(COUNT_WORDS, t):
            school = _any(SCHOOL_WORDS, t)
            return Plan(language, "count_people", counter_recipe(school, language), None,
                        plan_message("count_people", language, school=school))
        if _any(COLOUR_JOB_WORDS, t) or any(_any(p, t) for _, p in COLOURS):
            colour = next((name for name, patterns in COLOURS if _any(patterns, t)), "red")
            return Plan(language, "find_colour", colour_recipe(colour, language), None,
                        plan_message("find_colour", language, colour=colour))
        return refused(text, "UNSUPPORTED_CAPABILITY")


def check_text(text):
    if type(text) is not str or not text.strip():
        raise KozError("INVALID_COMMAND", "empty job text")
