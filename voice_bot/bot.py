"""Pipecat voice bot entrypoint for InsureFlow customer workflows."""

from __future__ import annotations

import logging

from dotenv import load_dotenv

from voice_bot.config import get_voice_bot_settings
from voice_bot.functions import build_tools_schema, build_voice_tool_definitions, register_voice_tools
from voice_bot.prompts import VOICE_BOT_SYSTEM_PROMPT
from voice_bot.runtime import VoiceBotRuntime
from voice_bot.session_handlers import (
    register_llm_event_handlers,
    register_session_event_handlers,
)
from voice_bot.transports import TRANSPORT_PARAMS

try:
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.worker import PipelineParams, PipelineWorker
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
    )
    from pipecat.runner.types import RunnerArguments
    from pipecat.runner.utils import create_transport
    from pipecat.services.cartesia.tts import CartesiaTTSService
    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.groq.llm import GroqLLMService
    from pipecat.transports.base_transport import BaseTransport
    from pipecat.workers.runner import WorkerRunner
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise RuntimeError(
        "Pipecat voice dependencies are not installed. Install voice_bot/requirements.txt first."
    ) from exc

load_dotenv(override=True)

logger = logging.getLogger(__name__)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    """Build the Pipecat pipeline and start the InsureFlow voice session."""

    runtime = VoiceBotRuntime.build()
    settings = get_voice_bot_settings()
    definitions = build_voice_tool_definitions(runtime)

    logger.info("starting voice bot")

    stt = DeepgramSTTService(api_key=settings.deepgram_api_key)
    tts = CartesiaTTSService(
        api_key=settings.cartesia_api_key,
        settings=CartesiaTTSService.Settings(voice=settings.cartesia_voice_id),
    )
    llm = GroqLLMService(
        api_key=settings.groq_api_key,
        settings=GroqLLMService.Settings(
            model=settings.groq_model,
            system_instruction=VOICE_BOT_SYSTEM_PROMPT,
        ),
    )

    register_voice_tools(llm=llm, definitions=definitions)
    register_llm_event_handlers(llm=llm, tts=tts, settings=settings)

    context = LLMContext(tools=build_tools_schema(definitions))
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )
    register_session_event_handlers(
        transport=transport,
        worker=worker,
        tts=tts,
        context=context,
        settings=settings,
        logger=logger,
    )

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)
    await runner.run()


async def bot(runner_args: RunnerArguments) -> None:
    """Main Pipecat bot entrypoint used by local and hosted transports."""

    transport = await create_transport(runner_args, TRANSPORT_PARAMS)
    await run_bot(transport, runner_args)
