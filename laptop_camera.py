#!/usr/bin/env python3

from threading import Thread

import cv2

import framerate


class LaptopCamera:
    # The idea is that this class has roughly the same interface and functionality as picamera in
    # order to make it easy to prototype and debug without the real raspi hardware.

    def __enter__(self):
        self._resolution_lowres = (320, 240)
        self._resolution_highres = (1024, 768)

        self._vc = cv2.VideoCapture(0)
        self._rval = False
        if self._vc.isOpened():
            self._rval, _ = self._vc.read()
        else:
            raise RuntimeError("Could not open VideoCapture.")
        self._thread = None
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self._vc.release()

    def capture_file(
        self,
        stream,
        format,
    ):
        rval, frame = self._vc.read()
        frame = cv2.resize(frame, self._resolution_highres)
        encoded_frame = cv2.imencode(f".{format}", frame)[1]
        stream.write(encoded_frame.tobytes())
        print("capture() encoded frame shape:", encoded_frame.shape)

    def start_recording(self, stream):
        self._thread = Thread(
            target=self._recording_thread,
            kwargs={
                "stream": stream,
                "format": "jpeg",
                "resolution": self._resolution_lowres,
            },
        )
        self._thread.start()

    def capture_continuous(self, stream, format, resolution):
        while self._rval:
            rval, frame = self._vc.read()
            frame = cv2.resize(frame, self._resolution_lowres)
            encoded_frame = cv2.imencode(f".{format}", frame)[1]

            print("capture_continuous() encoded frame shape:", encoded_frame.shape)

            stream.write(encoded_frame.tobytes())
            yield None

    def _recording_thread(self, stream, format, resolution):
        for foo in self.capture_continuous(stream, format, resolution):
            framerate.sleep()
