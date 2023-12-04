from pydantic import BaseModel


class Book(BaseModel):
    ident: str
    title: str
    author: str
    url: str
    links: dict[str, str]
    media_type: str
