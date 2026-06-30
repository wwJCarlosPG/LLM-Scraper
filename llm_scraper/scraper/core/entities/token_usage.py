from dataclasses import dataclass
from typing import Literal


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    role: Literal["scorer", "extractor", "validator"] = "extractor"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
