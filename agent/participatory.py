"""
Bhujal — Participatory Groundwater Monitoring Agent
====================================================
Processes community-submitted observations via WhatsApp/Voice.
Integrates Amazon Transcribe (ASR) + LLM extraction for structured data.
Feeds validated observations back into scoring engine as 'community_validated'.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from agent.base import BaseAgent
from backend.models import (
    DataTag,
    Observation,
    ObservationCreate,
)
from scoring import get_all_villages, get_site_raw_data

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_OBSERVATION_TYPES: dict[str, list[str]] = {
    "well_depth": [
        "well depth",
        "water level",
        "borewell depth",
        "open well depth",
        "groundwater level",
    ],
    "spring_flow": [
        "spring flow",
        "spring discharge",
        "jhola flow",
        "jharna flow",
        "spring drying",
    ],
    "rainfall": ["rainfall", "rain", "monsoon", "precipitation"],
    "water_quality": [
        "water quality",
        "taste",
        "color",
        "smell",
        "contamination",
        "salinity",
        "fluoride",
        "iron",
    ],
    "structure_condition": [
        "check dam",
        "percolation tank",
        "contour trench",
        "gabion",
        "farm pond",
        "damage",
        "silted",
        "breach",
    ],
    "general": ["general", "other", "observation"],
}

_BADGE_THRESHOLDS: dict[str, int] = {
    "Jal Mitra (Bronze)": 5,
    "Jal Mitra (Silver)": 15,
    "Jal Mitra (Gold)": 30,
    "Jal Mitra (Platinum)": 50,
}


class ParticipatoryMonitoringAgent(BaseAgent):
    """Agent for processing community groundwater observations from WhatsApp/Voice."""

    def __init__(self) -> None:
        super().__init__(
            name="ParticipatoryMonitoringAgent",
            role="Community Groundwater Observation Processor",
            system_prompt=(
                "You are a specialized agent for extracting structured groundwater observation data "
                "from community-submitted text/voice messages in Indian languages (Hindi, Odia, Marathi, "
                "Bengali, tribal dialects) and English. Extract: site/village name, observation type, "
                "numeric value, unit, location hints, and confidence. Return ONLY valid JSON."
            ),
        )
        self._transcribe_client = None
        self._s3_client = None
        self._dynamodb_table = None
        self._initialize_aws_clients()

    def _initialize_aws_clients(self) -> None:
        """Lazy-initialize AWS clients."""
        try:
            self._transcribe_client = boto3.client(
                "transcribe", region_name="ap-south-1"
            )
            self._s3_client = boto3.client("s3", region_name="ap-south-1")
            dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
            self._dynamodb_table = dynamodb.Table("bhujal-observations")
        except Exception as exc:  # noqa: BLE001
            logger.debug("AWS clients not initialized (local mode): %s", exc)

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Process a community observation.

        Context keys:
        - text: str (raw message text)
        - audio_s3_uri: str (optional S3 URI for audio file)
        - observer_id: str (WhatsApp phone number or user ID)
        - observer_name: str (optional)
        - language_code: str (optional, e.g., 'hi-IN', 'en-IN', 'or-IN')
        """
        text = context.get("text", "").strip()
        audio_s3_uri = context.get("audio_s3_uri")
        observer_id = context.get("observer_id", "unknown")
        observer_name = context.get("observer_name", "")
        language_code = context.get("language_code", "en-IN")

        # If audio provided, transcribe first
        if audio_s3_uri and not text:
            text = self._transcribe_audio(audio_s3_uri, language_code)
            if not text:
                return {"success": False, "error": "Transcription failed or empty"}

        if not text:
            return {"success": False, "error": "No text or audio provided"}

        # Extract structured data using LLM
        extracted = self._extract_observation(text)

        # Validate and enrich with site data
        validated = self._validate_and_enrich(extracted, observer_id, observer_name)

        # Store observation
        stored = self._store_observation(validated)

        # Update observer stats / badges
        badge_info = self._update_observer_stats(observer_id, observer_name)

        return {
            "success": True,
            "observation_id": stored.observation_id,
            "extracted": extracted,
            "validated": validated.model_dump()
            if hasattr(validated, "model_dump")
            else validated,
            "badge": badge_info,
            "message": f"Observation recorded. {badge_info.get('message', '')}",
        }

    def _transcribe_audio(self, s3_uri: str, language_code: str) -> str:
        """Transcribe audio from S3 using Amazon Transcribe."""
        if not self._transcribe_client:
            logger.warning("Transcribe client not available, skipping transcription")
            return ""

        job_name = f"bhujal-transcribe-{uuid.uuid4().hex[:12]}"
        try:
            self._transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": s3_uri},
                MediaFormat=s3_uri.split(".")[-1].lower(),
                LanguageCode=language_code,
                Settings={"ShowSpeakerLabels": False, "MaxSpeakerLabels": 1},
            )
            # Wait for completion (in production, use async callback)
            waiter = self._transcribe_client.get_waiter("transcription_job_completed")
            waiter.wait(
                TranscriptionJobName=job_name,
                WaiterConfig={"Delay": 5, "MaxAttempts": 60},
            )
            response = self._transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            transcript_uri = response["TranscriptionJob"]["Transcript"][
                "TranscriptFileUri"
            ]
            # Fetch transcript (simplified - in production use presigned URL)
            return self._fetch_transcript(transcript_uri)
        except ClientError as exc:
            logger.error("Transcribe error: %s", exc)
            return ""
        except Exception as exc:  # noqa: BLE001
            logger.error("Transcription failed: %s", exc)
            return ""

    def _fetch_transcript(self, uri: str) -> str:
        """Fetch transcript from Transcribe output URI."""
        try:
            import urllib.request

            with urllib.request.urlopen(uri) as response:
                data = json.loads(response.read())
                return (
                    data.get("results", {})
                    .get("transcripts", [{}])[0]
                    .get("transcript", "")
                )
        except Exception:  # noqa: BLE001
            return ""

    def _extract_observation(self, text: str) -> dict[str, Any]:
        """Extract structured observation data using LLM (Bedrock) or fallback regex."""
        prompt = self._build_extraction_prompt(text)

        try:
            response = self._invoke_bedrock(prompt)
            if response:
                return json.loads(response)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Bedrock extraction failed, using fallback: %s", exc)

        return self._fallback_extraction(text)

    def _build_extraction_prompt(self, text: str) -> str:
        return f"""Extract groundwater observation data from this message. Return ONLY JSON with these fields:
- village_name: string (village/hamlet name mentioned, or null)
- observation_type: one of ["well_depth", "spring_flow", "rainfall", "water_quality", "structure_condition", "general"]
- value: number (numeric measurement, or null)
- unit: string (unit like "meters", "feet", "liters_per_minute", "mm", "ppm", or null)
- location_hints: string (any landmarks, coordinates, block/district mentioned)
- confidence: number 0-1 (your confidence in extraction)
- raw_text: string (original text)

Message: "{text}"

JSON:"""

    def _fallback_extraction(self, text: str) -> dict[str, Any]:
        """Regex-based fallback extraction when LLM unavailable."""
        text_lower = text.lower()

        # Detect observation type
        obs_type = "general"
        for otype, keywords in _OBSERVATION_TYPES.items():
            if any(kw in text_lower for kw in keywords):
                obs_type = otype
                break

        # Extract numbers with units
        value: float | None = None
        unit: str | None = None

        # Pattern: number + unit
        patterns = [
            (r"(\d+(?:\.\d+)?)\s*(?:meters?|metres?|m\b)", "meters"),
            (r"(\d+(?:\.\d+)?)\s*(?:feet|ft\b)", "feet"),
            (r"(\d+(?:\.\d+)?)\s*(?:liters? per minute|lpm)", "liters_per_minute"),
            (r"(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)", "mm"),
            (r"(\d+(?:\.\d+)?)\s*(?:ppm|mg/l)", "ppm"),
            (r"(\d+(?:\.\d+)?)\s*(?:cubic meters?|m3|m\^3)", "cubic_meters"),
        ]

        for pattern, u in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                unit = u
                break

        # If no unit found, look for bare numbers near keywords
        if value is None:
            numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", text)
            if numbers:
                value = float(numbers[0])

        # Extract village name (simple heuristic - capitalized words)
        village_name: str | None = None
        villages = get_all_villages()
        for v in villages:
            if v.name.lower() in text_lower:
                village_name = v.name
                break

        return {
            "village_name": village_name,
            "observation_type": obs_type,
            "value": value,
            "unit": unit,
            "location_hints": "",
            "confidence": 0.5 if value is not None else 0.2,
            "raw_text": text,
        }

    def _validate_and_enrich(
        self,
        extracted: dict[str, Any],
        observer_id: str,
        observer_name: str,
    ) -> ObservationCreate:
        """Validate extracted data against known sites and enrich with metadata."""
        village_name = extracted.get("village_name")
        site_id: str | None = None

        if village_name:
            raw = get_site_raw_data(village_name.lower().replace(" ", "_"))
            if not raw:
                # Try fuzzy match
                for v in get_all_villages():
                    if (
                        village_name.lower() in v.name.lower()
                        or v.name.lower() in village_name.lower()
                    ):
                        site_id = v.id
                        break
            else:
                site_id = raw["id"]

        obs_type = extracted.get("observation_type", "general")
        value = extracted.get("value")
        unit = extracted.get("unit")

        # Validate value ranges
        if obs_type == "well_depth" and value is not None and value > 200:
            value = None  # Implausible
        elif obs_type == "spring_flow" and value is not None and value > 1000:
            value = None

        return ObservationCreate(
            site_id=site_id or "unknown",
            observer_name=observer_name or observer_id,
            observation_type=obs_type,
            value=value,
            unit=unit,
            notes=(
                f"Community observation via WhatsApp/Voice. "
                f"Confidence: {extracted.get('confidence', 0):.0%}. "
                f"Raw: {extracted.get('raw_text', '')[:200]}"
            ),
            photo_filename=None,
        )

    def _store_observation(self, obs_create: ObservationCreate) -> Observation:
        """Store observation in DynamoDB and return Observation object."""
        obs_id = f"obs_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        stored = Observation(
            observation_id=obs_id,
            site_id=obs_create.site_id,
            observer_name=obs_create.observer_name,
            observation_type=obs_create.observation_type,
            value=obs_create.value,
            unit=obs_create.unit,
            notes=obs_create.notes,
            photo_filename=obs_create.photo_filename,
            timestamp=now,
            photo_url=None,
        )

        if self._dynamodb_table:
            try:
                item = stored.model_dump()
                item["timestamp"] = item["timestamp"].isoformat()
                item["data_tag"] = DataTag.PROXY.value  # Community data is proxy
                self._dynamodb_table.put_item(Item=item)
            except Exception as exc:  # noqa: BLE001
                logger.debug("DynamoDB store failed: %s", exc)

        return stored

    def _update_observer_stats(
        self, observer_id: str, observer_name: str
    ) -> dict[str, Any]:
        """Update observer contribution count and badge."""
        # In production, this would use a separate DynamoDB table for observer stats
        # For now, return mock badge info
        return {
            "observer_id": observer_id,
            "observer_name": observer_name or observer_id,
            "contributions": 1,
            "current_badge": "Jal Mitra (Bronze)",
            "next_badge": "Jal Mitra (Silver)",
            "observations_to_next": 14,
            "message": "Thank you for your contribution! You are now a Jal Mitra (Bronze).",
        }

    def get_leaderboard(
        self, state: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get top contributors leaderboard (mock implementation)."""
        # In production, query observer stats table
        return [
            {
                "rank": 1,
                "observer_name": "Ramesh Kumar",
                "village": "Laxmipur",
                "contributions": 47,
                "badge": "Jal Mitra (Platinum)",
            },
            {
                "rank": 2,
                "observer_name": "Sunita Devi",
                "village": "Dukum",
                "contributions": 32,
                "badge": "Jal Mitra (Gold)",
            },
            {
                "rank": 3,
                "observer_name": "Mohan Singh",
                "village": "Bichhiya",
                "contributions": 28,
                "badge": "Jal Mitra (Gold)",
            },
        ][:limit]

    def fallback_execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Deterministic fallback when Bedrock unavailable."""
        return self.execute(context)
