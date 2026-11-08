"""Transformation : bronze -> silver (nettoyé, typé, dédoublonné) + rejets."""
import logging
import re
import unicodedata

import numpy as np
import pandas as pd

from src.config import RACINE
from src.etl.extract import extraire

logger = logging.getLogger(__name__)

DATE_MIN = pd.Timestamp("2022-01-01")
CLE_METIER = ["technicien", "date", "employe_aide", "description"]
COLONNES_TEMPS = ["temps_reaction_min", "temps_execution_min", "temps_resolution_min"]

MOIS = {"jan": 1, "fev": 2, "mar": 3, "avr": 4, "mai": 5, "juin": 6,
        "juil": 7, "aou": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
MOTIF_MOIS = re.compile("|".join(MOIS))


def periode_depuis_nom(nom_fichier: str):
    """'HOTLINE Janiver 2025 X.xlsx' -> (2025, 1). Année None si absente ; None si mois inconnu."""
    txt = unicodedata.normalize("NFKD", nom_fichier.lower()).encode("ascii", "ignore").decode()
    mois = MOTIF_MOIS.search(txt)
    if not mois:
        return None
    annee = re.search(r"20\d\d", txt)
    return (int(annee.group()) if annee else None), MOIS[mois.group()]


def _conforme(date: pd.Timestamp, periode) -> bool:
    """La date correspond-elle au mois indiqué dans le nom du fichier ?"""
    if periode is None:
        return True  # impossible de juger
    annee, mois = periode
    return date.month == mois and (annee is None or date.year == annee)


def nettoyer(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renvoie (silver, rejets)."""
    df = bronze.copy()

    # Typage
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in COLONNES_TEMPS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["employe_aide"] = df["employe_aide"].astype("string").str.strip().str.lower().replace("", pd.NA)
    df["description"] = df["description"].astype("string").str.strip().replace("", pd.NA)

    # Dates hors plage
    hors_plage = df["date"].isna() | (df["date"] < DATE_MIN) | (df["date"] > pd.Timestamp.today())
    rejets_date = df[hors_plage].assign(raison="date_invalide")
    df = df[~hors_plage].copy()

    # Doublons : on garde en priorité la ligne du fichier dont le nom correspond au mois
    periodes = {f: periode_depuis_nom(f) for f in df["fichier_source"].unique()}
    df["fichier_conforme"] = [_conforme(d, periodes[f])
                              for d, f in zip(df["date"], df["fichier_source"])]
    df = df.sort_values(["fichier_conforme", "fichier_source", "ligne_source"],
                        ascending=[False, True, True], kind="stable")
    est_doublon = df.duplicated(CLE_METIER, keep="first")

    conserves = (df[~est_doublon][CLE_METIER + ["fichier_source"]]
                 .rename(columns={"fichier_source": "fichier_conserve"}))
    rejets_dup = df[est_doublon].merge(conserves, on=CLE_METIER, how="left")
    rejets_dup["raison"] = np.where(
        rejets_dup["fichier_source"] == rejets_dup["fichier_conserve"],
        "doublon_meme_fichier", "doublon_inter_fichier")

    silver = (df[~est_doublon].drop(columns="fichier_conforme")
              .sort_values(["date", "technicien", "ligne_source"]).reset_index(drop=True))
    colonnes = ["raison", "technicien", "date", "employe_aide", "description",
                "fichier_source", "ligne_source"]
    rejets = pd.concat([rejets_date[colonnes], rejets_dup[colonnes]], ignore_index=True)

    logger.info("bronze=%d silver=%d rejets=%d", len(bronze), len(silver), len(rejets))
    return silver, rejets


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    bronze, _ = extraire()
    silver, rejets = nettoyer(bronze)

    sortie = RACINE / "data" / "processed"
    sortie.mkdir(parents=True, exist_ok=True)
    silver.to_csv(sortie / "silver_hotline.csv", index=False, encoding="utf-8")
    rejets.to_csv(sortie / "rejets.csv", index=False, encoding="utf-8")

    print(rejets["raison"].value_counts())
    print(rejets[rejets["raison"] == "date_invalide"][["fichier_source", "ligne_source", "date"]])