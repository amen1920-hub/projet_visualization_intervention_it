import pandas as pd

from src.etl.transform import nettoyer, periode_depuis_nom


def test_periode_nom_standard():
    assert periode_depuis_nom("HOTLINE Janiver 2025 Jean Dupont.xlsx") == (2025, 1)


def test_periode_accents():
    assert periode_depuis_nom("HOTLINE Août 2024 X.xlsx") == (2024, 8)
    assert periode_depuis_nom("HOTLINE Février 2025 X.xlsx") == (2025, 2)


def test_periode_sans_annee():
    assert periode_depuis_nom("HOTLINE Novembre  Jean Dupont.xlsx") == (None, 11)


def test_garde_la_copie_du_bon_mois():
    base = dict(technicien="T", date=pd.Timestamp("2025-01-10"), employe_aide="x",
                description="d", temps_reaction_min=1, temps_execution_min=1,
                temps_resolution_min=2, ligne_source=5)
    bronze = pd.DataFrame([
        {**base, "fichier_source": "HOTLINE Février 2025 T.xlsx"},
        {**base, "fichier_source": "HOTLINE Janvier 2025 T.xlsx"},
    ])
    silver, rejets = nettoyer(bronze)
    assert silver["fichier_source"].tolist() == ["HOTLINE Janvier 2025 T.xlsx"]
    assert rejets["raison"].tolist() == ["doublon_inter_fichier"]