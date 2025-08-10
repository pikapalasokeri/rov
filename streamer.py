#!/usr/bin/env python3

# This flask server thing is based on this excellent piece of code:
# https://github.com/Mjrovai/Video-Streaming-with-Flask/tree/master/camWebServer

import io

from flask import Flask, render_template, Response, send_file

from camera import Camera
import framerate

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def gen_video(camera):
    while True:
        framerate.sleep()
        frame = camera.get_video_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


def get_image(camera):
    frame = camera.get_image_frame()
    return frame


@app.route("/video")
def video():
    return Response(
        gen_video(Camera()), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/image")
def image():
    return send_file(io.BytesIO(get_image(Camera())), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)
