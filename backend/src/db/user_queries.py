"""
src/db/user_queries.py — queries para usuarios, librería y wishlist.

FIX: DuckDB lanza BinderException cuando se mezclan parámetros '?' con
     CURRENT_TIMESTAMP en la misma cláusula VALUES.
     Solución: pasar datetime.now() como parámetro Python explícito.
"""
import logging
import math
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ── Detección de géneros por palabras clave en el título ──────────────────────
GENRE_KEYWORDS = {
    "RPG":        ["rpg", "role", "quest", "legend", "fantasy", "dragon", "souls",
                   "elder", "witcher", "baldur", "divinity", "pathfinder"],
    "FPS":        ["fps", "shooter", "counter", "strike", "doom", "halo", "warzone",
                   "battlefield", "call of duty", "titanfall", "apex", "valorant"],
    "Strategy":   ["strategy", "civilization", "total war", "stellaris", "crusader",
                   "tropico", "anno", "age of", "command", "xcom", "endless"],
    "Action":     ["action", "batman", "spider", "assassin", "devil may cry",
                   "sekiro", "nioh", "hack", "slash", "brawl", "beat"],
    "Survival":   ["survival", "rust", "ark", "forest", "don't starve", "valheim",
                   "subnautica", "stranded", "green hell", "the long dark"],
    "Racing":     ["racing", "forza", "need for speed", "dirt", "f1", "nascar",
                   "gran turismo", "assetto", "wreckfest", "rally"],
    "Simulation": ["simulator", "simulation", "farming", "cities", "planet",
                   "euro truck", "flight", "train", "sims", "stardew"],
    "Horror":     ["horror", "resident evil", "silent hill", "outlast", "amnesia",
                   "alien", "fear", "dead", "evil", "nightmare", "terror"],
    "Sports":     ["fifa", "pes", "nba", "nhl", "nfl", "mlb", "football",
                   "soccer", "tennis", "golf", "sports"],
    "Indie":      ["hollow knight", "celeste", "hades", "dead cells", "shovel knight",
                   "cuphead", "ori ", "undertale", "stardew", "terraria"],
    "Adventure":  ["adventure", "journey", "life is strange", "walking dead",
                   "wolf among", "detroit", "beyond", "heavy rain", "telltale"],
    "MOBA":       ["dota", "league", "smite", "heroes of", "moba", "arena"],
}


def _detect_genres(title: str) -> list[str]:
    """Detecta géneros probables de un juego por su título."""
    if not title:
        return []
    t = title.lower()
    return [genre for genre, keywords in GENRE_KEYWORDS.items()
            if any(kw in t for kw in keywords)]


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _san(d: dict) -> dict:
    return {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
            for k, v in d.items()}


def upsert_user(con, steam_id: str, display_name: str, avatar_url: str, profile_url: str):
    now = _now()
    con.execute("""
        INSERT INTO users (steam_id, display_name, avatar_url, profile_url, last_login)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (steam_id) DO UPDATE SET
            display_name = excluded.display_name,
            avatar_url   = excluded.avatar_url,
            profile_url  = excluded.profile_url,
            last_login   = excluded.last_login
    """, [steam_id, display_name, avatar_url, profile_url, now])


def get_user(con, steam_id: str) -> Optional[dict]:
    row = con.execute("SELECT * FROM users WHERE steam_id = ?", [steam_id]).fetchdf()
    return _san(row.iloc[0].to_dict()) if not row.empty else None


def sync_user_library(con, steam_id: str, games: list[dict]) -> int:
    if not games:
        return 0
    inserted = 0
    now = _now()
    for g in games:
        try:
            last_played = None
            if g.get("last_played") and int(g["last_played"]) > 0:
                last_played = datetime.fromtimestamp(int(g["last_played"]))
            con.execute("""
                INSERT INTO user_games (steam_id, appid, game_title, playtime_mins, last_played, synced_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (steam_id, appid) DO UPDATE SET
                    game_title    = excluded.game_title,
                    playtime_mins = excluded.playtime_mins,
                    last_played   = excluded.last_played,
                    synced_at     = excluded.synced_at
            """, [steam_id, g["appid"], g.get("title"), g.get("playtime_mins", 0), last_played, now])
            inserted += 1
        except Exception as e:
            logger.debug(f"sync_user_library error appid={g.get('appid')}: {e}")
    return inserted


def sync_user_wishlist(con, steam_id: str, items: list[dict]) -> int:
    if not items:
        return 0
    inserted = 0
    now = _now()
    for item in items:
        try:
            con.execute("""
                INSERT INTO user_wishlist (steam_id, appid, game_title, added_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (steam_id, appid) DO NOTHING
            """, [steam_id, item["appid"], item.get("title"), now])
            inserted += 1
        except Exception as e:
            logger.debug(f"sync_user_wishlist error appid={item.get('appid')}: {e}")
    return inserted


def get_user_library(con, steam_id: str) -> list[dict]:
    rows = con.execute("""
        SELECT
            ug.appid,
            ug.game_title,
            ug.playtime_mins,
            ug.last_played,
            g.id                             AS game_id,
            COALESCE(ps.min_price, 0)        AS min_price,
            COALESCE(ps.avg_price, 0)        AS avg_price,
            COALESCE(ps.max_discount, 0)     AS max_discount,
            COALESCE(ps.total_records, 0)    AS total_records
        FROM user_games ug
        LEFT JOIN games g ON g.appid = ug.appid
        LEFT JOIN (
            SELECT game_id,
                   MIN(price_usd) AS min_price,
                   AVG(price_usd) AS avg_price,
                   MAX(cut_pct)   AS max_discount,
                   COUNT(*)       AS total_records
            FROM price_history
            WHERE (shop_id = 61 OR LOWER(shop_name) LIKE '%steam%')
            GROUP BY game_id
        ) ps ON ps.game_id = g.id
        WHERE ug.steam_id = ?
        ORDER BY ug.playtime_mins DESC
    """, [steam_id]).fetchdf()
    return [_san(r) for r in rows.to_dict(orient="records")]


def get_user_wishlist_with_prices(con, steam_id: str) -> list[dict]:
    rows = con.execute("""
        WITH latest AS (
            SELECT game_id, price_usd, regular_usd, cut_pct,
                   ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY timestamp DESC) AS rn
            FROM price_history
            WHERE (shop_id = 61 OR LOWER(shop_name) LIKE '%steam%')
        )
        SELECT
            uw.appid,
            uw.game_title,
            uw.added_at,
            g.id                             AS game_id,
            COALESCE(lp.price_usd, 0)        AS current_price,
            COALESCE(lp.cut_pct, 0)          AS discount_pct,
            COALESCE(ps.min_price, 0)        AS all_time_low,
            COALESCE(ps.avg_price, 0)        AS avg_price,
            pc.score,
            pc.signal
        FROM user_wishlist uw
        LEFT JOIN games g ON g.appid = uw.appid
        LEFT JOIN (SELECT * FROM latest WHERE rn = 1) lp ON lp.game_id = g.id
        LEFT JOIN (
            SELECT game_id,
                   MIN(price_usd) AS min_price,
                   AVG(price_usd) AS avg_price
            FROM price_history
            WHERE (shop_id = 61 OR LOWER(shop_name) LIKE '%steam%')
            GROUP BY game_id
        ) ps ON ps.game_id = g.id
        LEFT JOIN predictions_cache pc ON pc.game_id = g.id
        WHERE uw.steam_id = ?
        ORDER BY COALESCE(pc.score, 0) DESC, COALESCE(lp.cut_pct, 0) DESC
    """, [steam_id]).fetchdf()
    return [_san(r) for r in rows.to_dict(orient="records")]


def get_user_owned_appids(con, steam_id: str) -> set:
    rows = con.execute(
        "SELECT appid FROM user_games WHERE steam_id = ?", [steam_id]
    ).fetchdf()
    return set(rows["appid"].tolist()) if not rows.empty else set()


def _build_user_profile(con, steam_id: str) -> dict:
    """
    Construye el perfil de gustos del usuario a partir de su librería.
    Retorna:
      - genre_weights: {genre: peso_normalizado} basado en playtime
      - price_sensitivity: precio promedio que el usuario paga
      - top_titles: set de títulos jugados (para detección de similares)
      - total_playtime: horas totales jugadas
    """
    rows = con.execute("""
        SELECT game_title, playtime_mins
        FROM user_games
        WHERE steam_id = ? AND playtime_mins > 0
        ORDER BY playtime_mins DESC
        LIMIT 200
    """, [steam_id]).fetchdf()

    if rows.empty:
        return {"genre_weights": {}, "price_sensitivity": 20.0,
                "top_titles": set(), "total_playtime": 0}

    genre_playtime: dict[str, float] = {}
    total_playtime = float(rows["playtime_mins"].sum())

    for _, row in rows.iterrows():
        title = row["game_title"] or ""
        mins  = float(row["playtime_mins"] or 0)
        genres = _detect_genres(title)
        for genre in genres:
            genre_playtime[genre] = genre_playtime.get(genre, 0) + mins

    # Normalizar a pesos 0-1
    max_pt = max(genre_playtime.values()) if genre_playtime else 1
    genre_weights = {g: round(pt / max_pt, 3) for g, pt in genre_playtime.items()}

    # Precio promedio pagado (de los juegos que están en nuestra DB)
    price_row = con.execute("""
        SELECT AVG(ph.regular_usd) AS avg_paid
        FROM user_games ug
        JOIN games g ON g.appid = ug.appid
        JOIN price_history ph ON ph.game_id = g.id
        WHERE ug.steam_id = ?
          AND ph.regular_usd > 0
          AND (ph.shop_id = 61 OR LOWER(ph.shop_name) LIKE '%steam%')
    """, [steam_id]).fetchone()
    price_sensitivity = float(price_row[0] or 20.0) if price_row else 20.0

    top_titles = set(rows["game_title"].str.lower().dropna().tolist())

    return {
        "genre_weights":   genre_weights,
        "price_sensitivity": price_sensitivity,
        "top_titles":      top_titles,
        "total_playtime":  total_playtime / 60,  # en horas
    }


def get_recommendations(con, steam_id: str, limit: int = 24) -> list[dict]:
    """
    Recomendaciones personalizadas combinando:
    - ML score (precio + momento de compra)
    - Affinity score (géneros del usuario basado en playtime)
    - Precio compatible con lo que el usuario suele pagar
    - Excluye juegos ya poseídos o en wishlist
    """
    # ── 1. Perfil del usuario ─────────────────────────────────────────────────
    profile = _build_user_profile(con, steam_id)
    genre_weights   = profile["genre_weights"]
    price_threshold = profile["price_sensitivity"] * 1.5  # hasta 50% más de lo que suele pagar
    has_profile     = bool(genre_weights)

    # ── 2. Candidatos: BUY signal + no poseídos + no en wishlist ─────────────
    rows = con.execute("""
        WITH owned AS (
            SELECT appid FROM user_games    WHERE steam_id = ?
            UNION ALL
            SELECT appid FROM user_wishlist WHERE steam_id = ?
        ),
        latest AS (
            SELECT game_id, price_usd, cut_pct,
                   ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY timestamp DESC) AS rn
            FROM price_history
            WHERE (shop_id = 61 OR LOWER(shop_name) LIKE '%steam%')
        )
        SELECT
            g.id, g.title, g.appid,
            pc.score        AS ml_score,
            pc.signal,
            pc.reason,
            COALESCE(lp.price_usd, 0)  AS current_price,
            COALESCE(lp.cut_pct, 0)    AS discount_pct,
            COALESCE(ps.min_price, 0)  AS min_price,
            COALESCE(ps.avg_price, 0)  AS avg_price
        FROM predictions_cache pc
        JOIN games g ON g.id = pc.game_id
        LEFT JOIN (SELECT * FROM latest WHERE rn = 1) lp ON lp.game_id = g.id
        LEFT JOIN (
            SELECT game_id, MIN(price_usd) AS min_price, AVG(price_usd) AS avg_price
            FROM price_history
            WHERE (shop_id = 61 OR LOWER(shop_name) LIKE '%steam%')
            GROUP BY game_id
        ) ps ON ps.game_id = g.id
        WHERE pc.signal = 'BUY'
          AND g.appid IS NOT NULL
          AND g.title IS NOT NULL
          AND g.title != g.id
          AND g.appid NOT IN (SELECT appid FROM owned WHERE appid IS NOT NULL)
        ORDER BY pc.score DESC
        LIMIT 100
    """, [steam_id, steam_id]).fetchdf()

    if rows.empty:
        return []

    candidates = rows.to_dict(orient="records")

    # ── 3. Calcular affinity score para cada candidato ────────────────────────
    scored = []
    for c in candidates:
        ml_score     = float(c.get("ml_score") or 0)
        title        = c.get("title") or ""
        current_price = float(c.get("current_price") or 0)

        # Afinidad de género
        genres = _detect_genres(title)
        affinity = 0.0
        matched_genres = []
        if genres and genre_weights:
            for genre in genres:
                w = genre_weights.get(genre, 0)
                if w > 0:
                    affinity += w
                    matched_genres.append(genre)
            affinity = min(affinity, 2.0)  # cap a 2.0

        # Compatibilidad de precio (penalizar juegos muy caros para el usuario)
        price_score = 1.0
        if has_profile and current_price > 0 and price_threshold > 0:
            if current_price > price_threshold:
                price_score = max(0.3, price_threshold / current_price)

        # Score final: 60% ML + 30% afinidad + 10% precio
        if has_profile:
            final_score = (ml_score * 0.60) + (affinity * 15 * 0.30) + (price_score * 100 * 0.10)
        else:
            # Sin perfil, usar solo ML score
            final_score = ml_score

        # Reason personalizada
        reason = c.get("reason") or ""
        if matched_genres:
            genre_str = " & ".join(matched_genres[:2])
            reason = f"Matches your {genre_str} taste · " + reason
        elif not has_profile:
            reason = reason  # reason original del ML

        scored.append({
            **_san(c),
            "final_score":    round(final_score, 1),
            "affinity_score": round(affinity, 3),
            "matched_genres": matched_genres,
            "reason":         reason,
            "personalized":   has_profile,
        })

    # ── 4. Ordenar por score final y retornar top N ───────────────────────────
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:limit]


def get_library_stats(con, steam_id: str) -> dict:
    row = con.execute("""
        SELECT
            COUNT(*)                      AS total_games,
            SUM(ug.playtime_mins) / 60.0  AS total_hours,
            COUNT(g.id)                   AS tracked_games
        FROM user_games ug
        LEFT JOIN games g ON g.appid = ug.appid
        WHERE ug.steam_id = ?
    """, [steam_id]).fetchone()
    return {
        "total_games":   int(row[0] or 0),
        "total_hours":   round(float(row[1] or 0), 1),
        "tracked_games": int(row[2] or 0),
    }