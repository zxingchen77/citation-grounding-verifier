import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from grounding.models import VerificationError, VerifyRequest, VerifyResponse
from grounding.provider import Model, Settings, create_model
from grounding.verifiers import METHODS, verify


def create_app(model: Model | None = None, method: str | None = None) -> FastAPI:
    app = FastAPI(title="Citation Grounding Verifier", version="0.1.0")
    settings = Settings.from_env()
    selected = method or os.getenv("VERIFIER_METHOD", "optimized")
    if selected not in METHODS:
        raise ValueError("Invalid VERIFIER_METHOD")
    provider = model if model is not None else create_model(settings)

    @app.exception_handler(VerificationError)
    async def verification_error(_request: Request, exc: VerificationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/health")
    async def health():
        return {"status": "ok", "method": selected}

    @app.post("/verify", response_model=VerifyResponse)
    async def verify_endpoint(body: VerifyRequest):
        return await verify(body, selected, provider, timeout=settings.request_timeout)

    return app


app = create_app()
