"""
==========================
  ██████  ██████  ██   ██
 ██    ██ ██   ██ ██  ██
 ██    ██ ██████  █████ 
 ██    ██ ██      ██  ██ 
  ██████  ██      ██   ██
==========================
 Open Programmatic Keycap
==========================

OPK is a spherical top keycap profile developed in CadQuery
(https://github.com/CadQuery/cadquery) and released under the very permissive
Apache License 2.0. It's especially suited for creating high/medium profile,
spherical top keycaps.

!!! The profile is still highly experimental and very alpha stage. ¡¡¡

If you use the code please give credit, if you do modifications consider 
releasing them back to the public under a permissive open source license.

Copyright 2023 sporkus
Copyright (c) 2022 Matteo "Matt3o" Spinelli
https://matt3o.com
"""

import math
import cadquery as cq
from typing import List, Optional, Tuple, Union

unit_x: float = 2  # keycap size in unit. Standard sizes: 1, 1.25, 1.5, ...
unit_y: float = 1
base_dim: float = 18.2  # 1-unit size in mm at the base
top_dim: float = 12.5  # 1-unit size in mm at the top
b_fillet: float = 0.5  # side Fillet at the base
t_fillet: float = 3.5  # side Fillet at the top
s_fillet: float = 0.9    # surface fillet
height: float = 9  # Height of the keycap before cutting the scoop 
angle: float = 2  # Angle of the top surface
depth: float = 2.5  # Scoop depth
thickness: float = 1.5  # Keycap sides thickness
convex: bool = True  # Is this a spacebar?
pos: bool = False  # use POS style stabilizers


def calc_base_dim(unit_x, unit_y, base_dim):
    """
    calculate dimensions of keycap at the bottom
    """

    def dim(unit):
        return 19.05 * unit - (19.05 - base_dim)

    return [dim(unit_x), dim(unit_y)]


def calc_top_dim(base_dims, top_dim):
    """
    calculate dimensions of keycap at the top, before tilting and cutting the scoop
    """
    diff = min(base_dims) - top_dim
    return [x - diff for x in base_dims]


def rounded_rect(w: float, h: float, radius: float) -> cq.Sketch:
    return cq.Sketch().rect(w, h).vertices().fillet(radius)


def make_keycap_shell(
    base_dims: List[float],
    b_fillet: float,
    top_dims: List[float],
    t_fillet: float,
    height: float,
    angle: float,
) -> cq.Workplane:
    if t_fillet < b_fillet:
        t_fillet = b_fillet + 1

    base = rounded_rect(*base_dims, b_fillet)
    mid = rounded_rect(*base_dims, (t_fillet - b_fillet) / 4)
    top = rounded_rect(*top_dims, t_fillet)

    return (
        cq.Workplane("XY")
        .placeSketch(
            base,
            mid.moved(
                cq.Location(cq.Vector(0, 0, height / 4), cq.Vector(1, 0, 0), angle / 4)
            ),
            top.moved(cq.Location(cq.Vector(0, 0, height), cq.Vector(1, 0, 0), angle)),
        )
        .loft()
    )

def saddle(x:float, w:float=1, h:float=1, steepness:int=1, convex:int=-1):
    if steepness <= 0:
        raise ValueError("steepness should be integers > 0")

    steepness *= 2
    return x, -convex * math.atan((x / w) ** steepness) * h / 1.55


def make_scoop(base_x, base_y, height, angle, convex=False) -> cq.Workplane:
    """
    Create a body that will be carved from the main shape to create the top scoop
    """
    if convex:
        scoop = (
            cq.Workplane("YZ")
            .transformed(
                offset=cq.Vector(0, height - 2.1, -base_x / 2),
                rotate=cq.Vector(0, 0, angle),
            )
            .moveTo(-base_y / 2, -1)
            .threePointArc((0, 2), (base_y / 2, -1))
            .lineTo(base_y / 2, 10)
            .lineTo(-base_y / 2, 10)
            .close()
            .extrude(base_x, combine=False)
        )
    else:
        scoop = (
            cq.Workplane("YZ")
            .transformed(
                offset=cq.Vector(0, height, base_x / 2), rotate=cq.Vector(0, 0, angle)
            )
            .moveTo(-base_y / 2 + 2, 0)
            .threePointArc((0, min(-0.1, -depth + 1.5)), (base_y / 2 - 2, 0))
            .lineTo(base_y / 2, height)
            .lineTo(-base_y / 2, height)
            .close()
            .workplane(offset=-base_x / 2)
            .moveTo(-base_y / 2 - 2, -0.5)
            .threePointArc((0, -depth), (base_y / 2 + 2, -0.5))
            .lineTo(base_y / 2, height)
            .lineTo(-base_y / 2, height)
            .close()
            .workplane(offset=-base_x / 2)
            .moveTo(-base_y / 2 + 2, 0)
            .threePointArc((0, min(-0.1, -depth + 1.5)), (base_y / 2 - 2, 0))
            .lineTo(base_y / 2, height)
            .lineTo(-base_y / 2, height)
            .close()
            .loft(combine=False)
        )
    return scoop


def make_noodle_scoop(top_x:float, top_y:float, translate_z:float) -> cq.Workplane:
    yz_wire = (
        cq.Workplane("YZ")
        .transformed(offset=(0,-2))
        .parametricCurve(lambda x: saddle(x, w=top_y, h=height,steepness=4, convex=1), start=-top_y, stop=top_y) 
    )

    scoop = (
        cq.Workplane("XZ")
        .parametricCurve(lambda x: saddle(x, w=top_x, h=height,steepness=2), start=-top_x, stop=top_y, makeWire=False)
        .close()
        .sweep(yz_wire)
        .translate((0, 0, translate_z))
    )

    return scoop


def calc_stem_points(unit_x, unit_y, pos=False) -> List[float]:
    """
    finds the locations of stems
    """
    stem_pts = []

    if unit_x < 2 and unit_y < 2:
        pos = False

    if not pos:  # standard stems
        stem_pts = [(0, 0)]
        width = unit_x if unit_x >= unit_y else unit_y
        if width > 2.75:
            dist = width / 2 * 19.05 - 19.05 / 2
            stem_pts.extend([(dist, 0), (-dist, 0)])
        elif width > 1.75:  # keycaps smaller than 3unit all have 2.25 stabilizers
            dist = 2.25 / 2 * 19.05 - 19.05 / 2
            stem_pts.extend([(dist, 0), (-dist, 0)])

        # flip x/y for vertical keys
        if unit_y > unit_x:
            stem_pts = [(y, x) for x, y in stem_pts]

    elif pos:  # POS-like stems
        stem_num_x = math.floor(unit_x)
        stem_num_y = math.floor(unit_y)
        stem_start_x = round(-19.05 * (stem_num_x / 2) + 19.05 / 2, 6)
        stem_start_y = round(-19.05 * (stem_num_y / 2) + 19.05 / 2, 6)

        for i in range(0, stem_num_y):
            for l in range(0, stem_num_x):
                stem_pts.extend([(stem_start_x + l * 19.05, stem_start_y + i * 19.05)])

    stem_pts.sort(key=lambda x: sum(x))

    return stem_pts


def make_cherry_stem() -> cq.Workplane:
    """
    makes a single cherry stem with supporting ribs
    """
    stem_dia = 2.75
    rib_thickness = 0.8
    stem_z_inset = 0.6
    cross_horiz = [4.15, 1.27]
    cross_vert = [1.12, 4.15]
    rib_z = 4.5

    cross_sketch = cq.Sketch().rect(*cross_horiz).rect(*cross_vert).clean()
    rib_sketch = (
        cq.Sketch()
        .circle(stem_dia)
        .rect(100, rib_thickness)
        .rect(rib_thickness, 100)
        .clean()
    )

    return (
        cq.Workplane()
        .circle(stem_dia)
        .extrude(rib_z - stem_z_inset)
        .faces(">Z")
        .workplane()
        .placeSketch(rib_sketch)
        .extrude(20)
        .faces("<Z")
        .workplane()
        .placeSketch(cross_sketch)
        .extrude(-4.6, combine="cut")
        .faces("<Z")
        .edges()
        .chamfer(0.2)
        .translate([0, 0, stem_z_inset])
    )


def make_alps_stem() -> cq.Workplane:
    """
    makes a single alps stem with supporting ribs
    """
    alps_stem_dims = [4.35, 2.1]
    rib_thickness = 0.8
    rib_z = 5.4

    rib_sketch = cq.Sketch().rect(100, rib_thickness).rect(rib_thickness, 100).clean()

    return (
        cq.Workplane()
        .rect(*alps_stem_dims)
        .extrude(20)
        .faces("<Z")
        .shell(-0.7)
        .faces(">X or <X or >Y or <Y")
        .edges()
        .chamfer(0.2)
        .faces("<Z")
        .workplane()
        .transformed(offset=[0, 0, -rib_z])
        .placeSketch(rib_sketch)
        .extrude(-20)
    )


def make_stems(unit_x: float, unit_y: float, pos: bool, type="cherry"):
    """
    make multiple stems based on keysize
    """    
    stem_pts = calc_stem_points(unit_x, unit_y, pos)

    if type not in ["cherry", "alps"]:
        raise TypeError('stem type must be one of ["cherry", "alps"]')

    stems = cq.Workplane()
    for pt in stem_pts:
        if pt == (0, 0) and type == "alps":
            stem = make_alps_stem().translate(pt)
        else:
            stem = make_cherry_stem().translate(pt)
        stems = stems.union(stem)

    return stems


def make_keycap(
    unit_x: float = unit_x,
    unit_y: float = unit_y,
    base_dim: float = base_dim,
    top_dim: float = top_dim,
    b_fillet: float = b_fillet,
    t_fillet: float = t_fillet,
    s_fillet: float = s_fillet,
    height: float = height,
    depth: float = depth,
    angle: float = depth,
    convex: bool = convex,
    pos: bool = False,
    stem_type="cherry",
):
    base_dims = calc_base_dim(unit_x, unit_y, base_dim)
    top_dims = calc_top_dim(base_dims, top_dim)
    base_inner_dims = [x - thickness for x in base_dims]
    top_inner_dims = [x - thickness for x in top_dims]

    scoop = make_scoop(*base_dims, height, angle, convex)
    if convex:
        t_fillet = t_fillet * 0.7

    inner_shell = make_keycap_shell(
        base_inner_dims, b_fillet, top_inner_dims, t_fillet, height - depth - thickness, angle
    )

    outer_shell = (
        make_keycap_shell(base_dims, b_fillet, top_dims, t_fillet, height, angle)
        .cut(scoop)
        .faces(">Z")
        .edges()
    )

    filleted = False
    surface_fillet = s_fillet
    while not filleted:
        try:
            outer_shell = outer_shell.fillet(surface_fillet)
            filleted = True
        except:
            surface_fillet -= 0.1

    stems = make_stems(unit_x, unit_y, pos, type=stem_type).intersect(outer_shell)
    keycap = outer_shell - inner_shell + stems

    return keycap 
