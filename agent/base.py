"""
Bhujal — Autonomous Agent Base Framework
=========================================
Provides foundational interfaces, Bedrock client invocation, and deterministic
template fallback engines for all specialized analytical agents.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

import boto3
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Unified response envelope emitted by any Bhujal agent."""

    agent_name: str
    role: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    narrative: str
    recommendations: list[str] = Field(default_factory=list)
    mode: str = Field(
        "deterministic_fallback", description="'bedrock' or 'deterministic_fallback'"
    )


class BaseAgent:
    """
    Abstract base class for domain specialist agents.
    Tries Amazon Bedrock invocation first; gracefully degrades to
    deterministic domain template synthesis when cloud credentials are unconfigured.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model_id: str | None = None,
        region: str | None = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"
        )
        self.region = region or os.getenv(
            "BEDROCK_REGION", os.getenv("AWS_REGION", "ap-south-1")
        )
        # Initialize Bedrock cache table if configured
        self.bedrock_cache_table = os.getenv("DYNAMODB_TABLE_BEDROCK_CACHE")
        if self.bedrock_cache_table:
            self.dynamodb = boto3.resource("dynamodb")
            self.cache_table = self.dynamodb.Table(self.bedrock_cache_table)

    def _get_cache_key(self, prompt: str) -> str:
        """Generate a cache key for Bedrock invocation based on prompt and system parameters."""
        key_string = f"{self.system_prompt}|{prompt}|{self.model_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _invoke_bedrock(self, prompt: str) -> str | None:
        """Attempt invoking Claude 3 Sonnet on Amazon Bedrock."""
        # Check if Bedrock usage is disabled via environment variable
        use_bedrock = os.getenv("USE_BEDROCK", "true").lower()
        if use_bedrock == "false":
            return None

        # Generate cache key
        cache_key = self._get_cache_key(prompt)

        # Try to get from cache if cache table is configured
        if self.bedrock_cache_table:
            try:
                response = self.cache_table.get_item(Key={"cache_key": cache_key})
                if "Item" in response:
                    logger.debug("Bedrock cache hit for key: %s", cache_key)
                    return response["Item"].get("cached_narrative")
            except Exception as e:  # noqa: BLE001
                logger.debug("Bedrock cache get failed: %s", e)
                # Continue to Bedrock invocation on cache error

        # Fast bail-out if no credentials exist in environment or ~/.aws/credentials
        has_env_creds = bool(
            os.getenv("AWS_ACCESS_KEY_ID")
            or os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
            or os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE")
        )
        has_file_creds = os.path.exists(os.path.expanduser("~/.aws/credentials"))
        if not (has_env_creds or has_file_creds):
            return None

        try:
            import boto3
            from botocore.config import Config

            cfg = Config(connect_timeout=2, read_timeout=5, retries={"max_attempts": 0})
            client = boto3.client(
                "bedrock-runtime", region_name=self.region, config=cfg
            )
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "system": self.system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.2,
            }

            response = client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )
            resp_body = json.loads(response["body"].read().decode("utf-8"))
            narrative = resp_body.get("content", [{}])[0].get("text", "")

            # Cache the result if cache table is configured
            if self.bedrock_cache_table:
                try:
                    self.cache_table.put_item(
                        Item={
                            "cache_key": cache_key,
                            "cached_narrative": narrative,
                        }
                    )
                    logger.debug("Bedrock cache stored for key: %s", cache_key)
                except Exception as e:  # noqa: BLE001
                    logger.debug("Bedrock cache put failed: %s", e)

            return narrative
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Bedrock invocation bypassed (%s). Falling back to deterministic synthesis.",
                e,
            )
            return None

    def execute(self, context: dict[str, Any]) -> AgentResponse:
        """Execute agent analysis with automated Bedrock / fallback selection."""
        prompt = self.build_prompt(context)
        bedrock_narrative = self._invoke_bedrock(prompt)

        if bedrock_narrative:
            summary, recs = self.parse_narrative(bedrock_narrative, context)
            return AgentResponse(
                agent_name=self.name,
                role=self.role,
                summary=summary,
                details=context,
                narrative=bedrock_narrative,
                recommendations=recs,
                mode="bedrock",
            )

        # Fallback to deterministic expert synthesis
        return self.fallback_execute(context)

    def build_prompt(self, context: dict[str, Any]) -> str:
        """Construct user message for the LLM."""

        def serialize_default(o: Any) -> Any:
            if hasattr(o, "model_dump"):
                return o.model_dump()
            return str(o)

        serialized = json.dumps(context, indent=2, default=serialize_default)
        return (
            f"Analyze the following deterministic hydrogeological data:\n{serialized}"
        )

    def parse_narrative(
        self, narrative: str, context: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Extract executive summary and bullet points from generated narrative."""
        lines = [line.strip() for line in narrative.split("\n") if line.strip()]
        summary = lines[0] if lines else "Analysis completed."
        recs = [
            line.lstrip("-*123456789. ")
            for line in lines
            if line.startswith(("-", "*"))
        ][:4]
        return summary, recs

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        """Deterministic domain synthesis logic overridden by subclasses."""
        raise NotImplementedError
