# backend/scripts/dedupe_suppliers.py
"""C2: fuzzy deduplication of suppliers.

Match criteria (any):
- identical non-empty INN
- identical site domain
- normalized name similarity >= 0.85 (difflib)

Merge: addresses, categories, material_types, product keywords move to the
keeper (oldest record / the verified one); the duplicate is deactivated
(is_active=False) — hard delete is avoided to keep quote history intact.

Usage: cd backend && uv run python scripts/dedupe_suppliers.py [--apply]
Without --apply runs in dry-run mode.
"""
import difflib
import os
import re
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory
from apps.quotes.models import Quote, RfqInvitation

APPLY = "--apply" in sys.argv
SIMILARITY = 0.85

LEGAL_FORMS = re.compile(
    r"\b(ооо|зао|оао|пао|ао|ип|гк|мп|нпф|ooo|zao|oao|ip|ltd|llc|группа компаний|gk)\b", re.I)


def norm_name(name: str) -> str:
    n = name.lower()
    n = re.sub(r"[«»\"'()`]", " ", n)
    n = LEGAL_FORMS.sub(" ", n)
    n = re.sub(r"[^a-zа-я0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def norm_site(site: str) -> str:
    if not site:
        return ""
    s = site.lower()
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"^www\.", "", s)
    return s.split("/")[0]


def pick_keeper(group):
    """Verified > unverified; then most complete; then oldest."""
    def score(s):
        completeness = sum(bool(x) for x in (s.email, s.phone, s.site, s.legal_name, s.inn))
        verified = 1 if s.moderation_status == "verified" else 0
        return (verified, completeness, -s.id)
    return sorted(group, key=score, reverse=True)[0]


def merge(keeper, dupe, report):
    moved_addr = moved_cat = 0
    for addr in SupplierAddress.objects.filter(supplier=dupe):
        addr.supplier = keeper
        addr.save(update_fields=["supplier"])
        moved_addr += 1
    for sc in SupplierCategory.objects.filter(supplier=dupe):
        if SupplierCategory.objects.filter(supplier=keeper, category=sc.category).exists():
            sc.delete()
        else:
            sc.supplier = keeper
            sc.save(update_fields=["supplier"])
            moved_cat += 1
    # Preserve tender history: re-link quotes and invitations to the keeper
    Quote.objects.filter(supplier=dupe).update(supplier=keeper)
    RfqInvitation.objects.filter(supplier=dupe).update(supplier=keeper)
    # Union of material types / keywords
    for field in ("material_types", "product_keywords"):
        merged = list(getattr(keeper, field) or [])
        for v in getattr(dupe, field) or []:
            if v and v.lower() not in [x.lower() for x in merged]:
                merged.append(v)
        if merged != (getattr(keeper, field) or []):
            setattr(keeper, field, merged)
            keeper.save(update_fields=[field])
    # Fill empty keeper fields from the dupe
    for field in ("email", "phone", "site", "legal_name", "inn", "product_description"):
        if not getattr(keeper, field) and getattr(dupe, field):
            setattr(keeper, field, getattr(dupe, field))
            keeper.save(update_fields=[field])
    dupe.is_active = False
    dupe.save(update_fields=["is_active"])
    report.append(
        f"- «{dupe.name}» (id={dupe.id}) → «{keeper.name}» (id={keeper.id}): "
        f"адресов {moved_addr}, категорий {moved_cat}, дубликат деактивирован")


def names_are_dupes(a: str, b: str) -> bool:
    """True only when names differ by typos/variants of the SAME tokens.
    Prevents false positives like «Подольский ДОК» vs «Подольский Дом»:
    unmatched tokens must pair up with similarity >= 0.85."""
    if a == b:
        return True
    if difflib.SequenceMatcher(None, a, b).ratio() < SIMILARITY:
        return False
    ta, tb = a.split(), b.split()
    unmatched_a = [t for t in ta if t not in tb]
    unmatched_b = [t for t in tb if t not in ta]
    if not unmatched_a and not unmatched_b:
        return True  # same tokens, different order
    if len(unmatched_a) != len(unmatched_b):
        return False
    remaining = list(unmatched_b)
    for token in unmatched_a:
        best_i, best_sim = -1, 0.0
        for i, other in enumerate(remaining):
            sim = difflib.SequenceMatcher(None, token, other).ratio()
            if sim > best_sim:
                best_i, best_sim = i, sim
        if best_sim < SIMILARITY:
            return False
        remaining.pop(best_i)
    return True


def main():
    suppliers = list(Supplier.objects.filter(is_active=True))
    # Build candidate groups
    groups = []
    used = set()

    by_inn = {}
    by_site = {}
    for s in suppliers:
        if s.inn:
            by_inn.setdefault(s.inn, []).append(s)
        site = norm_site(s.site)
        if site:
            by_site.setdefault(site, []).append(s)

    def add_group(members):
        ids = frozenset(m.id for m in members)
        if len(ids) > 1 and ids not in used:
            used.add(ids)
            groups.append(list(members))

    for members in list(by_inn.values()) + list(by_site.values()):
        add_group(members)

    # Fuzzy name matching
    norms = [(s, norm_name(s.name)) for s in suppliers]
    for i in range(len(norms)):
        for j in range(i + 1, len(norms)):
            si, ni = norms[i]
            sj, nj = norms[j]
            if not ni or not nj:
                continue
            if names_are_dupes(ni, nj):
                add_group([si, sj])

    report = []
    for group in groups:
        # Merge with any existing group members transitively: keep it simple —
        # keeper is chosen per group; dupes deactivated
        keeper = pick_keeper(group)
        for s in group:
            if s.id != keeper.id and s.is_active:
                if APPLY:
                    merge(keeper, s, report)
                else:
                    report.append(f"- [dry-run] «{s.name}» (id={s.id}) → «{keeper.name}» (id={keeper.id})")

    header = "# Дедупликация поставщиков (C2)\n\n"
    header += f"Активных поставщиков проверено: {len(suppliers)}. "
    header += f"Найдено групп дублей: {len(groups)}. Режим: {'APPLY' if APPLY else 'dry-run'}.\n\n"
    body = "\n".join(report) if report else "Дублей не найдено."
    print(header + body)

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "docs", "DEDUP_REPORT.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(header + body + "\n")
    print("\nWritten:", out)


if __name__ == "__main__":
    main()
