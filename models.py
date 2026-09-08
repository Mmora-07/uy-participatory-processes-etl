"""Modelo de datos de un proceso participativo.

Se usa pydantic en vez de dataclass porque valida tipos en el borde
(parser -> modelo) sin código manual y da serialización a dict/JSON
(model_dump) sin lógica ad hoc en main.py.

Nota sobre "7 campos obligatorios": slug, nombre_largo, nombre_corto,
fecha (inicio + fin, un solo concepto con dos valores), entidad,
descripcion_url y formulario_url. `componentes` es el campo opcional.
"""

from pydantic import BaseModel


class Componente(BaseModel):
    texto: str
    url: str


class Proceso(BaseModel):
    slug: str
    nombre_largo: str
    nombre_corto: str
    fecha_inicio: str | None
    fecha_fin: str | None
    entidad: str | None
    descripcion_url: str
    formulario_url: str | None
    componentes: list[Componente] | None = None

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
