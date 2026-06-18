# SpinToro

SpinToro is a Python recreation of the classic rotating ASCII donut, extended with a video export pipeline so the animation can be rendered as a high-resolution wallpaper-ready MP4.

## What the repository does

The project contains two execution modes:

- `console.py` reproduces the original terminal version of the donut and prints the animation directly to the console.
- `main.py` renders the same mathematical donut into 1080p frames using Pillow and exports the result as `donut_3d_1080p.mp4`.

The core torus math is intentionally preserved. The `xyz`, `xyprime`, and `L` functions still define the 3D position, 2D projection, and lighting response, and the internal Z-buffer logic still decides which ASCII character reaches the screen for each frame.

## How it works

At a high level, the animation is built in four stages:

1. The torus is sampled in two angles, `theta` and `phi`.
2. Each sample point is rotated with the global angles `A` and `B`.
3. The point is projected to 2D and compared against a Z-buffer so only the closest sample remains visible.
4. The visible samples are rendered as ASCII characters.

In `main.py`, that same ASCII buffer is drawn onto a black 1920x1080 image using a monospaced font and then encoded into an MP4 video. This makes the output suitable for use as a live wallpaper source or any other looping background workflow.

## Files

- `main.py`: video export pipeline.
- `console.py`: original console animation.
- `.gitignore`: repository ignore rules, including generated MP4 files.
- `LICENSE`: project license.
- `CODE_OF_CONDUCT.md`: community behavior policy.
- `CONTRIBUTING.md`: contribution workflow.
- `SECURITY.md`: vulnerability reporting guidance.

## Requirements

The video exporter uses:

- Python 3.12+
- Pillow
- NumPy
- OpenCV or imageio fallback
- progressbar2

The console version only requires Python’s standard library.

## Installation

Create and activate a virtual environment if you do not already have one, then install the dependencies used by the video exporter:

```bash
pip install pillow numpy opencv-python imageio imageio-ffmpeg progressbar2
```

## Usage

### Console mode

Run the original terminal animation:

```bash
python console.py
```

### Video mode

Run the main exporter to generate the MP4:

```bash
python main.py
```

Running `main.py` is what creates the final video file. The script renders the animation frame by frame and writes the MP4 to disk automatically.

## Output

By default, the exporter writes:

- `donut_3d_1080p.mp4`

If that file is locked by another process, the script automatically falls back to a numbered filename such as `donut_3d_1080p_1.mp4`.

## Performance and visual tuning

The renderer is configured for a smooth 60 FPS output while keeping the animation visually slower than the original terminal version. That separation between rotation speed and output FPS makes the video cleaner for wallpaper use.

You can tune the feel of the animation through these values in `main.py`:

- `velocidad_rotacion`: reduces or increases the angular speed.
- `fps`: controls the playback frame rate.
- `wide` and `high`: control the logical ASCII buffer density.
- `K1`: controls the apparent size of the donut inside the frame.

## Repository policy

Generated media files are ignored by design so the repository stays lightweight. Commit the source code, documentation, and license files, but not exported videos.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for the full text.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Security

Security issues should be reported privately according to [SECURITY.md](SECURITY.md).

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
