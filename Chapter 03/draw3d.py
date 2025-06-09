# draw3d.py
# -----------
from math import sqrt, pi
import matplotlib
import os
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D, proj3d   # proj3d might still be needed for other stuff
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from colors import *  # your blue, red, etc.

###
### We will no longer use FancyArrowPatch for 3D arrows. Instead, we use ax.quiver().
###

class Polygon3D():
    def __init__(self, *vertices, color=blue):
        self.vertices = vertices
        self.color = color

class Points3D():
    def __init__(self, *vectors, color=black):
        self.vectors = list(vectors)
        self.color = color

class Arrow3D():
    """
    tip = (x_t, y_t, z_t)
    tail = (x_0, y_0, z_0)    # default tail is origin if not specified
    color: any Matplotlib color
    """
    def __init__(self, tip, tail=(0, 0, 0), color=red):
        self.tip = tip
        self.tail = tail
        self.color = color

class Segment3D():
    def __init__(self, start_point, end_point, color=blue, linestyle='solid'):
        self.start_point = start_point
        self.end_point = end_point
        self.color = color
        self.linestyle = linestyle

class Box3D():
    """
    A Box from (0,0,0) to the given (x,y,z) with dashed gray edges.
    Pass Box3D(x, y, z).
    """
    def __init__(self, *vector):
        # If someone calls Box3D(x, y, z), vector will be the tuple (x, y, z).
        self.vector = vector

# helper to gather all points from objects
def extract_vectors_3D(objects):
    for obj in objects:
        if isinstance(obj, Polygon3D):
            for v in obj.vertices:
                yield v
        elif isinstance(obj, Points3D):
            for v in obj.vectors:
                yield v
        elif isinstance(obj, Arrow3D):
            yield obj.tip
            yield obj.tail
        elif isinstance(obj, Segment3D):
            yield obj.start_point
            yield obj.end_point
        elif isinstance(obj, Box3D):
            # if user passed Box3D(x, y, z), then obj.vector == (x,y,z)
            # yield that triple so we can set limits
            yield obj.vector
        else:
            raise TypeError(f"Unrecognized object: {obj}")

def draw3d(*objects,
           origin=True,
           axes=True,
           width=6,
           save_as=None,
           azim=None,
           elev=None,
           xlim=None,
           ylim=None,
           zlim=None,
           xticks=None,
           yticks=None,
           zticks=None,
           depthshade=False):
    """
    Draw a collection of 3D objects (Points3D, Polygon3D, Arrow3D, Segment3D, Box3D).
     - origin: if True, plot a black 'x' at (0,0,0)
     - axes: if True, draw x‐, y‐, z‐axes lines from the computed bounding box (or default ±2)
     - width: size of the figure in inches (we use a square figure here)
     - save_as: if not None, save figure to this filename
     - azim, elev: optional view angles to pass to ax.view_init()
     - xlim, ylim, zlim: if given (tuples), enforce those axis ranges
     - xticks, yticks, zticks: if given (lists), set tick marks
     - depthshade: passed to ax.scatter(...) for Points3D
    """

    # 1) Always start with a fresh figure
    fig = plt.figure(figsize=(width, width))
    ax = fig.add_subplot(111, projection='3d')

    # 2) Optionally set the camera/view angles
    if (azim is not None) or (elev is not None):
        ax.view_init(elev=elev, azim=azim)

    # 3) Collect all vectors (including “(0,0,0)” if origin=True, to ensure we at least have the origin inside the box)
    all_vectors = list(extract_vectors_3D(objects))
    if origin:
        all_vectors.append((0.0, 0.0, 0.0))

    xs, ys, zs = zip(*all_vectors)

    # 4) Compute min/max (including 0)
    max_x, min_x = max(0, *xs), min(0, *xs)
    max_y, min_y = max(0, *ys), min(0, *ys)
    max_z, min_z = max(0, *zs), min(0, *zs)

    x_size = max_x - min_x
    y_size = max_y - min_y
    z_size = max_z - min_z

    padding_x = 0.05 * x_size if (x_size != 0) else 1
    padding_y = 0.05 * y_size if (y_size != 0) else 1
    padding_z = 0.05 * z_size if (z_size != 0) else 1

    # 5) Set up plot ranges (we ensure at least ±2 in each axis so small objects are visible)
    plot_x_range = (min(min_x - padding_x, -2), max(max_x + padding_x, 2))
    plot_y_range = (min(min_y - padding_y, -2), max(max_y + padding_y, 2))
    plot_z_range = (min(min_z - padding_z, -2), max(max_z + padding_z, 2))

    ax.set_xlim(*plot_x_range)
    ax.set_ylim(*plot_y_range)
    ax.set_zlim(*plot_z_range)

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')

    # 6) Draw the “axes” as simple line segments, if requested
    def _draw_axis_line(start, end, color=black, linestyle='solid'):
        xs_line = [start[0], end[0]]
        ys_line = [start[1], end[1]]
        zs_line = [start[2], end[2]]
        ax.plot(xs_line, ys_line, zs_line, color=color, linestyle=linestyle)

    if axes:
        # x‐axis: (plot_x_range[0], 0, 0) to (plot_x_range[1], 0, 0)
        _draw_axis_line((plot_x_range[0], 0, 0), (plot_x_range[1], 0, 0))
        # y‐axis: (0, plot_y_range[0], 0) to (0, plot_y_range[1], 0)
        _draw_axis_line((0, plot_y_range[0], 0), (0, plot_y_range[1], 0))
        # z‐axis: (0, 0, plot_z_range[0]) to (0, 0, plot_z_range[1])
        _draw_axis_line((0, 0, plot_z_range[0]), (0, 0, plot_z_range[1]))

    # 7) Optionally mark the origin (0,0,0) with a black 'x'
    if origin:
        ax.scatter([0], [0], [0], color='k', marker='x')

    # 8) Now loop over each object type and draw it:
    for obj in objects:
        # 8a) Draw Points3D as a scatter
        if isinstance(obj, Points3D):
            xs_pts, ys_pts, zs_pts = zip(*obj.vectors)
            ax.scatter(xs_pts, ys_pts, zs_pts, color=obj.color, depthshade=depthshade)

        # 8b) Draw Polygon3D by drawing each edge
        elif isinstance(obj, Polygon3D):
            N = len(obj.vertices)
            for i in range(N):
                p1 = obj.vertices[i]
                p2 = obj.vertices[(i + 1) % N]
                _draw_axis_line(p1, p2, color=obj.color)

        # 8c) Draw Arrow3D via ax.quiver
        elif isinstance(obj, Arrow3D):
            tx, ty, tz = obj.tail
            px, py, pz = obj.tip
            dx, dy, dz = px - tx, py - ty, pz - tz

            # arrow_length_ratio controls how big the arrowhead is
            ax.quiver(
                tx, ty, tz,
                dx, dy, dz,
                arrow_length_ratio=0.1,
                color=obj.color,
                linewidth=1.5,
                normalize=False
            )

        # 8d) Draw Segment3D via a straight line
        elif isinstance(obj, Segment3D):
            s = obj.start_point
            e = obj.end_point
            xs_line = [s[0], e[0]]
            ys_line = [s[1], e[1]]
            zs_line = [s[2], e[2]]
            ax.plot(xs_line, ys_line, zs_line, color=obj.color, linestyle=obj.linestyle)

        # 8e) Draw Box3D: dashed gray edges from (0,0,0) to (x,y,z)
        elif isinstance(obj, Box3D):
            x, y, z = obj.vector  # because vector is the triple (x, y, z)
            kwargs = {'linestyle': 'dashed', 'color': 'gray'}
            # 12 edges of a rectangular prism from (0,0,0) to (x,y,z)
            _draw_axis_line((0, y, 0), (x, y, 0), **kwargs)
            _draw_axis_line((0, 0, z), (0, y, z), **kwargs)
            _draw_axis_line((0, 0, z), (x, 0, z), **kwargs)
            _draw_axis_line((0, y, 0), (0, y, z), **kwargs)
            _draw_axis_line((x, 0, 0), (x, y, 0), **kwargs)
            _draw_axis_line((x, 0, 0), (x, 0, z), **kwargs)
            _draw_axis_line((0, y, z), (x, y, z), **kwargs)
            _draw_axis_line((x, 0, z), (x, y, z), **kwargs)
            _draw_axis_line((x, y, 0), (x, y, z), **kwargs)

        else:
            raise TypeError(f"Unrecognized object: {obj}")

    # 9) If user explicitly passed xlim/ylim/zlim, override our computed ranges
    if (xlim is not None) and (ylim is not None) and (zlim is not None):
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_zlim(*zlim)

    # 10) If user explicitly passed tick positions
    if (xticks is not None) and (yticks is not None) and (zticks is not None):
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.set_zticks(zticks)

    # 11) Optionally save to a file
    if save_as:
        plt.savefig(save_as)

    # 12) Finally show (in PyCharm’s Jupyter plugin this will render in the output cell)
    plt.show()
