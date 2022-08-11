from re import L
import pkg_resources
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
import numpy as np
from pyodide import to_js, create_proxy
from PIL import Image
from js import (
    document,
    test,
    create_node,
    create_edge,
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
    setHotSpot,
)

current_frame = 0  # Current frame index displayed in canvas
pkg = None


def element(elem):
    """Get element by id."""
    return document.getElementById(elem)


def clear(w=512, h=512):
    """Render gray canvas."""
    canvas = element("disp")
    ctx = canvas.getContext("2d")
    canvas.width = w
    canvas.height = h
    ctx.fillStyle = "#181818"
    ctx.fillRect(0, 0, w, h)


def feature_check():
    """Check if browser supports features."""
    if hasattr(window, "showOpenFilePicker"):
        console.log("showOpenFilePicker present")
    else:
        console.log("showOpenFilePicker is not present")
        # Do something here to let the user know or
        # fallback to the FileReader class


def add_row(table, data):
    """Add a row to table and fill with given data."""
    rows = element(table).rows.length
    table = element(table)
    row = table.insertRow(-1)
    row.appendChild(document.createElement("th")).appendChild(
        document.createTextNode(rows)
    )
    for i in range(len(data)):
        cell = row.insertCell(-1)
        cell.innerText = data[i]


def set_tables():
    """Fill tables with data from uploaded file."""
    def remove_rows(table_list):
        for table in table_list:
            table = element(table)
            while table.rows.length > 1:
                table.deleteRow(table.rows.length - 1)

    remove_rows(["instance", "node", "edge", "video"])

    global l_frames

    def add_instance(points="", track="", score="", skeleton=""):
        add_row("instance", [points, track, score, skeleton])

    for instance in l_frames[current_frame].instances:
        if isinstance(instance, sleap_io.PredictedInstance):
            print(instance)
            add_instance(
                len(instance.points),
                instance.track.name if hasattr(instance.track, "name") else "",
                instance.score,
                instance.skeleton.name,
            )
        elif isinstance(instance, sleap_io.Instance):
            add_row(
                "instance",
                [
                    len(instance.points),
                    instance.track.name if hasattr(instance.track, "name") else "",
                    "",
                    instance.skeleton.name,
                ],
            )

    video = l_frames[0].video

    # Truncate path
    vid_path = video.filename
    if len(vid_path) > 15:
        vid_path = vid_path[:15] + "..."
    add_row("video", [vid_path])

    for node in l_frames[current_frame].instances[0].points.keys():
        add_row("node", [node.name])
    for edge in l_frames[current_frame].instances[0].skeleton.edges:
        add_row("edge", [edge.source.name, edge.destination.name])


def write_nodes_edges(num):
    """Render nodes and edges for current frame on canvas."""
    element("num").innerText = str(fname) + " | " + str(num)
    if not pkg:
        clear()
    hotspots = []
    for instance_list in edge_array[int(num)]:
        for instance in instance_list:
            print(instance)
            create_edge(
                pct * instance[0][0],
                pct * instance[0][1],
                pct * instance[1][0],
                pct * instance[1][1],
            )
    for instance_list in point_array[int(num)]:
        for point_list in instance_list:
            for point in point_list:
                hotspots.append(
                    [pct * point_list[point][0], pct * point_list[point][1], point]
                )
                create_node(pct * point_list[point][0], pct * point_list[point][1])
    setHotSpot(to_js(hotspots))


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

    canvas = element("disp")
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

    if pkg:
        draw_image(size, frame_array[int(num)])
    else:
        clear()

    # Switch "active" class to corresponding button for current frame
    elems = document.querySelectorAll(".active")
    if len(elems) > 0:
        for elem in elems:
            elem.classList.remove("active")
    e.currentTarget.classList.add("active")

    write_nodes_edges(num)
    set_tables()


def create_video_scrubber(size, length):
    """Dynamically create video scrubber."""

    # Remove existing scrubber
    elems = document.querySelectorAll(".seekButton")
    if len(elems) > 0:
        for elem in elems:
            elem.remove()
    element("num").style.display = "block"
    width = 500 / length  # Many buttons -> Smaller width
    width = 5 if width < 5 else width  # Glitchy with widths < 5px
    width = math.ceil(width)
    buttons = []
    element("scrubber").textContent = ""  # Clear Loading text

    # Create buttons and add id's & classes
    for i in range(length):
        scrubber = element("scrubber")
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
    canvas = element("disp")
    ctx = canvas.getContext("2d")
    cw = canvas.width
    ch = canvas.height
    tempCanvas = document.createElement("canvas")
    tctx = tempCanvas.getContext("2d")
    canvas.width = size[0]
    canvas.height = size[1]
    ctx.putImageData(image, 0, 0)
    global pct
    pct = 512 / size[1]
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
    """Upload file event."""
    console.log("Received Upload")
    # Get the first file from upload
    file_list = e.target.files
    file = file_list.item(0)
    await update(file)


async def arrow_event(e):
    """Handle arrow keys."""
    global current_frame
    console.log("Key pressed")

    valid = False  # if the key is a valid arrow key
    if e.keyCode == 37:
        if current_frame == 0:
            current_frame = frame_num - 1
        else:
            current_frame -= 1
        console.log("left")
        valid = True

    if e.keyCode == 39:
        if current_frame == frame_num - 1:
            current_frame = 0
        else:
            current_frame += 1
        console.log("right")
        valid = True
    if pkg is not None and pkg and valid:
        draw_image(size, frame_array[current_frame])
    if valid:
        elems = document.querySelectorAll(".active")
        if len(elems) > 0:
            for elem in elems:
                elem.classList.remove("active")
        console.log(f"current_frame: {current_frame}")
        element(f"seek_button{current_frame}").classList.add("active")
        write_nodes_edges(current_frame)
        set_tables()
    console.log(f"current_frame: {current_frame}")


async def file_select_event(e):
    """Handle file selection."""
    console.log("File Select Event")
    try:
        fileHandles = await window.showOpenFilePicker()

    except Exception as e:
        console.log("Exception: " + str(e))
        return
    file = await fileHandles[0].getFile()
    await update(file)


async def update(file):
    """Display data from file."""
    element("scrubber").style.display = "block"
    load = element("scrubber")
    load.textContent = "Loading..."
    global fname
    fname = file.name
    name = fname.replace(" ", ".").split(".")
    print(name)
    if name[-1] != "slp":
        load.textContent = "Invalid File Type"
        return
    global pkg
    pkg = True if "pkg" in name and name[-1] == "slp" else False
    if not pkg:
        clear()
    # Get the data from the files arrayBuffer as an array of unsigned bytes
    array_buf = Uint8Array.new(await file.arrayBuffer())
    # BytesIO wants a bytes-like object, so convert to bytearray first
    bytes_list = bytearray(array_buf)
    bytes = io.BytesIO(bytes_list)
    l = sleap_io.load_slp(bytes)

    global frame_array
    frame_array = []
    global size
    if pkg:
        frame_array, images, frames = create_frame_array(bytes)
        size = images[0].size

    global current_frame
    current_frame = 0

    setup_nodes_edges(l)
    if pkg:
        draw_image(size, frame_array[0])
    else:
        global pct
        pct = 0.5
    write_nodes_edges(0)
    set_tables()

    global frame_num
    frame_num = len(frame_array) if pkg else len(l.labeled_frames)
    create_video_scrubber(size, frame_num) if pkg else create_video_scrubber(
        (512, 512), frame_num
    )


async def export_nwb(e):
    """Convert and export NWB file."""
    console.log("Exporting NWB...")


def setup_nodes_edges(l):
    """Setup nodes and edges arrays."""
    global l_frames
    l_frames = l.labeled_frames
    global point_array
    global edge_array
    point_array = []
    edge_array = []
    for frame in l_frames:
        frame_points = []
        frame_edges = []
        for instance in frame.instances:
            instance_points = []
            instance_edges = []
            node_points = {}
            for node, point in instance.points.items():
                instance_points.append({node.name: (point.x, point.y)})
                node_points[node.name] = (point.x, point.y)
            for edge in instance.skeleton.edges:
                instance_edges.append(
                    (node_points[edge.source.name], node_points[edge.destination.name])
                )
            frame_points.append(instance_points)
            frame_edges.append(instance_edges)
        point_array.append(frame_points)
        edge_array.append(frame_edges)


def setup_file_upload():
    # Create a Python proxy for the callback function
    upload_file = create_proxy(upload)
    # Set the listener to the callback
    element("files").addEventListener("change", upload_file)


def setup_button():
    # Create a Python proxy for the callback function
    file_select_proxy = create_proxy(file_select_event)
    # Set the listener to the callback
    element("file_select").addEventListener("click", file_select_proxy, False)


def setup_arrows():
    # Create a Python proxy for the callback function
    arrow_proxy = create_proxy(arrow_event)
    # Set the listener to the callback
    document.body.addEventListener("keydown", arrow_proxy)


def setup_nwb_export():
    # Create a Python proxy for the callback function
    nwb_proxy = create_proxy(export_nwb)
    # Set the listener to the callback
    element("export_nwb").addEventListener("click", nwb_proxy)


setup_file_upload()
setup_button()
setup_arrows()
setup_nwb_export()
test()
clear()

# Remove loading screen
element("loadingOverlay").style.display = "none"
