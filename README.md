# gphoto-threading

This python script allows you to provide v4l2loopback with frames from a DSLR.
Unlike other options this script allows you to send commands to your camera while capturing preview frames.
This let's you for example adjust the ISO and control focus.

## Windows
For windows to work you have to install libgphoto2 using msys2.
Then replace the driver with Win-USB using [https://zadig.akeo.ie/](Zadig)
(I have tested this with my D5600 and without it you won't be able to access the camera.)

## mpv playback
To play with mpv `--demuxer-lavf-probescore=10` must be used since the stream has no timestamps.
For low latency add `--no-cache --untimed --no-demuxer-thread --vd-lavc-threads=1`

