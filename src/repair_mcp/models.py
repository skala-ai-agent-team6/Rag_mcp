from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DamageLabel(StrictModel):
    damage_type: Literal["damage", "dent"]
    part: str = Field(min_length=1, max_length=100)


class SearchRequest(StrictModel):
    raw_text: str = Field(default="", max_length=2000)
    origin: Literal["technician", "ai_image"] = "technician"
    technician_confirmed: bool = False
    pcb_labels: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=30)
    damage_labels: list[DamageLabel] = Field(default_factory=list, max_length=30)
    model_code: str | None = Field(default=None, max_length=120)
    top_k: int = Field(default=5, ge=1, le=20)
    # Relevance cutoff is experimental, NOT diagnosis confidence.
    min_score: float = Field(default=0.75, ge=-1, le=1)
    repair_status: Literal["Fixed", "Repairable", "End of life", "Unknown"] | None = None
    use_bilingual_hints: bool = True
