from pydantic import BaseModel, Field


class NovoCofre(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    senha_mestra: str = Field(..., min_length=8, max_length=256)


class NovoSegredo(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    usuario: str | None = Field(None, max_length=200)
    url: str | None = Field(None, max_length=2048)
    senha: str = Field(..., min_length=1, max_length=4096)