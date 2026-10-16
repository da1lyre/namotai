MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_VIDEO_DURATION_SEC = 7200

ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
ALLOWED_TEXT_EXT = {".txt", ".docx", ".pdf"}

MIN_TEXT_LENGTH = 100
MAX_TEXT_LENGTH = 200_000


class ValidationError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
