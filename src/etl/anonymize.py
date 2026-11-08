"""Pseudonymisation : techniciens, employés, noms de fichiers."""
import hashlib
import hmac
import os
import re

import pandas as pd
from dotenv import load_dotenv

from src.etl.extract import TECHNICIENS

load_dotenv()


def _sel() -> bytes:
    sel = os.getenv("ANON_SALT")
    if not sel:
        raise RuntimeError("ANON_SALT manquant : ajoute-le dans .env")
    return sel.encode()


def pseudonyme(valeur, prefixe: str, sel: bytes):
    if pd.isna(valeur):
        return pd.NA
    cle = " ".join(str(valeur).lower().split())
    return f"{prefixe}-{hmac.new(sel, cle.encode(), hashlib.sha256).hexdigest()[:6]}"


def anonymiser_fichier(nom: str, sel: bytes, techniciens: dict | None = None) -> str:
    """Remplace le nom du technicien dans le nom de fichier."""
    for cle in (techniciens or TECHNICIENS):
        motif = r"\s+".join(map(re.escape, cle.split()))
        nom = re.sub(motif, pseudonyme(cle, "T", sel), nom, flags=re.IGNORECASE)
    return nom


def anonymiser(df: pd.DataFrame, sel: bytes | None = None,
               techniciens: dict | None = None) -> pd.DataFrame:
    sel = sel or _sel()
    out = df.copy()
    out["technicien"] = out["technicien"].map(lambda v: pseudonyme(v, "T", sel))
    out["employe_aide"] = out["employe_aide"].map(lambda v: pseudonyme(v, "E", sel))
    out["fichier_source"] = out["fichier_source"].map(
        lambda n: anonymiser_fichier(n, sel, techniciens))
    return out


def masquer_descriptions_inconnues(df: pd.DataFrame, sel: bytes | None = None) -> pd.DataFrame:
    """Descriptions non reconnues par les règles : pseudonymisées (peuvent contenir un nom)."""
    sel = sel or _sel()
    out = df.copy()
    masque = out["categorie"] == "Autre / à vérifier"
    out.loc[masque, "description"] = out.loc[masque, "description"].map(
        lambda v: pseudonyme(v, "D", sel))
    return out