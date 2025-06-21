import json
import os
import logging
import subprocess
from vosk import Model, KaldiRecognizer
# from pydub import AudioSegment # pydub is not used, can be removed if truly not needed. For now, keeping it commented.

# Configure logging
logging.basicConfig(level=logging.INFO) # Consider configuring logging centrally
logger = logging.getLogger(__name__)

class SpeechToTextService:
    def __init__(self, model_path: str = "/usr/local/share/vosk/model"):
        # Check if model path exists, though in Docker it should be there
        if not os.path.exists(model_path):
            logger.warning(f"Vosk model path {model_path} does not exist. Transcription will fail.")
            # Depending on requirements, could raise an error or allow to proceed without a model
            self.model = None
            self.recognizer = None
            return

        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000) # 16kHz sample rate

    def _convert_to_wav(self, audio_path: str) -> str:
        """Converts audio to WAV format (16 kHz, mono, 16-bit PCM)."""
        if not self.model: # If model failed to load, cannot proceed
            raise Exception("Vosk model not loaded. Cannot convert audio.")

        logger.info(f"Starting conversion for file {audio_path}")
        
        wav_path = audio_path.replace(os.path.splitext(audio_path)[1], ".wav")
        cmd = [
            "ffmpeg", "-y",          # Overwrite existing files
            "-i", audio_path,
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "16000",          # 16 kHz
            "-ac", "1",              # mono
            wav_path
        ]
        
        try:
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"File successfully converted to {wav_path}")
            return wav_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during file conversion: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("ffmpeg command not found. Please ensure ffmpeg is installed and in PATH.")
            raise

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribes audio to text using Vosk."""
        if not self.model or not self.recognizer:
            logger.error("Vosk model or recognizer not initialized. Transcription aborted.")
            return "Error: Speech recognition service not available."

        try:
            wav_path = self._convert_to_wav(audio_path)
        except Exception as e:
            logger.error(f"Failed to convert audio to WAV: {e}")
            return "Error: Could not process audio file for transcription."

        result_parts = []
        logger.info("Starting speech recognition...")
        logger.info(f"Opening file: {wav_path}")
        
        if not os.path.exists(wav_path):
            logger.error(f"WAV file {wav_path} does not exist after conversion attempt.")
            return "Error: Processed audio file not found."

        try:
            with open(wav_path, "rb") as f:
                while True:
                    data = f.read(4000) # Read in chunks
                    if len(data) == 0:
                        break
                    if self.recognizer.AcceptWaveform(data):
                        part_result = json.loads(self.recognizer.Result())
                        text = part_result.get("text", "")
                        if text: # Append only if there's text
                            logger.info(f"Intermediate result: {text}")
                            result_parts.append(text)

            final_result_json = self.recognizer.FinalResult()
            final_result = json.loads(final_result_json)
            final_text = final_result.get("text", "")
            if final_text: # Append only if there's text
                logger.info(f"Final result: {final_text}")
                result_parts.append(final_text)
        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return "Error: Speech transcription failed."
        finally:
            # Clean up the temporary WAV file
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                    logger.info(f"Temporary WAV file {wav_path} removed.")
                except OSError as e:
                    logger.error(f"Error removing temporary WAV file {wav_path}: {e}")
        
        full_text = " ".join(filter(None, result_parts)).strip()
        logger.info(f"Transcription complete. Full text: {full_text}")
        return full_text

# Global instance for easy import, similar to gigachat_service
# Consider dependency injection for more complex applications
speech_to_text_service = SpeechToTextService() 