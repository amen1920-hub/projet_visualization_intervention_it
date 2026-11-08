"""Extraction : fichiers HOTLINE (.xlsx) -> DataFrame brut (couche Bronze).

Aucun nettoyage ici : on garde les valeurs telles quelles.
"""
import datetime
import logging
from pathlib import Path

import pandas as pd
import yaml

from src.config import DOSSIER_HOTLINE, RACINE

logger = logging.getLogger(__name__)


def charger_techniciens() -> dict:
    """Noms lus dans config/techniciens.yml (non versionné), sinon dans l'exemple."""
    chemin = RACINE / "config" / "techniciens.yml"
    if not chemin.exists():
        chemin = RACINE / "config" / "techniciens.example.yml"
    with open(chemin, encoding="utf-8") as f:
        noms = yaml.safe_load(f)["techniciens"]
    return {n.lower(): n for n in noms}


TECHNICIENS = charger_techniciens()


def identifier_technicien(nom_fichier: str) -> str:
    bas = nom_fichier.lower()
    for cle, valeur in TECHNICIENS.items():
        if cle in bas:
            return valeur
    return "Inconnu"


def lister_fichiers(dossier: Path) -> list[Path]:
    """Tous les .xlsx, sans les fichiers temporaires Excel (~$...)."""
    return sorted(p for p in dossier.rglob("*.xlsx") if not p.name.startswith("~$"))


def lire_fichier(chemin: Path) -> pd.DataFrame:
    """Lit un fichier HOTLINE et renvoie ses tickets bruts."""
    df = pd.read_excel(chemin, sheet_name=0, header=None)
    if df.shape[1] < 7:
        raise ValueError("moins de 7 colonnes")

    est_ticket = df[1].apply(lambda x: isinstance(x, (pd.Timestamp, datetime.datetime)))
    tickets = df[est_ticket]
    if tickets.empty:
        raise ValueError("aucun ticket détecté")

    return pd.DataFrame({
        "technicien": identifier_technicien(chemin.name),
        "date": tickets[1],
        "employe_aide": tickets[2],
        "description": tickets[3],
        "temps_reaction_min": tickets[4],
        "temps_execution_min": tickets[5],
        "temps_resolution_min": tickets[6],
        "fichier_source": chemin.name,
        "ligne_source": tickets.index + 1,  # numéro de ligne dans Excel
    }).reset_index(drop=True)


def extraire(dossier: Path = DOSSIER_HOTLINE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renvoie (bronze, fichiers_ignores)."""
    fichiers = lister_fichiers(dossier)
    logger.info("%d fichiers trouvés", len(fichiers))

    morceaux, ignores = [], []
    for f in fichiers:
        try:
            morceaux.append(lire_fichier(f))
        except Exception as e:
            logger.warning("ignoré : %s -> %s", f.name, e)
            ignores.append({"fichier": f.name, "raison": str(e)})

    bronze = pd.concat(morceaux, ignore_index=True) if morceaux else pd.DataFrame()
    return bronze, pd.DataFrame(ignores)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    bronze, ignores = extraire()
    print(f"{len(bronze)} lignes brutes, {len(ignores)} fichiers ignorés")
    print(bronze.head())
    print(ignores)