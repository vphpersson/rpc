from enum import IntFlag


class PfcFlag(IntFlag):
    PFC_FIRST_FRAG = 0x01
    PFC_LAST_FRAG = 0x02
    PFC_PENDING_CANCEL = 0x04
    PFC_RESERVED_1 = 0x08
    PFC_CONC_MPX = 0x10
    PFC_DID_NOT_EXECUTE = 0x20
    PFC_MAYBE = 0x40
    PFC_OBJECT_UUID = 0x80
