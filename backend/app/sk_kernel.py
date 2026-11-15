"""Microsoft Semantic Kernel agent framework integration for T.H.E.M.I.S.

Provides:
- Kernel instantiation with OpenAI-compatible Groq ChatCompletion service
- Specialized Agent Plugins decorated with @kernel_function
- Grounded retrieval and arithmetic execution tools registered within Semantic Kernel
"""
import asyncio
import json
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
import semantic_kernel as sk
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function

from . import config
from .documents import Retriever, verify_quote


class GroundedRetrievalPlugin:
    """Semantic Kernel Plugin for Grounded RAG Retrieval over bid documents."""

    @kernel_function(
        name="retrieve_evidence",
        description="Retrieves the most relevant passages from a document using BM25 ranking.",
    )
    def retrieve_evidence(self, document_text: str, query: str, top_k: int = 4) -> str:
        retriever = Retriever(document_text)
        results = retriever.search(query, k=top_k)
        return "\n---\n".join(results)

    @kernel_function(
        name="verify_quote",
        description="Verifies whether a quoted excerpt exists verbatim inside the source document.",
    )
    def verify_quote(self, quote: str, document_text: str) -> bool:
        return verify_quote(quote, document_text)


class FinancialArithmeticPlugin:
    """Semantic Kernel Plugin for deterministic arithmetic verification of prices."""

    @kernel_function(
        name="recompute_item",
        description="Computes amount = qty * unit_price with zero floating point drift.",
    )
    def recompute_item(self, qty: float, unit_price: float) -> float:
        return round(float(qty) * float(unit_price), 2)

    @kernel_function(
        name="recompute_total",
        description="Sums line item amounts and checks against quoted total.",
    )
    def recompute_total(self, amounts_json: str, stated_total: float) -> str:
        try:
            amounts = json.loads(amounts_json)
            calc_sum = round(sum(float(x) for x in amounts), 2)
            diff = round(abs(calc_sum - float(stated_total)), 2)
            match = diff <= 1.0
            return json.dumps({
                "recomputed_total": calc_sum,
                "stated_total": float(stated_total),
                "difference": diff,
                "matches": match,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})


class TenderParserPlugin:
    """Semantic Kernel Plugin for Tender Requirements Extraction Agent."""

    @kernel_function(
        name="extract_criteria_prompt",
        description="Builds the structured prompt for extracting evaluation rubric from a tender document.",
    )
    def extract_criteria_prompt(self, tender_text: str) -> str:
        return f"Extract all mandatory eligibility criteria and technical scoring criteria from the tender:\n\n{tender_text[:4000]}"


class ClarificationAgentPlugin:
    """Semantic Kernel Plugin for Clarification Loop Agent."""

    @kernel_function(
        name="format_clarification_inquiry",
        description="Formats a structured clarification request for a vendor on an unclear criterion.",
    )
    def format_clarification_inquiry(self, criterion_id: str, requirement: str, missing_info: str) -> str:
        return (
            f"CLARIFICATION NOTICE for Criterion {criterion_id}:\n"
            f"Requirement: {requirement}\n"
            f"Identified Defect / Ambiguity: {missing_info}\n"
            f"Please submit verified documentary evidence within 48 hours."
        )


def build_kernel(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    service_id: str = "themis-groq",
) -> Kernel:
    """Constructs and returns a Semantic Kernel instance wired to Groq with agent plugins."""
    kernel = Kernel()

    chosen_model = model or config.DEFAULT_MODEL
    key = api_key or config.GROQ_API_KEY

    if key:
        # Groq provides OpenAI-compatible endpoint at https://api.groq.com/openai/v1
        async_client = AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        chat_service = OpenAIChatCompletion(
            ai_model_id=chosen_model,
            service_id=service_id,
            async_client=async_client,
        )
        kernel.add_service(chat_service)

    # Register specialized multi-agent plugins into the Kernel
    kernel.add_plugin(GroundedRetrievalPlugin(), plugin_name="RetrievalPlugin")
    kernel.add_plugin(FinancialArithmeticPlugin(), plugin_name="FinancialArithmeticPlugin")
    kernel.add_plugin(TenderParserPlugin(), plugin_name="TenderParserPlugin")
    kernel.add_plugin(ClarificationAgentPlugin(), plugin_name="ClarificationAgentPlugin")

    return kernel


async def run_chat_completion(
    kernel: Kernel,
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = True,
    service_id: str = "themis-groq",
) -> str:
    """Executes a chat completion through the Semantic Kernel chat service."""
    service = kernel.get_service(service_id)
    chat = ChatHistory()
    chat.add_system_message(system_prompt)
    chat.add_user_message(user_prompt)

    settings = OpenAIChatPromptExecutionSettings(
        temperature=0.1,
        max_tokens=4096,
    )
    if json_mode:
        settings.response_format = {"type": "json_object"}

    response = await service.get_chat_message_content(chat_history=chat, settings=settings)
    return str(response.content or "")
