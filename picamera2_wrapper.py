#!/usr/bin/env python3

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput


class ReasonablePicameraWrapper:
    def __enter__(self):
        self._camera = Picamera2()
        half_resolution = [dim // 2 for dim in self._camera.sensor_resolution]
        main_stream = {"size": half_resolution}
        lores_stream = {"size": (640, 480)}
        video_config = self._camera.create_video_configuration(
            main_stream, lores_stream, encode="lores"
        )
        self._camera.configure(video_config)
        self._encoder = MJPEGEncoder()

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self._camera.stop_recording()

    def capture_file(
        self,
        stream,
        format,
    ):
        request = self._camera.capture_request()
        request.save(name="main", file_output=stream, format=format)
        request.release()

    def start_recording(self, stream):
        self._camera.start_recording(self._encoder, FileOutput(stream))
