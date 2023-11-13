from pydantic import BaseModel


class Book(BaseModel):
    title: str
    author: str
    url: str
    links: dict[str, str]
    media_type: str
