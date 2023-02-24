from abc import ABC
from dataclasses import dataclass
import hashlib
from typing import Any, Callable, Dict, List, Optional, Union
import pathlib


class NoID(ABC):
    """Class to indicate that an element do not have an ID."""

    pass


@dataclass
class ElementMetadata:
    filename: Optional[str] = None
    page_number: Optional[int] = None
    url: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.filename, pathlib.Path):
            self.filename = str(self.filename)

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if value is not None}

    @classmethod
    def from_dict(cls, input_dict):
        return cls(**input_dict)


class Element(ABC):
    """An element is a section of a page in the document."""

    def __init__(
        self,
        element_id: Union[str, NoID] = NoID(),
        coordinates: Optional[List[float]] = None,
        metadata: ElementMetadata = ElementMetadata(),
    ):
        self.id: Union[str, NoID] = element_id
        self.coordinates: Optional[List[float]] = coordinates
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "type": None,
            "coordinates": self.coordinates,
            "element_id": self.id,
            "metadata": self.metadata.to_dict(),
        }
    
    def to_markdown():
        raise NotImplementedError


class CheckBox(Element):
    """A checkbox with an attribute indicating whether its checked or not. Primarily used
    in documents that are forms"""

    def __init__(
        self,
        element_id: Union[str, NoID] = NoID(),
        coordinates: Optional[List[float]] = None,
        checked: bool = False,
        metadata: ElementMetadata = ElementMetadata(),
    ):
        self.id: Union[str, NoID] = element_id
        self.coordinates: Optional[List[float]] = coordinates
        self.checked: bool = checked
        self.metadata = metadata

    def __eq__(self, other):
        return (self.checked == other.checked) and (self.coordinates) == (other.coordinates)

    def to_dict(self) -> dict:
        return {
            "type": "CheckBox",
            "checked": self.checked,
            "coordinates": self.coordinates,
            "element_id": self.id,
            "metadata": self.metadata.to_dict(),
        }


class Text(Element):
    """Base element for capturing free text from within document."""

    category = "UncategorizedText"

    def __init__(
        self,
        text: str,
        element_id: Union[str, NoID] = NoID(),
        coordinates: Optional[List[float]] = None,
        metadata: ElementMetadata = ElementMetadata(),
    ):
        self.text: str = text

        if isinstance(element_id, NoID):
            # NOTE(robinson) - Cut the SHA256 hex in half to get the first 128 bits
            element_id = hashlib.sha256(text.encode()).hexdigest()[:32]

        super().__init__(element_id=element_id, metadata=metadata, coordinates=coordinates)

    def __str__(self):
        return self.text

    def __eq__(self, other):
        return all(
            [
                (self.text == other.text),
                (self.coordinates == other.coordinates),
                (self.category == other.category),
            ]
        )

    def to_dict(self) -> dict:
        return {
            "element_id": self.id,
            "coordinates": self.coordinates,
            "text": self.text,
            "type": self.category,
            "metadata": self.metadata.to_dict(),
        }

    def apply(self, *cleaners: Callable):
        """Applies a cleaning brick to the text element. The function that's passed in
        should take a string as input and produce a string as output."""
        cleaned_text = self.text
        for cleaner in cleaners:
            cleaned_text = cleaner(cleaned_text)

        if not isinstance(cleaned_text, str):
            raise ValueError("Cleaner produced a non-string output.")

        self.text = cleaned_text

    def to_markdown(self):
        return f"![]({self.text})"


class FigureCaption(Text):
    """An element for capturing text associated with figure captions."""

    category = "FigureCaption"

    def to_markdown(self):
        return f"![]({self.text})"

    pass


class NarrativeText(Text):
    """NarrativeText is an element consisting of multiple, well-formulated sentences. This
    excludes elements such titles, headers, footers, and captions."""

    category = "NarrativeText"

    def to_markdown(self):
        return f"{self.text}"


class ListItem(Text):
    """ListItem is a NarrativeText element that is part of a list."""

    category = "ListItem"

    def to_markdown(self):
        return f"- {self.text}"


class Title(Text):
    """A text element for capturing titles."""

    category = "Title"

    def to_markdown(self):
        return f"# {self.text}"


class Address(Text):
    """A text element for capturing addresses."""

    category = "Address"

    def to_markdown(self):
        return f"{self.text}"


class Image(Text):
    """A text element for capturing image metadata."""

    category = "Image"

    def to_markdown(self):
        return ""


class PageBreak(Text):
    """An element for capturing page breaks."""

    category = "PageBreak"

    def __init__(
        self,
        text: Optional[str] = None,
        element_id: Union[str, NoID] = NoID(),
        coordinates: Optional[List[float]] = None,
        metadata: ElementMetadata = ElementMetadata(),
    ):
        super().__init__(text="<PAGE BREAK>")

    def to_markdown(self):
        return f"\n\n"


TYPE_TO_TEXT_ELEMENT_MAP: Dict[str, Any] = {
    "UncategorizedText": Text,
    "FigureCaption": FigureCaption,
    "NarrativeText": NarrativeText,
    "ListItem": ListItem,
    "BulletedText": ListItem,
    "Title": Title,
    "Address": Address,
    "Image": Image,
    "PageBreak": PageBreak,
}
