import ctypes
import io
import math



def decode (raw):
    if not isinstance(raw, io.BytesIO):
        raw = io.BytesIO(raw)

    def _decode (): return handlers[raw.read(1)[0]]()

    handlers = {
        b"\0"[0]: lambda: None,
        b"0"[0]:  lambda: 0,
        b"+"[0]:  lambda: int.from_bytes(raw.read(4), "little"),
        b"-"[0]:  lambda: -int.from_bytes(raw.read(4), "little"),
        b">"[0]:  lambda: int.from_bytes(raw.read(8), "little"),
        b"<"[0]:  lambda: -int.from_bytes(raw.read(8), "little"),
        b"P"[0]:  lambda: int.from_bytes(raw.read(_decode()), "little"),
        b"p"[0]:  lambda: -int.from_bytes(raw.read(_decode()), "little"),
        b"."[0]:  lambda: ctypes.c_double.from_buffer_copy(raw.read(8)).value,
        b"'"[0]:  lambda: raw.read(_decode()),
        b'"'[0]:  lambda: raw.read(_decode()).decode("utf8"),
        b"("[0]:  lambda: tuple(_decode() for _ in range(_decode())),
        b"["[0]:  lambda: [_decode() for _ in range(_decode())],
        b"{"[0]:  lambda: dict((_decode(), _decode()) for _ in range(_decode()))
    }

    return _decode()



def encode (obj, stream = None):
    _stream = stream or io.BytesIO()

    if obj == None:
        _stream.write(b"\0")

    elif isinstance(obj, int):
        if obj == 0:
            _stream.write(b"0")
        else:
            if obj < 0:
                obj = -obj
                sign = True
            else:
                sign = False

            if obj <= 0xFFFFFFFF:
                _stream.write(b"-" if sign else b"+")
                _stream.write(obj.to_bytes(4, "little"))
            elif obj <= 0xFFFFFFFF_FFFFFFFF:
                _stream.write(b"<" if sign else b">")
                _stream.write(obj.to_bytes(8, "little"))
            else:
                byte_len = int(math.log2(obj)) // 8 + 1

                _stream.write(b"p" if sign else b"P")
                encode(byte_len, _stream)
                _stream.write(obj.to_bytes(byte_len, "little"))

    elif isinstance(obj, float):
        _stream.write(b".")
        _stream.write(bytes(ctypes.c_double(obj)))

    elif isinstance(obj, bytes):
        _stream.write(b"'")
        encode(len(obj), _stream)
        _stream.write(obj)

    elif isinstance(obj, str):
        obj = obj.encode("utf8")
        _stream.write(b'"')
        encode(len(obj), _stream)
        _stream.write(obj)

    elif isinstance(obj, tuple):
        _stream.write(b"(")
        encode(len(obj), _stream)
        for entry in obj: encode(entry, _stream)

    elif isinstance(obj, list):
        _stream.write(b"[")
        encode(len(obj), _stream)
        for entry in obj: encode(entry, _stream)

    elif isinstance(obj, dict):
        _stream.write(b"{")
        encode(len(obj), _stream)

        for key, value in obj.items():
            encode(key, _stream)
            encode(value, _stream)

    if stream == None:
        return _stream.getvalue()