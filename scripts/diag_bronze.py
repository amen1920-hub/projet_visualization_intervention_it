import pandas as pd

from src.etl.extract import extraire

b, _ = extraire()
b["date_dt"] = pd.to_datetime(b["date"], errors="coerce")

# 1. Dates invalides (mêmes règles que l'ancien script)
invalide = b["date_dt"].isna() | (b["date_dt"] < "2022-01-01") | (b["date_dt"] > pd.Timestamp.today())
print("Dates invalides :", invalide.sum())
print(b.loc[invalide, "fichier_source"].value_counts().head(5))

# 2. Doublons sur la clé métier (hors fichier et ligne)
cle = ["technicien", "date_dt", "employe_aide", "description"]
valide = b[~invalide]
print("\nDoublons (clé métier) :", valide.duplicated(cle).sum())

groupes = valide[valide.duplicated(cle, keep=False)]
n_fichiers = groupes.groupby(cle, dropna=False)["fichier_source"].nunique()
print("Groupes de doublons :", len(n_fichiers))
print("  dont répartis sur plusieurs fichiers :", (n_fichiers > 1).sum())
print("\nFichiers contenant le plus de doublons :")
print(groupes["fichier_source"].value_counts().head(10))