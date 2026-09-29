from typing import Any, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class ClaimGuardException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_dict())


class UnsupportedFileTypeError(ClaimGuardException):
    def __init__(self, message: str = "Only JPG, PNG, WebP and PDF files are supported.", details: Optional[dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="UNSUPPORTED_FILE_TYPE",
            message=message,
            details=details,
        )


class FileTooLargeError(ClaimGuardException):
    def __init__(self, message: str = "File exceeds maximum upload size limit.", details: Optional[dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message=message,
            details=details,
        )


class TooManyPagesError(ClaimGuardException):
    def __init__(self, message: str = "PDF exceeds maximum allowed page count.", details: Optional[dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="TOO_MANY_PAGES",
            message=message,
            details=details,
        )


class CorruptFileError(ClaimGuardException):
    def __init__(self, message: str = "File cannot be opened or decoded.", details: Optional[dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="CORRUPT_FILE",
            message=message,
            details=details,
        )


class NoInputError(ClaimGuardException):
    def __init__(self, message: str = "At least one input file must be supplied.", details: Optional[dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="NO_INPUT",
            message=message,
            details=details,
        )


class JobNotFoundError(ClaimGuardException):
    def __init__(self, job_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="JOB_NOT_FOUND",
            message=f"Job '{job_id}' not found.",
            details={"job_id": job_id},
        )


class ResultNotFoundError(ClaimGuardException):
    def __init__(self, result_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESULT_NOT_FOUND",
            message=f"Result '{result_id}' not found.",
            details={"result_id": result_id},
        )
