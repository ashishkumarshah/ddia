from pydantic import BaseModel


class UserDTO(BaseModel):
    id: int
    screen_name: str
    profile_image: str
