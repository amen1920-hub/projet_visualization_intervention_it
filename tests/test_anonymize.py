import pandas as pd

from src.etl.anonymize import anonymiser, masquer_descriptions_inconnues

TECH = {"jean dupont": "Jean Dupont"}
DF = pd.DataFrame({
    "technicien": ["Jean Dupont"],
    "employe_aide": ["alice.martin"],
    "fichier_source": ["HOTLINE Mai 2025 Jean Dupont.xlsx"],
})


def test_stable_et_sans_nom():
    a, b = anonymiser(DF, b"sel", TECH), anonymiser(DF, b"sel", TECH)
    assert a.equals(b)
    texte = a.to_string().lower()
    assert "dupont" not in texte and "martin" not in texte
    assert a.loc[0, "technicien"] in a.loc[0, "fichier_source"]


def test_le_sel_change_le_pseudonyme():
    a = anonymiser(DF, b"a", TECH).loc[0, "technicien"]
    b = anonymiser(DF, b"b", TECH).loc[0, "technicien"]
    assert a != b


def test_description_inconnue_masquee():
    df = pd.DataFrame({
        "description": ["jean dupont", "installation imprimante"],
        "categorie": ["Autre / à vérifier", "Imprimante / Scanner"],
    })
    out = masquer_descriptions_inconnues(df, b"sel")
    assert "dupont" not in out.loc[0, "description"].lower()
    assert out.loc[1, "description"] == "installation imprimante"