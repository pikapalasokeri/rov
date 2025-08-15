import time
import io
from threading import Condition, Thread


class StreamingOutput(io.BufferedIOBase):
    # From https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py

    def __init__(self):
        self.frame = None
        self.frame_ready_cv = Condition()

    def write(self, buf):
        with self.frame_ready_cv:
            self.frame = buf
            self.frame_ready_cv.notify_all()

    def get(self):
        with self.frame_ready_cv:
            self.frame_ready_cv.wait()
            return self.frame


def _get_camera_interface():
    try:
        from picamera2_wrapper import ReasonablePicameraWrapper

        return ReasonablePicameraWrapper()

    except ModuleNotFoundError as e:
        from laptop_camera import LaptopCamera

        return LaptopCamera()


class Camera(object):
    thread = None
    video_stream = StreamingOutput()
    image_frame = None
    image_requested_cv = Condition()
    image_ready_cv = Condition()

    def __init__(self):
        self._resolution_video = (320, 240)
        self._resolution_image = (1024, 768)

    def initialize(self):
        if Camera.thread is None:
            Camera.thread = Thread(
                target=self._thread,
                kwargs={
                    "resolution_video": self._resolution_video,
                    "resolution_image": self._resolution_image,
                },
            )
            Camera.thread.start()

    def get_video_frame(self):
        self.initialize()
        return self.video_stream.get()

    def get_image_frame(self):
        self.initialize()
        with self.image_ready_cv:
            with self.image_requested_cv:
                self.image_requested_cv.notify_all()
            self.image_ready_cv.wait()

        return self.image_frame

    @classmethod
    def _thread(cls, resolution_video, resolution_image):
        with _get_camera_interface() as camera:
            camera.start_recording(cls.video_stream)

            while True:
                with cls.image_requested_cv:
                    cls.image_requested_cv.wait()

                    image_stream = io.BytesIO()
                    camera.capture_file(
                        image_stream,
                        format="jpeg",
                    )

                    with cls.image_ready_cv:
                        cls.image_frame = image_stream.getvalue()
                        cls.image_ready_cv.notify_all()

        cls.thread = None
