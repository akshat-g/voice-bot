import os
import sys

from dotenv import load_dotenv
from loguru import logger
from openai.types.chat import ChatCompletionToolParam
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.filters.stt_mute_filter import STTMuteConfig, STTMuteFilter, STTMuteStrategy
from pipecat.services.deepgram import (
    DeepgramSTTService,
    LiveOptions,
)
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.openai import OpenAILLMService, BaseOpenAILLMService

from app.pipecat.processors.dynamic_vad_threshold_processor import DynamicVADThresholdProcessor
from app.pipecat.services.eleven_labs import AHElevenLabsTTSService


load_dotenv()
logger.add(sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss} | {level} | {module}:{function} | {message} | {extra}")


def extract_tools_from_api_tools(api_tools):
    """
    Extract tools from the api_tools configuration and convert them into ChatCompletionToolParam instances.
    :param api_tools: Dictionary containing tools and their parameters.
    :return: List of ChatCompletionToolParam instances.
    """
    tools = []
    if not api_tools or not api_tools.get("tools"):
        return tools

    for tool in api_tools["tools"]:
        function = {
            "name": tool.get("name"),
            "description": tool.get("description"),
            "parameters": tool.get("parameters", None),
        }

        tools.append(ChatCompletionToolParam(type="function", function=function))

    return tools


def create_openai_context(messages, api_tools):
    """
    Create an OpenAILLMContext instance with optional tools if provided.
    :param messages: List of message dictionaries.
    :param api_tools: Dictionary containing tools and their parameters.
    :return: OpenAILLMContext instance.
    """
    tools = extract_tools_from_api_tools(api_tools)
    if tools:
        return OpenAILLMContext(messages, tools)
    return OpenAILLMContext(messages)


class PipecatBot:
    def __init__(self, script: str, variables: dict, pipeline_config: dict, **kwargs):
        self.script: str = script
        self.variables: dict = variables
        self.pipeline_config: dict = pipeline_config
        self.kwargs: dict = kwargs
        self.pipeline: Pipeline | None = None
        self.conversation_history: list = []
        self.is_transferred: bool = False
        self.room_url: str = os.getenv("DAILY_ROOM_URL", "")

    class DictWithMissing(dict):
        def __missing__(self, key):
            return ''

    def setup_pipeline_context(self, messages, api_tools=None):
        """
        Setup the OpenAILLMContext for the pipeline.
        :param messages: List of message dictionaries.
        :return: OpenAILLMContext instance.
        """
        return create_openai_context(messages, api_tools)

    def setup_pipeline(self):
        vad_analyzer = SileroVADAnalyzer(
            sample_rate=16000,
            params=VADParams(
                confidence=0.85,
                min_volume=0.7,
            ),
        )
        transport = DailyTransport(
            room_url=self.room_url,
            token="",
            bot_name="Bot Name",
            params=DailyParams(audio_out_enabled=True)
        )
        tts_config_data = self.pipeline_config.get("tts", {})
        stt_config_data = self.pipeline_config.get("stt", {})
        llm_config_data = self.pipeline_config.get("llm", {})
        pipeline_config = self.pipeline_config.get("pipeline", {})

        tts = AHElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            voice_id=tts_config_data.get("voice_id", ""),
            model=tts_config_data.get("model", ""),
            params=ElevenLabsTTSService.InputParams(**tts_config_data.get("input_params", {})),
        )
        logger.info(f'STT config {stt_config_data}')
        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_AUTH_TOKEN", ""), 
                                                    live_options=LiveOptions(**stt_config_data.get("live_options", {})))
        logger.info(f'LLM config {llm_config_data}')
        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), 
                                                    model=llm_config_data.get("model", ""), 
                                                    params=BaseOpenAILLMService.InputParams(**llm_config_data.get("input_params", {})))

        content = self.script.format_map(self.DictWithMissing(self.variables))
        messages = [
            {
                "role": "system",
                "content": content,
            },
        ]
        stt._muted = True
        stt_mute_processor = STTMuteFilter(
            stt_service=stt,
            config=STTMuteConfig(
                strategies={STTMuteStrategy.FUNCTION_CALL, STTMuteStrategy.FIRST_SPEECH}
            ),
        )
        dynamic_vad_threshold_processor = DynamicVADThresholdProcessor(vad_analyzer=vad_analyzer)

        context = self.setup_pipeline_context(messages)
        context_aggregator = llm.create_context_aggregator(context)
        
        self.pipeline = Pipeline(
            [
                transport.input(),
                stt_mute_processor,
                stt,
                context_aggregator.user(),
                llm,
                tts,
                transport.output(),
                dynamic_vad_threshold_processor,
                context_aggregator.assistant(),
            ]
        )

        self.task = PipelineTask(self.pipeline,
                                PipelineParams(allow_interruptions=pipeline_config.get('allow_interruptions', False),
                                                enable_metrics=pipeline_config.get('enable_metrics', False)))

    async def run(self):
        runner = PipelineRunner()
        await runner.run(self.task)

