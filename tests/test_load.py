import pandas as pd

from src.etl.load import ajouter_id


def test_id_ticket_stable_et_distinct():
    df = pd.DataFrame({
        "technicien": ["T-1", "T-1", "T-2"],
        "date": ["2025-01-10"] * 3,
        "employe_aide": ["E-1", "E-1", "E-1"],
        "description": ["d", "d", "d"],
    })
    ids = ajouter_id(df)["id_ticket"].tolist()
    assert ids[0] == ids[1]
    assert ids[0] != ids[2]