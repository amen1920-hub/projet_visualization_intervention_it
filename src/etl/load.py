"""Chargement : silver -> PostgreSQL, incrémental (pas de doublon si on relance)."""
import hashlib
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

from src.config import RACINE
from src.etl.pipeline import lancer

load_dotenv()
logger = logging.getLogger(__name__)

COLONNES = ["id_ticket", "technicien", "date", "employe_aide", "description", "categorie",
            "temps_reaction_min", "temps_execution_min", "temps_resolution_min",
            "fichier_source", "ligne_source"]
CLE = ["technicien", "date", "employe_aide", "description"]


def ajouter_id(df: pd.DataFrame) -> pd.DataFrame:
    """id_ticket = hash des champs métier : stable d'une exécution à l'autre."""
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["id_ticket"] = out[CLE].apply(
        lambda r: hashlib.sha256(
            "|".join("" if pd.isna(v) else str(v) for v in r).encode()).hexdigest()[:16],
        axis=1)
    return out


def creer_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"),
        host="localhost", port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"))
    return create_engine(url)


def charger():
    silver, rejets = lancer()
    silver = ajouter_id(silver)

    with creer_engine().begin() as con:
        for fichier in sorted((RACINE / "sql").glob("01_*.sql")):
            con.execute(text(fichier.read_text(encoding="utf-8")))

        silver[COLONNES].to_sql("_stg_ticket", con, schema="silver",
                                if_exists="replace", index=False)
        cols = ", ".join(COLONNES)
        selection = ", ".join("CAST(date AS DATE)" if c == "date" else c for c in COLONNES)
        res = con.execute(text(
            f"INSERT INTO silver.ticket ({cols}) SELECT {selection} FROM silver._stg_ticket "
            "ON CONFLICT (id_ticket) DO NOTHING"))
        inserees = res.rowcount
        con.execute(text("DROP TABLE silver._stg_ticket"))

        rejets.to_sql("rejet", con, schema="silver", if_exists="replace", index=False)

        con.execute(text(
            "INSERT INTO ops.log_chargement (lignes_lues, lignes_inserees, lignes_rejetees) "
            "VALUES (:l, :i, :r)"),
            {"l": len(silver), "i": inserees, "r": len(rejets)})
        total = con.execute(text("SELECT COUNT(*) FROM silver.ticket")).scalar()

    print(f"lues={len(silver)} inserees={inserees} rejetees={len(rejets)} total_en_base={total}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    charger()