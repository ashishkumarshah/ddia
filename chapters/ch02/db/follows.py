from sqlmodel import SQLModel, Field


class Follows(SQLModel, table=True):
    follower_id: int | None = Field(default=None, foreign_key="users.id",
                                    primary_key=True, )
    followee_id: int | None = Field(default=None, foreign_key="users.id",
                                    primary_key=True, )


def get_followee_ids_for_user(user_id: int, limit: int = 100) -> list[int]:
    # Boilerplate only; implementation intentionally deferred.
    return []
