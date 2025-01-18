from pipecat.frames.frames import TextFrame
from pipecat.services.elevenlabs import ElevenLabsTTSService

import re

ENDOFSENTENCE_PATTERN_STR = r"""
    (?<![A-Z])       # Negative lookbehind: not preceded by an uppercase letter (e.g., "U.S.A.")
    (?<!\d)          # Negative lookbehind: not preceded by a digit (e.g., "1. Let's start")
    (?<!\d\s[ap])    # Negative lookbehind: not preceded by time (e.g., "3:00 a.m.")
    (?<!Mr|Ms|Dr)    # Negative lookbehind: not preceded by Mr, Ms, Dr (combined bc. length is the same)
    (?<!Mrs)         # Negative lookbehind: not preceded by "Mrs"
    (?<!Prof)        # Negative lookbehind: not preceded by "Prof"
    [\.\?\!:;।]|    # Match a period, question mark, exclamation point, colon, semicolon, or Hindi danda
    [。？！：；|]      # the full-width version (mainly used in East Asian languages such as Chinese) and Hindi danda
    $                # End of string
"""
ENDOFSENTENCE_PATTERN = re.compile(ENDOFSENTENCE_PATTERN_STR, re.VERBOSE)


def match_endofsentence(text: str) -> int:
    match = ENDOFSENTENCE_PATTERN.search(text.rstrip())
    return match.end() if match else 0


class AHElevenLabsTTSService(ElevenLabsTTSService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _process_text_frame(self, frame: TextFrame):
        text: str | None = None
        if not self._aggregate_sentences:
            text = frame.text
        else:
            self._current_sentence += frame.text
            eos_end_marker = match_endofsentence(self._current_sentence)
            if eos_end_marker:
                text = self._current_sentence[:eos_end_marker]
                self._current_sentence = self._current_sentence[eos_end_marker:]
        if text:
            await self._push_tts_frames(text)
