import loguru
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    StartInterruptionFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.audio.vad.vad_analyzer import VADAnalyzer, VADParams


class DynamicVADThresholdProcessor(FrameProcessor):
    def __init__(self, vad_analyzer: VADAnalyzer, **kwargs):
        super().__init__(**kwargs)
        self.logger = loguru.logger
        self.vad_analyzer = vad_analyzer

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
        if isinstance(frame, BotStartedSpeakingFrame):
            self.logger.info("bot started speaking, changing vad params")
            self.vad_analyzer.set_params(
                VADParams(
                    confidence=0.82,
                    start_secs=0.5,
                    stop_secs=0.7,
                    min_volume=0.7,
                )
            )
        elif isinstance(frame, BotStoppedSpeakingFrame) or isinstance(
            frame, StartInterruptionFrame
        ):
            self.logger.info("bot stopped speaking, changing vad params")
            self.vad_analyzer.set_params(
                VADParams(
                    confidence=0.35,
                    start_secs=0.2,
                    stop_secs=0.4,
                    min_volume=0.4,
                )
            )
