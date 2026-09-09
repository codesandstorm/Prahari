from __future__ import annotations
import logging,time,uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from llm.rag.assistant import UnifiedPrahariAssistant
from llm.rag.retriever import LexicalRetriever
from .api import router
from .assistant_service import AssistantAdapter
from .config import get_settings

settings=get_settings()
logging.basicConfig(level=settings.log_level,format="%(asctime)s %(levelname)s %(name)s %(message)s")
LOG=logging.getLogger("prahari.api")


def default_assistant():
    if not settings.llm_enabled:return None
    try:
        try: retriever=LexicalRetriever.from_index(settings.rag_index_dir)
        except Exception as exc:
            LOG.warning("rag_initialization_failed reason=%s",type(exc).__name__);retriever=None
        return AssistantAdapter(UnifiedPrahariAssistant(retriever))
    except Exception as exc:
        LOG.warning("assistant_initialization_failed reason=%s",type(exc).__name__)
        return None


@asynccontextmanager
async def lifespan(app:FastAPI):
    if app.state.assistant is _DEFAULT: app.state.assistant=default_assistant()
    yield


_DEFAULT = object()

def create_app(assistant=_DEFAULT) -> FastAPI:
    app=FastAPI(title="PRAHARI Backend",version="1.0.0",description="Bounded decision-support API; predictions are not alerts.",lifespan=lifespan)
    app.state.assistant=assistant
    app.add_middleware(CORSMiddleware,allow_origins=list(settings.cors_origins),allow_credentials=True,allow_methods=["GET","POST"],allow_headers=["Content-Type","X-Request-ID"])
    @app.exception_handler(HTTPException)
    async def api_error(request:Request,exc:HTTPException):
        detail=exc.detail if isinstance(exc.detail,dict) else {"code":"HTTP_ERROR","message":str(exc.detail)}
        return JSONResponse(status_code=exc.status_code,content={"error":detail})
    @app.exception_handler(RequestValidationError)
    async def validation_error(request:Request,exc:RequestValidationError):
        return JSONResponse(status_code=422,content={"error":{"code":"VALIDATION_ERROR","message":"Request validation failed","details":exc.errors()}})
    @app.middleware("http")
    async def request_log(request:Request,call_next):
        started=time.perf_counter();rid=request.headers.get("X-Request-ID") or str(uuid.uuid4())
        try:response=await call_next(request)
        except Exception:
            LOG.exception("request_failed request_id=%s route=%s",rid,request.url.path)
            return JSONResponse(status_code=500,content={"error":{"code":"INTERNAL_ERROR","message":"Unexpected internal error","request_id":rid}})
        response.headers["X-Request-ID"]=rid
        LOG.info("request request_id=%s route=%s status=%d duration_ms=%.2f",rid,request.url.path,response.status_code,(time.perf_counter()-started)*1000)
        return response
    app.include_router(router,prefix=settings.api_prefix)
    return app


app=create_app()
