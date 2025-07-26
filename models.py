import datetime
import pydantic


class Node(pydantic.BaseModel):
    """
    Base class for all nodes, containing common mandatory fields.
    """

    name: str = pydantic.Field(description="Name of the node")
    tags: list[str] = pydantic.Field(
        default_factory=list,
        description="Tags of the node",
    )
    date: datetime.datetime | None = pydantic.Field(description="Date of the node")


class ObsidianNode(Node):
    absolute_path: str = pydantic.Field(
        description="Absolute path of the obsidian file"
    )
    markdown_content: str = pydantic.Field(description="Content of the obsidian file.")
    yaml_content: dict = pydantic.Field(
        description="YAML content of the obsidian file."
    )
    # TODO: add links

    def __str__(self) -> str:
        content_preview = (
            self.markdown_content[:20] + "..."
            if len(self.markdown_content) > 20
            else self.markdown_content
        )
        return f"ObsidianNode(name='{self.name}', tags={self.tags}, date={self.date}, absolute_path='{self.absolute_path}', markdown_content='{content_preview}')"
