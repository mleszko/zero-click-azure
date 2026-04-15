from __future__ import annotations

import logging
from dataclasses import dataclass

from core.settings import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GenerationInput:
    prompt: str
    required_facts: list[str]
    feedback: str
    attempt: int


class LLMService:
    """Encapsulates generation strategy with safe fallback behavior."""

    def __init__(self, settings: Settings):
        self._settings = settings

    def generate(self, payload: GenerationInput) -> str:
        if self._can_use_azure_openai:
            azure_response = self._generate_with_azure_openai(payload)
            if azure_response:
                return azure_response

        return self._generate_rule_based(payload)

    @property
    def _can_use_azure_openai(self) -> bool:
        return bool(
            self._settings.enable_azure_openai
            and self._settings.azure_openai_endpoint
            and self._settings.azure_openai_deployment
        )

    def _generate_with_azure_openai(self, payload: GenerationInput) -> str | None:
        """Use Azure OpenAI with managed identity and return None on soft failure."""

        try:
            from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
            from openai import AzureOpenAI
        except Exception as exc:  # pragma: no cover - optional dependency path
            logger.warning('Azure OpenAI dependencies unavailable: %s', exc)
            return None

        try:
            credential = self._build_credential(ManagedIdentityCredential, DefaultAzureCredential)
            token_provider = self._build_token_provider(credential)

            client = AzureOpenAI(
                azure_endpoint=self._settings.azure_openai_endpoint,
                api_version=self._settings.azure_openai_api_version,
                azure_ad_token_provider=token_provider,
            )

            system_prompt = (
                'You are a precise assistant. Include every required fact exactly once when possible. '
                'If feedback indicates missing facts, prioritize adding them.'
            )
            required_facts = '\n'.join(f'- {fact}' for fact in payload.required_facts) or '- none'
            user_prompt = (
                f"Prompt:\n{payload.prompt}\n\n"
                f"Required facts:\n{required_facts}\n\n"
                f"Attempt: {payload.attempt}\n"
                f"Feedback from grader: {payload.feedback or 'n/a'}"
            )

            completion = client.chat.completions.create(
                model=self._settings.azure_openai_deployment,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            return content.strip() if content else None
        except Exception as exc:  # pragma: no cover - integration failure handled gracefully
            logger.warning('Azure OpenAI generation failed, using fallback: %s', exc)
            return None

    def _build_credential(self, managed_identity_cls, default_credential_cls):
        if self._settings.azure_openai_managed_identity_client_id:
            return managed_identity_cls(
                client_id=self._settings.azure_openai_managed_identity_client_id,
            )
        return default_credential_cls(exclude_interactive_browser_credential=True)

    @staticmethod
    def _build_token_provider(credential):
        def token_provider() -> str:
            token = credential.get_token('https://cognitiveservices.azure.com/.default')
            return token.token

        return token_provider

    @staticmethod
    def _generate_rule_based(payload: GenerationInput) -> str:
        response_lines: list[str] = [f"Answer: {payload.prompt.strip()}"]

        cleaned_required_facts = [fact.strip() for fact in payload.required_facts if fact.strip()]
        if cleaned_required_facts:
            if payload.attempt == 1 and len(cleaned_required_facts) > 1:
                facts_to_include = cleaned_required_facts[:1]
            else:
                facts_to_include = cleaned_required_facts

            response_lines.append('Supporting facts:')
            response_lines.extend(f"- {fact}" for fact in facts_to_include)

        if payload.feedback:
            response_lines.append(f"Correction applied: {payload.feedback}")

        return '\n'.join(response_lines)
