"""Pipeline : extract -> transform -> categorize -> anonymize -> data/processed."""
import logging

from src.config import RACINE
from src.etl.anonymize import anonymiser, masquer_descriptions_inconnues
from src.etl.categorize import ajouter_categorie
from src.etl.extract import extraire
from src.etl.transform import nettoyer


def lancer():
    bronze, _ = extraire()
    silver, rejets = nettoyer(bronze)
    silver, rejets = ajouter_categorie(silver), ajouter_categorie(rejets)
    silver = masquer_descriptions_inconnues(anonymiser(silver))
    rejets = masquer_descriptions_inconnues(anonymiser(rejets))

    sortie = RACINE / "data" / "processed"
    sortie.mkdir(parents=True, exist_ok=True)
    silver.to_csv(sortie / "silver_hotline.csv", index=False, encoding="utf-8")
    rejets.to_csv(sortie / "rejets.csv", index=False, encoding="utf-8")
    return silver, rejets


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    s, r = lancer()
    print(f"silver={len(s)} rejets={len(r)}")