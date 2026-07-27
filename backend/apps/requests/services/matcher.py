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
    supplier_type: str
    total_score: float

    matched_categories: list[str] = field(default_factory=list)
    total_categories: int = 0
    source: str = "seed"

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "site": self.site,
            "city": self.city,
            "distance_km": round(self.distance_km, 1) if self.distance_km else None,
            "total_score": round(self.total_score, 1),
            "category_score": round(self.category_score, 1),
            "distance_score": round(self.distance_score, 1),
            "rating_score": round(self.rating_score, 1),
            "completeness_score": round(self.completeness_score, 1),
            "manufacturer_bonus": round(self.manufacturer_bonus, 1),
            "supplier_type": getattr(self, 'supplier_type', 'unknown'),
            "source": getattr(self, 'source', 'seed'),
            "matched_categories": self.matched_categories,
            "matched_count": len(self.matched_categories),
            "total_categories": self.total_categories,
        }


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def match_suppliers(request_obj, limit=20):
    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()

    request_categories = list(Category.objects.filter(requestitem__request=request_obj).distinct())
    if not request_categories:
        return []

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

        completeness = 0
        if s.email:
            completeness += 2.5
        if s.phone:
            completeness += 2.5
        if s.site:
            completeness += 2.5
        if s.legal_name:
            completeness += 2.5

        total = category_score + distance_score + rating_score + completeness + mfr_bonus

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
            total_score=total,
            matched_categories=matched_names,
            total_categories=len(category_ids),
        ))

    matches.sort(key=lambda m: m.total_score, reverse=True)
    return [m.to_dict() for m in matches[:limit]]
