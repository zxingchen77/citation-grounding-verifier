from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Verdict = Literal["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class VerifyRequest(StrictModel):
    context_passages: list[str] = Field(max_length=32)
    generated_answer: str = Field(max_length=16000)

    @model_validator(mode="after")
    def limit_context(self):
        if any(len(p) > 32000 for p in self.context_passages):
            raise ValueError("each passage must contain at most 32000 characters")
        if sum(map(len, self.context_passages)) > 100000:
            raise ValueError("context must contain at most 100000 characters")
        return self


class Citation(StrictModel):
    index: int = Field(ge=0)
    quote: str = Field(min_length=1, max_length=32000)


class Claim(StrictModel):
    claim_text: str = Field(min_length=1, max_length=4000)
    verdict: Verdict
    reasoning: str = Field(min_length=1, max_length=2000)
    citations: list[Citation] = Field(max_length=8)


class VerifyResponse(StrictModel):
    claims: list[Claim] = Field(max_length=64)


class ExtractedClaim(StrictModel):
    claim_text: str = Field(min_length=1, max_length=4000)
    answer_quote: str = Field(min_length=1, max_length=16000)


class Extraction(StrictModel):
    claims: list[ExtractedClaim] = Field(max_length=64)


class Judgment(StrictModel):
    claim_index: int = Field(ge=0)
    verdict: Verdict
    reasoning: str = Field(min_length=1, max_length=2000)
    citations: list[Citation] = Field(max_length=8)


class Judgments(StrictModel):
    judgments: list[Judgment] = Field(max_length=64)


class VerificationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_evidence(report: VerifyResponse, passages: list[str]) -> VerifyResponse:
    for i, claim in enumerate(report.claims):
        if not claim.claim_text.strip() or not claim.reasoning.strip():
            raise VerificationError("invalid_output", f"claim {i}: blank text or reasoning")
        if (claim.verdict == "UNSUPPORTED") != (len(claim.citations) == 0):
            raise VerificationError("invalid_output", f"claim {i}: verdict/citation mismatch")
        for citation in claim.citations:
            if citation.index >= len(passages):
                raise VerificationError("invalid_output", f"claim {i}: citation index out of range")
            if not citation.quote.strip() or citation.quote not in passages[citation.index]:
                raise VerificationError("invalid_output", f"claim {i}: quote not verbatim")
    return report
