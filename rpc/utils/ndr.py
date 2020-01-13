def calculate_pad_length(length_unpadded: int, multiple: int = 4) -> int:
    return length_unpadded + (-length_unpadded % multiple)


def pad(data: bytes, multiple: int = 4, fillchar: bytes = b'\x00') -> bytes:
    return data.ljust(calculate_pad_length(length_unpadded=len(data), multiple=multiple), fillchar)
