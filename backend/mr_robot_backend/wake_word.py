"""Local streaming recognition for one phrase on the USB host."""
from pathlib import Path

from .providers import ProviderError

PHRASE = "HEY_MR_ROBOT"
MODEL = Path(__file__).resolve().parents[2] / "private/wake-model"
PARTS = {
    "encoder": "encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx",
    "decoder": "decoder-epoch-13-avg-2-chunk-8-left-64.onnx",
    "joiner": "joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx",
    "tokens": "tokens.txt",
}
KEYWORD_LINE = "HH EY1 M IH1 S T ER0 R OW1 B AA2 T @HEY_MR_ROBOT\n"


class WakeWord:
    def __init__(self):
        try:
            import sherpa_onnx
        except ImportError:
            raise ProviderError("wake_model_setup_required") from None
        files = {key: str(MODEL / value) for key, value in PARTS.items()}
        keywords = MODEL / "keywords.txt"
        if not keywords.is_file() or any(not Path(path).is_file() for path in files.values()):
            raise ProviderError("wake_model_setup_required")
        self.spotter = sherpa_onnx.KeywordSpotter(
            **files, keywords_file=str(keywords), num_threads=1, keywords_threshold=.25
        )
        self.reset()

    def reset(self):
        self.stream = self.spotter.create_stream()

    def accepts(self, samples):
        self.stream.accept_waveform(16000, [max(-1., min(1., value / 2048.)) for value in samples])
        while self.spotter.is_ready(self.stream):
            self.spotter.decode_stream(self.stream)
            if self.spotter.get_result(self.stream) == PHRASE:
                return True
        return False
