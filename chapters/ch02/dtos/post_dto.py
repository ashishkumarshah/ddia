from pydantic import BaseModel


class PostDTO(BaseModel):
    id: int
    sender_id: int
    text: str
    timestamp: int
