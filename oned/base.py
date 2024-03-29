# AUTOGENERATED! DO NOT EDIT! File to edit: oned/00_base.ipynb (unless otherwise specified).

__all__ = ['DistanceConverter', 'hatchbox', 'merge_MultiLineStrings', 'morsify', 'add_jittered_midpoints',
           'LineString_to_jittered_bezier', 'get_random_points_in_polygon']

# Cell
import bezier
import numpy as np
import shapely.geometry as shg
import shapely.affinity as sha
import shapely.ops as sho
from shapely.geometry import box, MultiLineString, Point, MultiPoint, Polygon, MultiPolygon, LineString
from shapely.affinity import rotate, translate, scale
from shapely.ops import split, triangulate
from shapely import speedups

import vsketch

# Cell
class DistanceConverter(object):

    def __init__(self, d, unit):
        setattr(self, unit, d)

    @property
    def inches(self):
        return self._inches

    @inches.setter
    def inches(self, inches):
        self._inches = inches
        self._mm = 25.4 * inches

    @property
    def mm(self):
        return self._mm

    @mm.setter
    def mm(self, d):
        self._mm = d
        self._inches = d / 25.4


# Cell
def hatchbox(rect, angle, spacing):
    """
    returns a Shapely geometry (MULTILINESTRING, or more rarely,
    GEOMETRYCOLLECTION) for a simple hatched rectangle.

    args:
    rect - a Shapely geometry for the outer boundary of the hatch
           Likely most useful if it really is a rectangle

    angle - angle of hatch lines, conventional anticlockwise -ve

    spacing - spacing between hatch lines

    GEOMETRYCOLLECTION case occurs when a hatch line intersects with
    the corner of the clipping rectangle, which produces a point
    along with the usual lines.
    """

    (llx, lly, urx, ury) = rect.bounds
    centre_x = (urx + llx) / 2
    centre_y = (ury + lly) / 2
    diagonal_length = ((urx - llx) ** 2 + (ury - lly) ** 2) ** 0.5
    number_of_lines = 2 + int(diagonal_length / spacing)
    hatch_length = spacing * (number_of_lines - 1)

    # build a square (of side hatch_length) horizontal lines
    # centred on centroid of the bounding box, 'spacing' units apart
    coords = []
    for i in range(number_of_lines):
        # alternate lines l2r and r2l to keep HP-7470A plotter happy ☺
        if i % 2:
            coords.extend([((centre_x - hatch_length / 2, centre_y
                          - hatch_length / 2 + i * spacing), (centre_x
                          + hatch_length / 2, centre_y - hatch_length
                          / 2 + i * spacing))])
        else:
            coords.extend([((centre_x + hatch_length / 2, centre_y
                          - hatch_length / 2 + i * spacing), (centre_x
                          - hatch_length / 2, centre_y - hatch_length
                          / 2 + i * spacing))])
    # turn array into Shapely object
    lines = MultiLineString(coords)
    # Rotate by angle around box centre
    lines = rotate(lines, angle, origin='centroid', use_radians=False)
    # return clipped array
    return rect.intersection(lines)

# Cell
def merge_MultiLineStrings(mls_list):
    merged_mls = []
    for mls in mls_list:
        if mls.type == 'MultiLineString':
            merged_mls += list(mls)
        elif mls.type == 'LineString':
            merged_mls.append(mls)
    return MultiLineString(merged_mls)

# Cell
def morsify(ls, buffer_factor=0.01):
    return ls.buffer(buffer_factor).buffer(-buffer_factor).boundary

# Cell
def add_jittered_midpoints(ls, n_midpoints, xstd, ystd, xbias=0, ybias=0):
    eval_range = np.linspace(0., 1., n_midpoints+2)
    pts = np.stack([ls.interpolate(t, normalized=True) for t in eval_range])
    x_jitter = np.random.randn(n_midpoints, 1) * xstd + xbias
    y_jitter = np.random.randn(n_midpoints, 1) * ystd + ybias
    pts[1:-1] += np.concatenate([x_jitter, y_jitter], axis=1)
    return shg.asLineString(pts)

# Cell
def LineString_to_jittered_bezier(ls, n_midpoints=1, xbias=0., xstd=0., ybias=0., ystd=0., normalized=True, n_eval_points=50):
    if normalized==True:
        xbias = xbias * ls.length
        xstd = xstd * ls.length
        ybias = ybias * ls.length
        ystd = ystd*ls.length

    jitter_ls = add_jittered_midpoints(ls, n_midpoints=n_midpoints, xbias=xbias, xstd=xstd, ybias=ybias, ystd=ystd,)
    curve1 = bezier.Curve(np.asfortranarray(jitter_ls).T, degree=n_midpoints+1)
    bez = curve1.evaluate_multi(np.linspace(0., 1., n_eval_points))
    return shg.asLineString(bez.T)

# Cell
def get_random_points_in_polygon(polygon, n_points=1, xgen=None, ygen=None):
    points = []
    minx, miny, maxx, maxy = polygon.bounds
    if xgen == None:
        xgen = lambda size=None: np.random.uniform(minx, maxx, size)
    if ygen == None:
        ygen = lambda size=None: np.random.uniform(miny, maxy, size)

    for i in range(n_points):
        point = Point((xgen(), ygen()))
        if polygon.contains(point):
            points.append(point)
    return points