DROP SCHEMA IF EXISTS gold CASCADE;
CREATE SCHEMA gold;

CREATE TABLE gold.dim_date (
    id_date      INTEGER PRIMARY KEY,
    date         DATE NOT NULL UNIQUE,
    annee        SMALLINT NOT NULL,
    trimestre    SMALLINT NOT NULL,
    mois         SMALLINT NOT NULL,
    nom_mois     TEXT NOT NULL,
    annee_mois   TEXT NOT NULL,
    semaine_iso  SMALLINT NOT NULL,
    jour_semaine SMALLINT NOT NULL,
    nom_jour     TEXT NOT NULL
);

INSERT INTO gold.dim_date
SELECT
    CAST(to_char(d, 'YYYYMMDD') AS INTEGER),
    CAST(d AS DATE),
    CAST(extract(year FROM d) AS SMALLINT),
    CAST(extract(quarter FROM d) AS SMALLINT),
    CAST(extract(month FROM d) AS SMALLINT),
    (ARRAY['janvier','février','mars','avril','mai','juin','juillet','août',
           'septembre','octobre','novembre','décembre'])[CAST(extract(month FROM d) AS INTEGER)],
    to_char(d, 'YYYY-MM'),
    CAST(extract(week FROM d) AS SMALLINT),
    CAST(extract(isodow FROM d) AS SMALLINT),
    (ARRAY['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'])[CAST(extract(isodow FROM d) AS INTEGER)]
FROM generate_series(
    (SELECT min(date) FROM silver.ticket),
    (SELECT max(date) FROM silver.ticket),
    INTERVAL '1 day') AS g(d);

CREATE TABLE gold.dim_technicien (
    id_technicien INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    technicien    TEXT NOT NULL UNIQUE
);
INSERT INTO gold.dim_technicien (technicien)
SELECT DISTINCT technicien FROM silver.ticket ORDER BY 1;

CREATE TABLE gold.dim_categorie (
    id_categorie INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categorie    TEXT NOT NULL UNIQUE
);
INSERT INTO gold.dim_categorie (categorie)
SELECT DISTINCT categorie FROM silver.ticket ORDER BY 1;

CREATE TABLE gold.dim_employe (
    id_employe   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employe_aide TEXT NOT NULL UNIQUE
);
INSERT INTO gold.dim_employe (employe_aide)
SELECT DISTINCT employe_aide FROM silver.ticket WHERE employe_aide IS NOT NULL ORDER BY 1;

CREATE TABLE gold.dim_description (
    id_description         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    description_normalisee TEXT NOT NULL UNIQUE
);
INSERT INTO gold.dim_description (description_normalisee)
SELECT DISTINCT lower(btrim(description)) FROM silver.ticket
WHERE description IS NOT NULL ORDER BY 1;

CREATE TABLE gold.fait_ticket (
    id_ticket            TEXT PRIMARY KEY,
    id_date              INTEGER NOT NULL REFERENCES gold.dim_date (id_date),
    id_technicien        INTEGER NOT NULL REFERENCES gold.dim_technicien (id_technicien),
    id_categorie         INTEGER NOT NULL REFERENCES gold.dim_categorie (id_categorie),
    id_employe           INTEGER REFERENCES gold.dim_employe (id_employe),
    id_description       INTEGER REFERENCES gold.dim_description (id_description),
    temps_reaction_min   NUMERIC,
    temps_execution_min  NUMERIC,
    temps_resolution_min NUMERIC,
    fichier_source       TEXT NOT NULL
);

INSERT INTO gold.fait_ticket
SELECT
    t.id_ticket,
    CAST(to_char(t.date, 'YYYYMMDD') AS INTEGER),
    tech.id_technicien,
    c.id_categorie,
    e.id_employe,
    d.id_description,
    t.temps_reaction_min,
    t.temps_execution_min,
    t.temps_resolution_min,
    t.fichier_source
FROM silver.ticket t
JOIN gold.dim_technicien tech ON tech.technicien = t.technicien
JOIN gold.dim_categorie c ON c.categorie = t.categorie
LEFT JOIN gold.dim_employe e ON e.employe_aide = t.employe_aide
LEFT JOIN gold.dim_description d ON d.description_normalisee = lower(btrim(t.description));