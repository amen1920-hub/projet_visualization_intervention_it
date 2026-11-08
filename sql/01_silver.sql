CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS silver.ticket (
    id_ticket            TEXT PRIMARY KEY,
    technicien           TEXT NOT NULL,
    date                 DATE NOT NULL,
    employe_aide         TEXT,
    description          TEXT,
    categorie            TEXT NOT NULL,
    temps_reaction_min   NUMERIC,
    temps_execution_min  NUMERIC,
    temps_resolution_min NUMERIC,
    fichier_source       TEXT NOT NULL,
    ligne_source         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ops.log_chargement (
    id               SERIAL PRIMARY KEY,
    date_chargement  TIMESTAMPTZ NOT NULL DEFAULT now(),
    lignes_lues      INTEGER NOT NULL,
    lignes_inserees  INTEGER NOT NULL,
    lignes_rejetees  INTEGER NOT NULL
);