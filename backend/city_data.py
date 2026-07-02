"""City data with realistic road segments for global cities.
Each city has coordinates, road segments (with realistic road names), and metadata.
"""
import random
from typing import Dict, List, Tuple


def _generate_grid_segments(
    city_key: str,
    center: Tuple[float, float],
    span: float,
    named_roads: List[str],
    num_segments: int = 40,
    seed: int = 42,
) -> List[Dict]:
    """Generate a realistic grid of road segments around a center point.
    Segments form a mesh with named roads.
    """
    rng = random.Random(seed)
    lat0, lng0 = center
    segments = []

    # Build a grid of nodes (7x7)
    grid_size = 7
    step = span / (grid_size - 1)
    nodes = {}
    for i in range(grid_size):
        for j in range(grid_size):
            lat = lat0 - span / 2 + i * step + rng.uniform(-step * 0.15, step * 0.15)
            lng = lng0 - span / 2 + j * step + rng.uniform(-step * 0.15, step * 0.15)
            nodes[(i, j)] = (round(lat, 5), round(lng, 5))

    seg_id = 0
    # Horizontal segments
    for i in range(grid_size):
        for j in range(grid_size - 1):
            name = named_roads[seg_id % len(named_roads)] if seg_id < num_segments else f"{city_key} Road {seg_id}"
            segments.append({
                "id": f"{city_key}-seg-{seg_id}",
                "name": name,
                "from": nodes[(i, j)],
                "to": nodes[(i, j + 1)],
                "from_node": f"{i}-{j}",
                "to_node": f"{i}-{j + 1}",
                "length_km": round(_haversine(nodes[(i, j)], nodes[(i, j + 1)]), 3),
                "lanes": rng.choice([2, 2, 3, 4]),
                "speed_limit": rng.choice([40, 50, 60, 60, 70]),
            })
            seg_id += 1
    # Vertical segments
    for j in range(grid_size):
        for i in range(grid_size - 1):
            name = named_roads[seg_id % len(named_roads)] if seg_id < num_segments else f"{city_key} Ave {seg_id}"
            segments.append({
                "id": f"{city_key}-seg-{seg_id}",
                "name": name,
                "from": nodes[(i, j)],
                "to": nodes[(i + 1, j)],
                "from_node": f"{i}-{j}",
                "to_node": f"{i + 1}-{j}",
                "length_km": round(_haversine(nodes[(i, j)], nodes[(i + 1, j)]), 3),
                "lanes": rng.choice([2, 2, 3, 4]),
                "speed_limit": rng.choice([40, 50, 60, 60, 70]),
            })
            seg_id += 1

    # Return truncated to num_segments
    return segments[:num_segments]


def _haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    from math import radians, sin, cos, asin, sqrt
    lat1, lng1 = a
    lat2, lng2 = b
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    aa = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * 6371 * asin(sqrt(aa))


# Named roads per city for authenticity
_PUNE_ROADS = [
    "FC Road", "JM Road", "MG Road", "Karve Road", "Sinhagad Road",
    "Baner Road", "University Road", "Nagar Road", "Solapur Road",
    "Tilak Road", "Bajirao Road", "Ganeshkhind Road", "Bund Garden Road",
    "North Main Road", "East Street", "Aundh Road", "Kothrud Road",
    "Hadapsar Road", "Katraj Road", "Wakad Road", "Hinjewadi Road",
    "Pashan Road", "Shivajinagar", "Camp Road", "Deccan Road",
]
_NAGPUR_ROADS = [
    "Wardha Road", "Kamptee Road", "Amravati Road", "Hingna Road",
    "Katol Road", "Bhandara Road", "Central Avenue", "North Ambazari",
    "West High Court", "East High Court", "Ring Road", "Sitabuldi",
    "Dhantoli Road", "Dharampeth Road", "Sadar Road", "Mahal Road",
    "Manish Nagar", "Ajni Road", "Pratap Nagar", "Trimurti Nagar",
    "Nandanvan", "Gandhibagh", "Itwari", "Mankapur", "Koradi Road",
]
_MUMBAI_ROADS = [
    "Marine Drive", "Linking Road", "SV Road", "Western Express Hwy",
    "Eastern Express Hwy", "LBS Marg", "Andheri-Kurla Rd", "JVLR",
    "Bandra-Worli Sea Link", "Peddar Road", "Nariman Point", "Colaba Causeway",
    "Hill Road", "Turner Road", "Carter Road", "Juhu Tara Rd",
    "Powai", "Mulund LBS", "Ghatkopar", "Chembur", "Kurla West",
    "Malad Link Rd", "Kandivali", "Borivali", "Dahisar",
]
_DELHI_ROADS = [
    "Ring Road", "Outer Ring Road", "NH-8", "NH-1", "Mathura Road",
    "Rohtak Road", "GT Karnal Road", "MG Road", "Bahadur Shah Zafar Marg",
    "Ashram Chowk", "ITO", "Rajpath", "Janpath", "Aurangzeb Road",
    "Barakhamba Rd", "Connaught Place", "Sansad Marg", "Kalindi Kunj Rd",
    "DND Flyway", "Noida Link Rd", "Vikas Marg", "Karol Bagh",
    "Pusa Road", "Bhikaji Cama", "Nelson Mandela Rd",
]
_LONDON_ROADS = [
    "Oxford Street", "Regent Street", "Piccadilly", "Strand", "Fleet Street",
    "Kensington High St", "Marylebone Rd", "Euston Rd", "Park Lane",
    "Victoria Embankment", "Bishopsgate", "Whitechapel Rd", "Old Kent Rd",
    "Kingsway", "Holborn", "Cheapside", "Farringdon Rd", "Baker Street",
    "Edgware Rd", "Bayswater Rd", "Cromwell Rd", "Fulham Rd",
    "Kings Rd", "Sloane St", "Buckingham Palace Rd",
]
_NYC_ROADS = [
    "5th Avenue", "7th Avenue", "Broadway", "Park Avenue", "Madison Ave",
    "Lexington Ave", "3rd Avenue", "1st Avenue", "West 42nd St",
    "West 34th St", "East 57th St", "Houston St", "Canal St",
    "14th Street", "23rd Street", "West Side Hwy", "FDR Drive",
    "Bowery", "Delancey St", "Grand St", "Lafayette St",
    "Church Street", "Varick St", "Hudson St", "Wall Street",
]
_TOKYO_ROADS = [
    "Chuo Dori", "Meiji Dori", "Yasukuni Dori", "Shinjuku Dori", "Aoyama Dori",
    "Roppongi Dori", "Sotobori Dori", "Uchibori Dori", "Kasuga Dori",
    "Hongo Dori", "Waseda Dori", "Ome Kaido", "Koshu Kaido",
    "Tamagawa Dori", "Kanpachi Dori", "Kannana Dori", "Loop 7",
    "Loop 8", "Rainbow Bridge", "Odaiba Line", "Shuto Expressway",
    "Ginza Dori", "Harajuku Rd", "Shibuya Center", "Akasaka Dori",
]
_SINGAPORE_ROADS = [
    "Orchard Road", "Bukit Timah Rd", "River Valley Rd", "Beach Road",
    "East Coast Pkwy", "Pan Island Expy", "Central Expy", "Ayer Rajah Expy",
    "Bugis St", "Chinatown", "Little India Rd", "Serangoon Rd",
    "Balestier Rd", "Novena Rd", "Newton Circus", "Marina Blvd",
    "Raffles Blvd", "Nicoll Hwy", "Kallang Rd", "Geylang Rd",
    "Jurong East", "Tampines Rd", "Woodlands Rd", "Yishun Ave",
    "Boon Lay Way",
]


CITIES: Dict[str, Dict] = {
    "pune": {
        "key": "pune",
        "name": "Pune",
        "country": "India",
        "center": [18.5204, 73.8567],
        "zoom": 12,
        "tz": "Asia/Kolkata",
        "span": 0.09,
        "roads": _PUNE_ROADS,
    },
    "nagpur": {
        "key": "nagpur",
        "name": "Nagpur",
        "country": "India",
        "center": [21.1458, 79.0882],
        "zoom": 12,
        "tz": "Asia/Kolkata",
        "span": 0.09,
        "roads": _NAGPUR_ROADS,
    },
    "mumbai": {
        "key": "mumbai",
        "name": "Mumbai",
        "country": "India",
        "center": [19.0760, 72.8777],
        "zoom": 12,
        "tz": "Asia/Kolkata",
        "span": 0.11,
        "roads": _MUMBAI_ROADS,
    },
    "delhi": {
        "key": "delhi",
        "name": "Delhi",
        "country": "India",
        "center": [28.6139, 77.2090],
        "zoom": 11,
        "tz": "Asia/Kolkata",
        "span": 0.13,
        "roads": _DELHI_ROADS,
    },
    "london": {
        "key": "london",
        "name": "London",
        "country": "United Kingdom",
        "center": [51.5074, -0.1278],
        "zoom": 12,
        "tz": "Europe/London",
        "span": 0.10,
        "roads": _LONDON_ROADS,
    },
    "nyc": {
        "key": "nyc",
        "name": "New York City",
        "country": "USA",
        "center": [40.7549, -73.9840],
        "zoom": 12,
        "tz": "America/New_York",
        "span": 0.09,
        "roads": _NYC_ROADS,
    },
    "tokyo": {
        "key": "tokyo",
        "name": "Tokyo",
        "country": "Japan",
        "center": [35.6762, 139.6503],
        "zoom": 12,
        "tz": "Asia/Tokyo",
        "span": 0.11,
        "roads": _TOKYO_ROADS,
    },
    "singapore": {
        "key": "singapore",
        "name": "Singapore",
        "country": "Singapore",
        "center": [1.3521, 103.8198],
        "zoom": 12,
        "tz": "Asia/Singapore",
        "span": 0.09,
        "roads": _SINGAPORE_ROADS,
    },
}


_SEG_CACHE: Dict[str, List[Dict]] = {}


def get_segments(city_key: str) -> List[Dict]:
    """Return segments for a city. Prefers real OSM roads (cached), falls back
    to a synthetic grid if OSM is unavailable.
    """
    if city_key not in CITIES:
        raise ValueError(f"Unknown city: {city_key}")
    if city_key not in _SEG_CACHE:
        cfg = CITIES[city_key]
        try:
            from osm_roads import fetch_osm_segments  # local import to avoid cycles
            osm_segs = fetch_osm_segments(
                city_key=cfg["key"],
                center=tuple(cfg["center"]),
                span=cfg["span"],
                max_segments=600,
            )
        except Exception:
            osm_segs = None
        if osm_segs:
            _SEG_CACHE[city_key] = osm_segs
        else:
            _SEG_CACHE[city_key] = _generate_grid_segments(
                city_key=cfg["key"],
                center=tuple(cfg["center"]),
                span=cfg["span"],
                named_roads=cfg["roads"],
                num_segments=84,
                seed=hash(city_key) & 0xFFFFFFFF,
            )
    return _SEG_CACHE[city_key]


def list_cities() -> List[Dict]:
    return [
        {
            "key": c["key"],
            "name": c["name"],
            "country": c["country"],
            "center": c["center"],
            "zoom": c["zoom"],
            "tz": c["tz"],
        }
        for c in CITIES.values()
    ]


def get_city(city_key: str) -> Dict:
    if city_key not in CITIES:
        raise ValueError(f"Unknown city: {city_key}")
    return CITIES[city_key]
