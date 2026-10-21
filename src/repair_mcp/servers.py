from contextlib import asynccontextmanager
import threading
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from .config import read_json
from .labels import SURFACE_DEFECTS, interpret_damage_labels, interpret_pcb_labels
from .models import SearchRequest
from .normalize import normalize_observations

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True,
             "openWorldHint": False}
AI_READ_ONLY = {**READ_ONLY, "idempotentHint": False, "openWorldHint": True}


def create_server(service: str, store=None) -> FastMCP:
    @asynccontextmanager
    async def lifespan(server):
        try:
            yield {}
        finally:
            if service == "rag" and instance[0] is not None and store is None:
                instance[0].close()
                instance[0] = None

    instance = [store]
    init_lock = threading.Lock()
    mcp = FastMCP(f"{service}-mcp", lifespan=lifespan,
                 instructions="Read-only interpretation/retrieval. Model labels are observations, not confirmed fault causes.")
    if service == "observation":
        @mcp.tool(annotations=AI_READ_ONLY)
        def normalize_observation(raw_text: Annotated[str, Field(min_length=1, max_length=2000)],
                                  origin: Literal["technician", "ai_image"] = "technician",
                                  technician_confirmed: bool = False) -> dict:
            """OpenAI로 기사 소견을 표준 용어 후보로 변환. 부정·추정·원문·미등록 표현 보존."""
            return normalize_observations(raw_text, origin, technician_confirmed)

        @mcp.tool(annotations=READ_ONLY)
        def list_observation_terms() -> dict:
            """지원하는 소견 코드와 출처를 반환."""
            return read_json("observation_vocabulary.json")
    elif service == "pcb":
        @mcp.tool(annotations=READ_ONLY)
        def interpret_pcb(labels: Annotated[list[Annotated[str, Field(min_length=1, max_length=100)]],
                                           Field(max_length=30)]) -> dict:
            """팀 PCB 모델의 라벨 결과를 해석. 이미지 추론·고장 원인 확정은 수행하지 않음."""
            return interpret_pcb_labels(labels)
    elif service == "damage":
        @mcp.tool(annotations=READ_ONLY)
        def interpret_damage(labels: Annotated[list[Annotated[str, Field(min_length=1, max_length=100)]],
                                              Field(max_length=30)]) -> dict:
            """외형 표면 결함 6종을 해석. 좌표·부위·심각도는 추정하지 않음."""
            return interpret_damage_labels(labels)

        @mcp.tool(annotations=READ_ONLY)
        def list_damage_labels() -> dict:
            """지원하는 표면 결함 라벨과 한국어 이름."""
            return {label: {"name_ko": name, "description_ko": description}
                    for label, (name, description) in SURFACE_DEFECTS.items()}
    elif service == "rag":
        def get_store():
            with init_lock:
                if instance[0] is None:
                    from .retrieval import DenseStore
                    instance[0] = DenseStore()
                return instance[0]

        @mcp.tool(annotations=AI_READ_ONLY)
        def retrieve_repair_context(request: SearchRequest) -> dict:
            """소견+PCB+외형 라벨로 사례·기술 문서 검색 및 정확한 라벨의 점검 지침 조회.
            근거별 출처, 증상 판정, 점검 순서를 반환. 내부에서 OpenAI 소견 변환 호출.
            외형 지침은 위치를 지정하지 않는 표면 점검 팀 초안. 확정 진단/DB 저장/승인은 수행하지 않음.
            """
            from .retrieval import retrieve_context
            return retrieve_context(request, get_store())

        @mcp.tool(annotations=READ_ONLY)
        def search_reference_documents(query: Annotated[str, Field(min_length=1, max_length=2000)],
                                       collection: Literal["pcb_documents", "damage_documents"],
                                       top_k: Annotated[int, Field(ge=1, le=20)] = 5,
                                       min_score: Annotated[float, Field(ge=-1, le=1)] = 0.75) -> dict:
            """PCB/파손 문서의 독립 dense 검색. 사례와 문서의 출처 유형을 분리."""
            return {"documents": get_store().search(collection, query, top_k, min_score)}
    else:
        raise ValueError(f"Unknown MCP service: {service}")
    return mcp
