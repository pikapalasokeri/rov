#!/usr/bin/env python3

from threading import Thread

import cv2

import framerate


class LaptopCamera:
    # The idea is that this class has roughly the same interface and functionality as picamera in
    # order to make it easy to prototype and debug without the real raspi hardware.

    def __enter__(self):
        self.resolution = (320, 320)
        self.hflip = False
        self.vflip = False

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

    def start_preview(self):
        pass

    def capture(
        self,
        stream,
        format,
        use_video_port=False,
        resize=None,
        splitter_port=0,
        quality=None,
    ):
        rval, frame = self._vc.read()
        frame = cv2.resize(frame, resize)
        encoded_frame = cv2.imencode(f".{format}", frame)[1]
        stream.write(encoded_frame.tobytes())
        print("capture() encoded frame shape:", encoded_frame.shape)

    def start_recording(
        self, stream, format, use_video_port=True, resize=None, splitter_port=0
    ):
        new_format = format
        if "jpeg" in new_format:
            new_format = "jpeg"

        self._thread = Thread(
            target=self._recording_thread,
            kwargs={
                "stream": stream,
                "format": new_format,
                "resize": resize,
            },
        )
        self._thread.start()

    def capture_continuous(
        self,
        stream,
        format,
        use_video_port=False,
        resize=None,
        splitter_port=0,
    ):
        resolution = self.resolution
        if resize is not None:
            resolution = resize

        while self._rval:
            rval, frame = self._vc.read()
            frame = cv2.resize(frame, resolution)
            encoded_frame = cv2.imencode(f".{format}", frame)[1]

            print("capture_continuous() encoded frame shape:", encoded_frame.shape)

            stream.write(encoded_frame.tobytes())
            yield None

    def _recording_thread(self, stream, format, resize):
        for foo in self.capture_continuous(stream, format, resize=resize):
            framerate.sleep()

