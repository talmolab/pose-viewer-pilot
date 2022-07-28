import sleap_io
import asyncio
import pandas as pd
import h5py
import os
import io
import difflib
import json
import time
import math
from js import (
    document,
    test,
    setTimeout,
    console,
    Object,
    Uint8Array,
    Uint8ClampedArray,
    window,
    typeof,
    File,
    devicePixelRatio,
    ImageData,
    Uint8ClampedArray,
    CanvasRenderingContext2D as Context2d,
    requestAnimationFrame,
)
from pyodide import to_js, create_proxy
import numpy as np
from PIL import Image


current_frame = 0  # Current frame index displayed in canvas


def add_row(table, data):
    """Add a row to table and fill with given data."""
    rows = document.getElementById(table).rows.length
    table = document.getElementById(table)
    row = table.insertRow(-1)
    row.appendChild(document.createElement("th")).appendChild(
        document.createTextNode(rows)
    )
    for i in range(len(data)):
        cell = row.insertCell(-1)
        cell.innerText = data[i]


def load_skeleton(skeleton_list):
    """Display list of given skeletons."""
    skeleton = skeleton_list[0]  # Work with first skeleton in list TODO: multi-skeleton
    for node in skeleton.nodes:
        add_row("node", [node.name])
    for edge in skeleton.edges:
        add_row("edge", [edge.source.name, edge.destination.name])


def load_videos(video_list):
    """Display list of given videos."""
    if video.shape is not None:
        if video.backend is not None:
            for video in video_list:
                add_row(
                    "video",
                    [
                        video.filename,
                        video.shape[0],
                        video.shape[1],
                        video.shape[2],
                        video.shape[3],
                        video.backend,
                    ],
                )
        else:
            for video in video_list:
                add_row(
                    "video",
                    [
                        video.filename,
                        video.shape[0],
                        video.shape[1],
                        video.shape[2],
                        video.shape[3],
                    ],
                )
    else:
        if video.backend is not None:
            for video in video_list:
                add_row("video", [video.filename, "", "", "", "", video.backend])
        else:
            for video in video_list:
                add_row("video", [video.filename, "", "", "", "", ""])


def read_hdf5(filename, dataset="/"):
    """Read data from an HDF5 file."""
    data = {}

    def read_datasets(k, v):
        if type(v) == h5py.Dataset:
            data[v.name] = v[()]

    with h5py.File(filename, "r") as f:
        if type(f[dataset]) == h5py.Group:
            f.visititems(read_datasets)
        elif type(f[dataset]) == h5py.Dataset:
            data = f[dataset][()]
    return data


def read_frames(labels_path):
    """Read frames dataset in a SLEAP labels file."""
    frames = read_hdf5(labels_path, "frames")
    frames = pd.DataFrame(frames)
    frames.set_index("frame_id", inplace=True)
    return frames


def read_videos(labels_path):
    """Read videos dataset in a SLEAP labels file."""
    videos = [json.loads(x) for x in read_hdf5(labels_path, "videos_json")]
    return videos


def get_frame_image(labels_path, video_id, frame_idx):
    """Get image from video at given frame index."""

    # Load metadata.
    videos = read_videos(labels_path)
    # Look up dataset name for video data
    dset = videos[video_id]["backend"]["dataset"]

    # Get frame index metadata
    frame_numbers = read_hdf5(labels_path, dset.replace("/video", "/frame_numbers"))
    # frame_numbers = read_hdf5_dataset(labels_path, dset)
    frame_ind = frame_numbers.tolist().index(frame_idx)

    # Decode frame image bytes and create PIL image
    image_bytes = read_hdf5(labels_path, dset)
    image = Image.open(io.BytesIO(image_bytes[frame_ind]))
    image = image.convert("RGBA")  # Necessary to display properly w/ canvas

    return image


def create_frame_array(bytes):
    """Create array of frame images from bytes."""

    canvas = document.getElementById("disp")
    ctx = canvas.getContext("2d")

    frame_array = []
    images = []
    frames = read_frames(bytes)
    frames.sort_values(by=["video", "frame_idx"])

    for ind in frames.index:
        img = get_frame_image(bytes, frames["video"][ind], frames["frame_idx"][ind])
        images.append(img)
        data = Uint8ClampedArray.new(to_js(img.tobytes()))
        size = img.size
        imageData = ctx.createImageData(size[0], size[1])
        imageData.data.set(data)
        frame_array.append(imageData)

    return frame_array, images, frames


def seek_to_frame(e):
    """Seek to frame in array of frames."""
    global current_frame
    num = e.currentTarget.id
    size = e.currentTarget.size
    num = num.replace("seek_button", "")
    current_frame = int(num)
    console.log(num, size)
    draw_image(size, frame_array[int(num)])

    # Switch "active" class to corresponding button for current frame
    elems = document.querySelectorAll(".active")
    if len(elems) > 0:
        for elem in elems:
            elem.classList.remove("active")
    e.currentTarget.classList.add("active")
    console.log(current_frame)


def create_video_scrubber(size, frame_array):
    """Dynamically create video scrubber."""
    # Remove existing scrubber
    elems = document.querySelectorAll(".seekButton")
    if len(elems) > 0:
        for elem in elems:
            elem.remove()
    length = len(frame_array)
    width = 500 / length  # Many buttons -> Smaller width
    width = 5 if width < 5 else width  # Glitchy with widths < 5px
    width = math.ceil(width)
    buttons = []
    document.getElementById("scrubber").textContent = ""  # Clear Loading text

    # Create buttons and add id's & classes
    for i in range(length):
        scrubber = document.getElementById("scrubber")
        seek_button = document.createElement("button")
        seek_button.style.width = str(width) + "px"
        seek_button.setAttribute("id", f"seek_button{i}")
        seek_button.classList.add("seekButton")
        scrubber.appendChild(seek_button)
        buttons.append(seek_button)

    buttons[0].classList.add("active")  # Set first button to active

    # Add event handlers to buttons
    for button in buttons:
        seek_proxy = create_proxy(seek_to_frame)
        button.size = size
        button.addEventListener("click", seek_proxy)


def draw_image(size, image):
    """Draw image on canvas."""
    # Resize image so that width is 512px
    canvas = document.getElementById("disp")
    ctx = canvas.getContext("2d")
    cw = canvas.width
    ch = canvas.height
    tempCanvas = document.createElement("canvas")
    tctx = tempCanvas.getContext("2d")
    canvas.width = size[0]
    canvas.height = size[0]
    ctx.putImageData(image, 0, 0)
    pct = 512 / size[0]
    cw = canvas.width
    ch = canvas.height
    tempCanvas.width = cw
    tempCanvas.height = ch
    tctx.drawImage(canvas, 0, 0)
    canvas.width *= pct
    canvas.height *= pct
    ctx = canvas.getContext("2d")

    # Draw image
    ctx.drawImage(tempCanvas, 0, 0, cw, ch, 0, 0, cw * pct, ch * pct)


async def upload(e):
    console.log("Received Upload")
    # Get the first file from upload
    file_list = e.target.files
    first_item = file_list.item(0)
    await update(first_item)


async def update(first_item):
    """ "Display data from file."""
    load = document.getElementById("scrubber")
    load.textContent = "Loading..."
    # Get the data from the files arrayBuffer as an array of unsigned bytes
    array_buf = Uint8Array.new(await first_item.arrayBuffer())
    # BytesIO wants a bytes-like object, so convert to bytearray first
    bytes_list = bytearray(array_buf)
    bytes = io.BytesIO(bytes_list)
    l = sleap_io.load_slp(bytes)
    global frame_array
    frame_array, images, frames = create_frame_array(bytes)
    global size
    size = images[0].size
    draw_image(size, frame_array[0])
    create_video_scrubber(size, frame_array)


def setup_file_upload():
    # Create a Python proxy for the callback function
    upload_file = create_proxy(upload)
    # Set the listener to the callback
    document.getElementById("files").addEventListener("change", upload_file)


def feature_check():
    """Check if browser supports features."""
    if hasattr(window, "showOpenFilePicker"):
        console.log("showOpenFilePicker present")
    else:
        console.log("showOpenFilePicker is not present")
        # Do something here to let the user know or
        # fallback to the FileReader class


def setup_button():
    # Create a Python proxy for the callback function
    file_select_proxy = create_proxy(file_select_event)
    # Set the listener to the callback
    document.getElementById("file_select").addEventListener(
        "click", file_select_proxy, False
    )


def setup_arrows():
    # Create a Python proxy for the callback function
    arrow_proxy = create_proxy(arrow_event)
    # Set the listener to the callback
    document.body.addEventListener("keyup", arrow_proxy)


async def arrow_event(event):
    """Handle arrow keys."""
    global current_frame
    console.log("arrow")

    valid = False  # if the key is a valid arrow key
    if event.keyCode == 37 and current_frame > 0:
        current_frame -= 1
        draw_image(size, frame_array[current_frame])
        console.log("left")
        valid = True

    if event.keyCode == 39 and current_frame < len(frame_array) - 1:
        current_frame += 1
        draw_image(size, frame_array[current_frame])
        console.log("right")
        valid = True

    if valid:
        elems = document.querySelectorAll(".active")
        if len(elems) > 0:
            for elem in elems:
                elem.classList.remove("active")
        document.getElementById(f"seek_button{current_frame}").classList.add("active")


async def file_select_event(event):

    console.log("File Select Event")
    try:
        fileHandles = await window.showOpenFilePicker()

    except Exception as e:
        console.log("Exception: " + str(e))
        return
    file = await fileHandles[0].getFile()
    await update(file)


setup_file_upload()
setup_button()
setup_arrows()
test()

document.getElementById("loadingOverlay").style.display = "none"
# console.log(frame_array("clip.mp4"))
