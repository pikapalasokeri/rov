import time
import io
from threading import Condition, Thread


class StreamingOutput(object):
    # From https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming

    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.frame_ready_cv = Condition()

    def write(self, buf):
        if buf.startswith(b"\xff\xd8"):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.frame_ready_cv:
                self.frame = self.buffer.getvalue()
                self.frame_ready_cv.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

    def get(self):
        with self.frame_ready_cv:
            self.frame_ready_cv.wait()
            return self.buffer.getvalue()


def _get_camera_interface():
    try:
        from picamera import PiCamera

        return PiCamera()
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
            camera.resolution = resolution_image
            camera.hflip = False
            camera.vflip = False

            camera.start_recording(
                cls.video_stream, format="mjpeg", resize=resolution_video
            )

            while True:
                with cls.image_requested_cv:
                    cls.image_requested_cv.wait()

                    # Using capure() will cause frame drops on the video stream. This is ok since
                    # the video stream won't be viewed by the user anyway when looking
                    # at the high res image.
                    image_stream = io.BytesIO()
                    camera.capture(
                        image_stream,
                        resize=resolution_image,
                        format="jpeg",
                        quality=100,
                    )
                    with cls.image_ready_cv:
                        cls.image_frame = image_stream.getvalue()
                        cls.image_ready_cv.notify_all()

        cls.thread = None
