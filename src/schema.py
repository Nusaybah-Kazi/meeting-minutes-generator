from pydantic import BaseModel, Field, field_validator


class _Base(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def none_to_default(cls, v, info):
        """Models sometimes return null for empty lists; use the field default instead."""
        if v is None:
            field = cls.model_fields[info.field_name]
            if not field.is_required():
                return field.get_default(call_default_factory=True)
        return v


class ActionItem(_Base):
    task: str
    owner: str | None = None
    due: str | None = None


class ChunkNotes(_Base):
    title: str | None = None
    date: str | None = None
    attendees: list[str] = Field(default_factory=list)
    agenda: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_meeting: str | None = None


class Minutes(_Base):
    title: str = "Meeting Minutes"
    date: str | None = None
    attendees: list[str] = Field(default_factory=list)
    agenda: list[str] = Field(default_factory=list)
    summary: str = ""
    discussion_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_meeting: str | None = None