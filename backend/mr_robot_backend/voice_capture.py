"""Local turn detection over verified 64 ms USB microphone blocks."""
import array
from collections import deque
import math
import sys
import time

from .providers import ProviderError
from tools.voice_device import INPUT_BYTES


def capture_turn(device, wake, cancelled, stage, followup_until=None, immediate=False, pause_blocks=10):
    """Wait for activation, then return a bounded utterance after a speech pause."""
    followup = followup_until is not None
    if immediate:
        device.stream_start(False, immediate=True)
        stage("listening")
    elif followup:
        device.stream_start(False, followup=True)
        stage("waiting_for_followup")
    else:
        device.stream_start(wake is not None)
    if wake:
        wake.reset()
    wait_until = followup_until if followup else time.monotonic() + (600 if wake else 60)
    pre_roll = deque()
    audio = bytearray()
    noise = 8.
    speaking = quiet = samples_waited = 0
    triggered = False
    trigger_next = False
    success = False
    settling_blocks = 3 if followup else 0
    try:
        if not wake and not followup and not immediate:
            while time.monotonic() < wait_until and not cancelled():
                if device.request("status", timeout=2).get("phase") == "recording":
                    break
                time.sleep(.04)
            else:
                return None

        if wake:
            stage("waiting_for_wake")
        while not cancelled() and (triggered or time.monotonic() < wait_until):
            try:
                phase, block = device.sample(trigger=trigger_next)
            except ValueError as error:
                # A physical button press ends a follow-up at the board.
                if followup and str(error) == "voice_device_rejected":
                    if device.request("status", timeout=1).get("phase") == "idle":
                        return None
                raise
            trigger_next = False
            try:
                samples = array.array("h", block)
                if sys.byteorder != "little":
                    samples.byteswap()
                level = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
                if phase == "wake":
                    noise = .96 * noise + .04 * min(level, noise * 1.4)
                    pre_roll.append(bytearray(block))
                    if len(pre_roll) > 5:
                        old = pre_roll.popleft()
                        old[:] = b"\0" * len(old)
                    trigger_next = wake.accepts(samples)
                    continue
                if phase != "recording":
                    raise ValueError("voice_stream_phase")
                if settling_blocks:
                    # Let the speaker tail and microphone startup settle locally.
                    settling_blocks -= 1
                    continue
                threshold = max(18., min(72., 2.3 * noise))
                if followup and not triggered:
                    # Keep only rolling lead-in until roughly 190 ms of speech.
                    pre_roll.append(bytearray(block))
                    if len(pre_roll) > 5:
                        recent = pre_roll.popleft()
                        recent[:] = b"\0" * len(recent)
                    speaking = speaking + 1 if level >= threshold else 0
                    if speaking < 3:
                        continue
                    triggered = True
                    stage("listening")
                    for recent in pre_roll:
                        audio.extend(recent)
                    continue
                if not triggered:
                    triggered = True
                    stage("listening")
                    for recent in pre_roll:
                        audio.extend(recent)
                audio.extend(block)
                if level >= threshold:
                    speaking += 1
                    quiet = 0
                else:
                    quiet += 1
                samples_waited += len(samples)
                ended = speaking >= 3 and quiet >= (13 if followup else pause_blocks)
                if ended or len(audio) >= INPUT_BYTES:
                    end = device.confirm("finish", timeout=.5)
                    if end.get("phase") != "thinking":
                        raise ValueError("voice_capture_cleanup")
                    if speaking < 3:
                        return None
                    del audio[INPUT_BYTES:]
                    success = True
                    return audio
                if not speaking and samples_waited >= 48000:
                    return None
            finally:
                block[:] = b"\0" * len(block)
    finally:
        for recent in pre_roll:
            recent[:] = b"\0" * len(recent)
        if not success:
            audio[:] = b"\0" * len(audio)
    if cancelled():
        raise ProviderError("voice_cancelled")
    return None
