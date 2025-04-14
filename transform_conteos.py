import pyarrow
import polars as pl

PROCESOS = [
    "No definido",
    "Comprensión",
    "Utilización del conocimiento",
    "Propuesta de solución",
    "Juicio crítico",
]

CAMPOS = [
        "Lenguajes",
        "Saberes y pensamiento científico",
        "De lo humano y lo comunitario",
        "Ética, naturaleza y sociedades",
]

# Diccionario de variables
diccionario = pl.read_parquet("data/diccionario.parquet").drop(
    ["fase", "nivel", "grado"]
)
# Data de rubricas
rubrica = pl.read_parquet("data/diccionario_rubrica.parquet")
# Data de medias
medias = pl.read_parquet("data/item_medias.parquet").with_columns(
    pl.col("grado").cast(pl.Int32)
)
# data irt
irt = pl.read_parquet("data/item_irt_eia.parquet").with_columns(
    pl.col("grado").cast(pl.Int32)
)
# Data de conteos
conteo = (
    pl.read_parquet("data/item_conteo_grado.parquet")
    .join(diccionario, how="inner", on="item")
    .join(rubrica, how="inner", on=["item", "resp"])
    .with_columns(
        pl.col("proceso").cast(pl.Enum(PROCESOS)),
        pl.col("campo").cast(pl.Enum(CAMPOS)),
        )
)
# Auxiliares para ordenar por nivel de respuesta
nivel_0 = (
    conteo.filter(pl.col("resp") == "N0")
    .select(["item", "grado", "prop"])
    .rename({"prop": "nivel_0"})
)
nivel_3 = (
    conteo.filter(pl.col("resp") == "N3")
    .select(["item", "grado", "prop"])
    .rename({"prop": "nivel_3"})
)
# Union con conteos
conteo = (
    conteo.join(nivel_0, how="left", on=["item", "grado"])
    .join(nivel_3, how="left", on=["item", "grado"])
    .join(medias, how="left", on=["item", "grado"])
    .join(irt, how="left", on=["item", "grado", "resp"])
    .with_columns(pl.col("resp").cast(pl.Enum(["N0", "N1", "N2", "N3"])))
)

conteo.write_parquet("data/st_conteo.parquet")