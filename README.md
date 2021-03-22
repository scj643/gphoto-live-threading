# gphoto-threading

This python script allows you to provide v4l2loopback, or other applications, with frames from a DSLR.
Unlike other options, this script allows you to send commands to your camera while capturing preview frames.
This lets you, for example, adjust the ISO and control focus.

## Windows

For windows to work you have to install libgphoto2 using msys2.
Then replace the driver with Win-USB using [Zadig](https://zadig.akeo.ie/)
(I have tested this with my D5600 and without it, you won't be able to access the camera.)

## mpv playback

To play with mpv `--demuxer-lavf-probescore=10` must be used since the stream has no timestamps.
For low latency add `--no-cache --untimed --demuxer-thread=no --vd-lavc-threads=1 --no-audio`

`--demuxer-thread=no` must be used otherwise mpv will be buffering a lot, and the output will be choppy. 

This can use a lot of CPU without hardware decoding.
On my i7 9700k on Windows 10, it hits 25% utilization sometimes.

Example

```
mpv --no-cache --untimed --no-demuxer-thread --vd-lavc-threads=1 --demuxer-lavf-probescore=10 --no-border --no-audio udp://127.0.0.1:8833
```

### Hardware Decoding
For mpv to do hardware decoding add `--hwdec-codecs=mjpeg`
This may or may not cause issues for you.
On my i7 9700k on Windows 10 with an RTX 2080 SUPER it significantly reduces CPU usage with little noticeable latency.