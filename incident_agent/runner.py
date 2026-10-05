from __future__ import annotations

import asyncio
from typing import Callable

from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.genai.errors import ServerError

from incident_agent.config import settings
from incident_agent.result import PipelineResult, record_event


def print_event(event, *, verbose: bool = True) -> None:
    if not event.content or not event.content.parts:
        return
    for part in event.content.parts:
        if part.text:
            print(f"\n--- [{event.author}] ---\n{part.text}")
        if verbose and part.function_call:
            print(f"[{event.author}] CALLING TOOL: {part.function_call.name}")
        if verbose and part.function_response:
            payload = part.function_response.response
            preview = str(payload)
            if len(preview) > 400:
                preview = preview[:400] + "..."
            print(f"[{event.author}] TOOL RESULT: {preview}")


async def run_agent(
    agent: BaseAgent,
    user_trigger: str,
    *,
    on_event: Callable | None = print_event,
) -> PipelineResult:
    runner = InMemoryRunner(agent=agent, app_name=settings.app_name)
    result = PipelineResult()
    last_error: ServerError | None = None

    for attempt in range(1, settings.max_retries + 1):
        session = await runner.session_service.create_session(
            app_name=settings.app_name, user_id=settings.user_id
        )
        try:
            async for event in runner.run_async(
                user_id=settings.user_id,
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part(text=user_trigger)]
                ),
            ):
                record_event(result, event)
                if on_event:
                    on_event(event)
            return result
        except ServerError as exc:
            last_error = exc
            result = PipelineResult()
            if attempt < settings.max_retries:
                print(
                    f"  (Gemini busy, attempt {attempt}/{settings.max_retries} "
                    f"failed -- retrying in {settings.retry_delay_seconds}s...)"
                )
                await asyncio.sleep(settings.retry_delay_seconds)
            else:
                print(f"  Gave up after {settings.max_retries} attempts: {exc}")
                raise

    assert last_error is not None
    raise last_error
