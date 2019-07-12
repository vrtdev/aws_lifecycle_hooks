import botocore.exceptions


class VolumeInUseError(botocore.exceptions.ClientError):
    def __init__(self, client_error: botocore.exceptions.ClientError):
        super().__init__(
            operation_name=client_error.operation_name,
            error_response=client_error.response,
        )


class ParsingError(Exception):
    pass
