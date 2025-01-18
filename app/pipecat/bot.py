import os
import sys

from dotenv import load_dotenv
from loguru import logger
from openai.types.chat import ChatCompletionToolParam
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame, LLMMessagesFrame, TextFrame, TranscriptionFrame, InterimTranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.filters.stt_mute_filter import STTMuteConfig, STTMuteFilter, STTMuteStrategy
from pipecat.processors.user_idle_processor import UserIdleProcessor
from pipecat.services.deepgram import (
    DeepgramSTTService,
    LiveOptions,
)
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.openai import OpenAILLMService, BaseOpenAILLMService


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

    def setup_pipeline_context(self, messages, api_tools):
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
            room_url=...,
            token="", # leave empty. Note: token is _not_ your api key
            bot_name="Bot Name",
            params=DailyParams(audio_out_enabled=True)
        )
        tts_config_data = self.pipeline_config.get("tts", {})
        stt_config_data = self.pipeline_config.get("stt", {})
        llm_config_data = self.pipeline_config.get("llm", {})
        pipeline_config = self.pipeline_config.get("pipeline", {})
        api_tools = self.pipeline_config.get("api_tools", {})
        agent_welcome_message_template = self.pipeline_config.get("agent_welcome_message_template", "Hello am i speaking with {customer_name}?")
        agent_welcome_message = agent_welcome_message_template.format_map(self.DictWithMissing(self.variables))

        logger.info(f'TTS config {tts_config_data}')
        tts = AHElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            voice_id=tts_config_data.get("voice_id", ""),
            model=tts_config_data.get("model", ""),
            params=ElevenLabsTTSService.InputParams(**tts_config_data.get("input_params", {})),
        )
        logger.info(f'STT config {stt_config_data}')
        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_AUTH_TOKEN"),
                                 live_options=LiveOptions(**stt_config_data.get("live_options", {})))
        logger.info(f'LLM config {llm_config_data}')
        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model=llm_config_data.get("model", ""),
                               params=BaseOpenAILLMService.InputParams(**llm_config_data.get("input_params", {})))

        def function_callback_creator():
            async def function_callback(function_name, tool_call_id, args, llm, context, result_callback):
                """
                Function callback called for every function call
                :param function_name: Name of the function being invoked.
                :param tool_call_id: Unique identifier for the tool call.
                :param args: Arguments passed to the function.
                :param llm: The LLM service instance.
                :param context: Context of the current pipeline execution.
                :param result_callback: Callback to return the fetched result.
                """
                if function_name == "transfer_call":
                    self.is_transferred = True
                    await execute_transfer_call(self.pipeline_config.get("context", {}), self.stream_sid,
                                                result_callback)
                elif function_name in ["send_payment_link", "send_renewal_notice"]:
                    await handle_api_tools(self.pipeline_config, function_name, args, result_callback)

            return function_callback

        llm.register_function(None, function_callback_creator(), function_call_start_callback)
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
        voicemail_word_processor = WordBasedDisconnectProcessor(
            callback=lambda text: (
                    "voicemail" in text.lower().replace(" ", "") or
                    "voice mail" in text.lower()
            ),
            accumulator_frame=TranscriptionFrame,
        )

        # disconnect if the bot says goodbye
        good_bye_word_processor = WordBasedDisconnectProcessor(
            callback=lambda text: (
                    "goodbye" in text.lower().replace(" ", "") or
                    "good bye" in text.lower()
            ),
            accumulator_frame=TextFrame,
        )
        dynamic_vad_threshold_processor = DynamicVADThresholdProcessor(vad_analyzer=vad_analyzer)

        async def user_idle_callback(processor: UserIdleProcessor):
            logger.info("User idle callback")
            if self.is_transferred:
                logger.info("Transfer call made, skipping user idle callback")
                return
            event_logger = get_event_logger()
            event_logger.info(Event(
                event_type=EventType.USER_IDLE_DETECTED,
                call_id=self.call_id,
                domain=self.domain,
                agent_id=self.agent_id,
                event_data_num=processor._timeout
            ))
            check_user_online_message = self.pipeline_config["check_user_online_message"]
            messages.append(
                {
                    "role": "system",
                    "content": f"ask '{check_user_online_message}'",
                }
            )
            await processor.push_frame(LLMMessagesFrame(messages))

        check_user_online_message_after = self.pipeline_config["trigger_user_online_message_after"]

        user_idle_processor = UserIdleProcessor(callback=user_idle_callback, timeout=check_user_online_message_after)

        context = self.setup_pipeline_context(messages, api_tools)
        context_aggregator = llm.create_context_aggregator(context)

        conversation_history_tracker = ConversationHistoryTracker(
            call_id=self.call_id,
            domain=self.domain,
            agent_id=self.agent_id,
            conversation_history=self.conversation_history,
            context_aggregator=context_aggregator,
        )
        self.pipeline = Pipeline(
            [
                transport.input(),
                stt_mute_processor,
                stt,
                EventLoggerProcessor(call_id=self.call_id, domain=self.domain, agent_id=self.agent_id,
                                     frame_filters=[TranscriptionFrame, InterimTranscriptionFrame]),
                voicemail_word_processor,
                conversation_history_tracker,
                user_idle_processor,
                context_aggregator.user(),
                llm,
                EventLoggerProcessor(call_id=self.call_id, domain=self.domain, agent_id=self.agent_id,
                                     frame_filters=[TextFrame]),
                good_bye_word_processor,
                tts,
                transport.output(),
                dynamic_vad_threshold_processor,
                context_aggregator.assistant(),
                MetricPublisherProcessor(),
                EventLoggerProcessor(call_id=self.call_id, domain=self.domain, agent_id=self.agent_id)
            ]
        )

        self.task = PipelineTask(self.pipeline,
                                 PipelineParams(allow_interruptions=pipeline_config.get('allow_interruptions', False),
                                                enable_metrics=pipeline_config.get('enable_metrics', False)))
        good_bye_word_processor.set_pipeline_task(self.task)
        voicemail_word_processor.set_pipeline_task(self.task)

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, websocket):
            messages.append(
                {"role": "system", "content": f"Introduce yourself by saying this as it is: '{agent_welcome_message}'"})
            await self.task.queue_frames([LLMMessagesFrame(messages)])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, websocket):
            await self.task.queue_frame(EndFrame())

    async def run(self):
        runner = PipelineRunner()
        with logger.contextualize(call_id=self.call_id, domain=self.domain):
            logger.info("Running pipecat task now")
            await runner.run(self.task)

