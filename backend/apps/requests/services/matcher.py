"""Supplier-to-request matching and relevance scoring.

Flow: parse request items -> find suppliers covering those categories ->
score by coverage + distance + rating + profile completeness -> return top 20.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory
from apps.requests.models import Request, Category


@dataclass
class SupplierMatch:
    supplier_id: int
    name: str
    email: str
    phone: str
    site: str
    city: Optional[str]
    distance_km: Optional[float]

    category_score: float
    distance_score: float
    rating_score: float
    completeness_score: float
    manufacturer_bonus: float
    material_type_score: float
    product_match_score: float
    supplier_type: str
    total_score: float

    matched_categories: list[str] = field(default_factory=list)
    total_categories: int = 0
    source: str = "seed"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "site": self.site,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": round(self.distance_km, 1) if self.distance_km else None,
            "total_score": round(self.total_score, 1),
            "category_score": round(self.category_score, 1),
            "distance_score": round(self.distance_score, 1),
            "rating_score": round(self.rating_score, 1),
            "completeness_score": round(self.completeness_score, 1),
            "manufacturer_bonus": round(self.manufacturer_bonus, 1),
            "material_type_score": round(self.material_type_score, 1),
            "product_match_score": round(self.product_match_score, 1),
            "supplier_type": getattr(self, 'supplier_type', 'unknown'),
            "source": getattr(self, 'source', 'seed'),
            "matched_categories": self.matched_categories,
            "matched_count": len(self.matched_categories),
            "total_categories": self.total_categories,
            "score_breakdown": {
                "category": f"{round(self.category_score, 1)} (совпало категорий: {len(self.matched_categories)} из {self.total_categories})",
                "distance": f"{round(self.distance_score, 1)} (расстояние: {self.distance_km:.1f} км)" if self.distance_km else "0 (расстояние не указано)",
                "rating": f"{round(self.rating_score, 1)} (рейтинг поставщика)",
                "completeness": f"{round(self.completeness_score, 1)} (email + телефон + сайт + юр.название)",
                "manufacturer_bonus": f"{round(self.manufacturer_bonus, 1)} (тип: {'Производитель' if self.supplier_type == 'manufacturer' else 'Дилер' if self.supplier_type == 'dealer' else 'Неизвестно'})",
                "material_type": f"{round(self.material_type_score, 1)} (совпадение типа материала)",
                "product_match": f"{round(self.product_match_score, 1)} (товар найден в ассортименте)",
                "total": round(self.total_score, 1),
            }
        }


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _product_match(request_terms, supplier):
    """Check if any request term appears in supplier's product catalog.
    
    Returns (matched: bool, score: float, matched_term: str)
    - If supplier has product_keywords/description and no match -> (False, 0, "")
    - If supplier has product_keywords/description and match -> (True, 20, term)
    - If supplier has no catalog data -> (True, 0, "нет данных") [backward compat]
    """
    keywords = [k.lower().strip() for k in (supplier.product_keywords or []) if k]
    description = (supplier.product_description or "").lower()
    
    # If supplier has no catalog data at all, allow them (backward compatibility)
    if not keywords and not description.strip():
        return True, 0.0, "нет данных об ассортименте"
    
    # Check product_keywords
    for term in request_terms:
        for kw in keywords:
            if term in kw or kw in term:
                return True, 20.0, term
    
    # Check product_description
    for term in request_terms:
        if term in description:
            return True, 20.0, term
    
    # No match found in catalog -> reject
    return False, 0.0, ""


def match_suppliers(request_obj, limit=20):
    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()

    request_categories = list(Category.objects.filter(requestitem__request=request_obj).distinct())
    if not request_categories:
        return []

    # Collect search terms from request items (material_type, name, category name)
    request_material_types = set()
    request_terms = set()  # All terms to search in supplier catalog
    for item in items:
        mt = (item.material_type or "").strip().lower()
        if mt:
            request_material_types.add(mt)
            request_terms.add(mt)
        name = (item.name or "").strip().lower()
        if name and len(name) > 2:
            request_terms.add(name)
        # Add category name if available
        if item.category:
            cat_name = (item.category.name or "").strip().lower()
            if cat_name:
                request_terms.add(cat_name)

    category_ids = set(c.id for c in request_categories)
    max_radius = max(c.default_radius_km for c in request_categories)

    req_lat = req_lon = None
    addr = request_obj.address
    if addr and addr.latitude and addr.longitude:
        req_lat = addr.latitude
        req_lon = addr.longitude

    suppliers = (
        Supplier.objects
        .filter(is_active=True)
        .prefetch_related("addresses", "supplier_categories__category")
    )

    matches = []

    for s in suppliers:
        # === PRODUCT MATCH RULE ===
        # Supplier MUST have the requested product in their catalog (keywords/description)
        has_product, product_score, matched_term = _product_match(request_terms, s)
        if not has_product:
            # Skip suppliers who don't carry this product
            continue

        supplier_category_ids = set(
            sc.category_id for sc in s.supplier_categories.all()
        )
        matched_ids = category_ids & supplier_category_ids
        category_score = 50 * len(matched_ids) / len(category_ids) if category_ids else 0

        matched_names = [
            c.name
            for c in request_categories
            if c.id in matched_ids
        ]

        best_distance = max_radius + 1
        best_city = None
        if req_lat is not None and req_lon is not None:
            for sa in s.addresses.all():
                if sa.latitude and sa.longitude and sa.is_active:
                    d = _haversine(req_lat, req_lon, sa.latitude, sa.longitude)
                    if d < best_distance:
                        best_distance = d
                        best_city = sa.city
        else:
            first_addr = s.addresses.first()
            if first_addr:
                best_city = first_addr.city
                best_distance = None

        distance_score = 0
        if best_distance is not None and best_distance <= max_radius:
            distance_score = 30 * (1 - best_distance / max_radius)

        rating_score = min(s.hidden_rating, 10)

        # Manufacturer bonus: +5 points if they produce the material
        mfr_bonus = 5.0 if s.supplier_type == "manufacturer" else 0

        # Material type bonus: +15 if supplier produces/has the exact material type
        material_type_score = 0
        supplier_mts = set((mt or "").strip().lower() for mt in (s.material_types or []))
        if request_material_types and supplier_mts:
            if request_material_types & supplier_mts:
                material_type_score = 15.0
        # Fallback: check if material_type appears in supplier name
        if material_type_score == 0 and request_material_types:
            name_lower = s.name.lower()
            for mt in request_material_types:
                if mt in name_lower:
                    material_type_score = 10.0
                    break

        completeness = 0
        if s.email:
            completeness += 2.5
        if s.phone:
            completeness += 2.5
        if s.site:
            completeness += 2.5
        if s.legal_name:
            completeness += 2.5

        total = category_score + distance_score + rating_score + completeness + mfr_bonus + material_type_score + product_score

        matches.append(SupplierMatch(
            supplier_id=s.id,
            supplier_type=s.supplier_type,
            source=getattr(s, "source", "seed"),
            name=s.name,
            email=s.email,
            phone=s.phone or "",
            site=s.site or "",
            city=best_city,
            distance_km=best_distance if best_distance and best_distance <= max_radius else None,
            category_score=category_score,
            distance_score=distance_score,
            rating_score=rating_score,
            completeness_score=completeness,
            manufacturer_bonus=mfr_bonus,
            material_type_score=material_type_score,
            product_match_score=product_score,
            total_score=total,
            matched_categories=matched_names,
            total_categories=len(category_ids),
        ))

    matches.sort(key=lambda m: m.total_score, reverse=True)
    return [m.to_dict() for m in matches[:limit]]
