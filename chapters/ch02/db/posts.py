from sqlmodel import Field, SQLModel


class Posts(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sender_id: int | None = Field(default=None, foreign_key="users.id")
    text: str
    timestamp: int
