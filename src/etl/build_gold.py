"""Construit la couche Gold (schéma en étoile) à partir de silver."""
import logging

from sqlalchemy import text

from src.config import RACINE
from src.etl.load import creer_engine

TABLES = ["dim_date", "dim_technicien", "dim_categorie",
          "dim_employe", "dim_description", "fait_ticket"]


def construire():
    sql = (RACINE / "sql" / "02_gold.sql").read_text(encoding="utf-8")
    with creer_engine().begin() as con:
        con.execute(text(sql))
        for t in TABLES:
            n = con.execute(text(f"SELECT COUNT(*) FROM gold.{t}")).scalar()
            print(f"gold.{t}: {n}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    construire()