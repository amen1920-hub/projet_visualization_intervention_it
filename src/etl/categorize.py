"""Catégorisation des tickets par règles lues dans config/categories.yml."""
import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd
import yaml

from src.config import RACINE
from src.etl.extract import extraire
from src.etl.transform import nettoyer

logger = logging.getLogger(__name__)
CHEMIN_REGLES = RACINE / "config" / "categories.yml"


def normaliser(texte) -> str:
    """Minuscules, sans accents, espaces simplifiés."""
    t = unicodedata.normalize("NFKD", str(texte).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip()


def charger_regles(chemin: Path = CHEMIN_REGLES):
    with open(chemin, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    regles = []
    for cat in cfg["categories"]:
        motifs = []
        for kw in cat["mots_cles"]:
            mot_entier = kw.endswith("$")
            kw = normaliser(kw.rstrip("$"))
            motifs.append(r"\b" + re.escape(kw) + (r"\b" if mot_entier else ""))
        regles.append((cat["nom"], re.compile("|".join(motifs))))
    return regles, cfg["defaut_vide"], cfg["defaut_inconnu"]


def categoriser(description, regles, defaut_vide, defaut_inconnu) -> str:
    if pd.isna(description) or not str(description).strip():
        return defaut_vide
    texte = normaliser(description)
    for nom, motif in regles:
        if motif.search(texte):
            return nom
    return defaut_inconnu


def ajouter_categorie(silver: pd.DataFrame, chemin: Path = CHEMIN_REGLES) -> pd.DataFrame:
    regles, vide, inconnu = charger_regles(chemin)
    out = silver.copy()
    out["categorie"] = out["description"].apply(lambda d: categoriser(d, regles, vide, inconnu))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    bronze, _ = extraire()
    silver, _ = nettoyer(bronze)
    silver = ajouter_categorie(silver)

    sortie = RACINE / "data" / "processed"
    sortie.mkdir(parents=True, exist_ok=True)
    silver.to_csv(sortie / "silver_hotline.csv", index=False, encoding="utf-8")

    # Revue : chaque description distincte avec sa catégorie (à relire à la main)
    revue = (silver.assign(description_norm=silver["description"].map(
                 lambda d: "" if pd.isna(d) else normaliser(d)))
             .groupby(["description_norm", "categorie"]).size()
             .reset_index(name="nb_tickets")
             .sort_values(["categorie", "nb_tickets"], ascending=[True, False]))
    revue["categorie_correcte"] = ""   # à remplir seulement si la catégorie est fausse
    revue.to_csv(sortie / "revue_categories.csv", index=False, encoding="utf-8-sig")

    print(silver["categorie"].value_counts())
    print(f"\nDescriptions distinctes à relire : {len(revue)}")