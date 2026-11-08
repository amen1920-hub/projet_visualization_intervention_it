from src.etl.categorize import categoriser, charger_regles

R, V, I = charger_regles()


def cat(texte):
    return categoriser(texte, R, V, I)


def test_accents_et_fautes():
    assert cat("Installation imptrimant") == "Imprimante / Scanner"
    assert cat("installation systéme d'exploitation") == "Système d'exploitation"


def test_mot_court_dans_un_mot_ne_matche_pas():
    assert cat("changed settings") != "Application métier / ERP"   # "ged" dans un mot
    assert cat("adresse reseau") == "Réseau"                        # pas "ad" = comptes


def test_mot_entier_matche():
    assert cat("probleme GED") == "Application métier / ERP"
    assert cat("reset AD") == "Gestion des comptes"


def test_vide_et_inconnu():
    assert cat(None) == "Non renseigné"
    assert cat("blabla") == "Autre / à vérifier"