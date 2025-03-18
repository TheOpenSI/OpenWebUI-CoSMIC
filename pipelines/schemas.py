from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from typing import Union

class OpenAIChatMessage(BaseModel):
    role: str
    content: Union[str, List]
    content_cosmic: Optional[Union[str, List]] = None

    model_config = ConfigDict(extra="allow")


class OpenAIChatCompletionForm(BaseModel):
    stream: bool = True
    model: str
    messages: List[OpenAIChatMessage]

    model_config = ConfigDict(extra="allow")


class FilterForm(BaseModel):
    body: dict
    user: Optional[dict] = None
    model_config = ConfigDict(extra="allow")