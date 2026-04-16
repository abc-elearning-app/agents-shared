from faster_whisper import WhisperModel
import sys

def transcribe(audio_path):
    model_size = "base"
    # Run on CPU for compatibility
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    full_text = ""
    for segment in segments:
        full_text += segment.text + " "
    
    print(full_text.strip())

if __name__ == "__main__":
    transcribe(sys.argv[1])
