from pydantic import BaseModel

class Character(BaseModel):
    name: str
    class_name: str
    level: int
    stats: dict
    skills: dict
    hit_points: int
    armor_class: int
    proficiency_bonus: int
    inventory: list