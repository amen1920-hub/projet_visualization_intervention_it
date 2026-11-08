import pandas as pd

from src.etl.extract import extraire

b, _ = extraire()
b["date_dt"] = pd.to_datetime(b["date"], errors="coerce")
b["mois_donnees"] = b["date_dt"].dt.to_period("M")

cle = ["technicien", "date_dt", "employe_aide", "description"]
b["est_doublon"] = b.duplicated(cle, keep=False)

# 1. Pour les fichiers suspects : quels mois contiennent-ils vraiment ?
suspects = ["Février 2025", "Janvier 2025", "Janiver 2025", "Juin 2025", "Juillet 2025"]
masque = b["fichier_source"].str.contains("|".join(suspects), case=False, na=False)
print(b[masque].groupby("fichier_source")["mois_donnees"]
        .agg(lambda s: sorted(set(map(str, s.dropna())))).to_string())

# 2. Le seul groupe de doublons dans un même fichier
g = b[b["est_doublon"]].groupby(cle, dropna=False)["fichier_source"].nunique()
intra = g[g == 1].index
print("\nDoublon dans un même fichier :")
print(b.set_index(cle).loc[intra].reset_index()[cle + ["fichier_source", "ligne_source"]].to_string())

# 3. La date invalide
print("\nDate invalide :")
print(b[b["date_dt"].isna()][["fichier_source", "ligne_source", "date"]].to_string())