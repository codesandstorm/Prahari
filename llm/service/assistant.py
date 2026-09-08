"""Grounded PRAHARI explanation service: evidence in, validated response or fallback out."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from llm.schemas.evidence import PrahariEvidence
from llm.schemas.response import PrahariResponse
from llm.service.fallback import deterministic_fallback
from llm.service.ollama_client import GenerationSettings, OllamaClient
from llm.service.output_validator import validate_output
from llm.service.prompt_builder import build_prompt

ROOT=Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class AssistantResult:
    response: PrahariResponse
    model: str
    used_fallback: bool
    fallback_reason: str | None
    latency_seconds: float | None

class PrahariAssistant:
    def __init__(self,config_path:Path|None=None,client:OllamaClient|None=None):
        path=config_path or ROOT/"llm/prototype_config.json"
        self.config=json.loads(path.read_text(encoding="utf-8"))
        self.system=(ROOT/self.config["system_prompt"]).read_text(encoding="utf-8")
        self.client=client or OllamaClient(self.config["ollama_base_url"],self.config["timeout_seconds"])

    def explain(self,evidence_data:dict[str,Any],officer_question:str)->AssistantResult:
        evidence=PrahariEvidence.from_dict(evidence_data)
        prompt=build_prompt(evidence,officer_question)
        settings=GenerationSettings(temperature=self.config["temperature"],seed=self.config["seed"],
                                    num_predict=self.config["num_predict"],top_p=self.config["top_p"])
        generated=self.client.generate(self.config["model"],self.system,prompt,settings)
        failure=generated.get("error") or generated.get("parse_error")
        validation=validate_output(generated.get("parsed_response"),evidence) if not failure else None
        if failure or validation is None or not validation.valid:
            reason=str(failure or "; ".join(validation.errors))
            return AssistantResult(deterministic_fallback(evidence,reason,officer_question),self.config["model"],True,reason,generated.get("latency_seconds"))
        return AssistantResult(validation.response,self.config["model"],False,None,generated.get("latency_seconds"))

    @staticmethod
    def serialize(result:AssistantResult)->dict[str,Any]:
        data=asdict(result); return data
