import cadquery as cq
from cadquery import exporters
from opk import make_keycap

keys = {
    0: [
        # { 'unit_x': 1 },
    ],
    1: [
        {"unit_x": 1},
        # { 'unit_x': 2 }
    ],
    2: [
        {"unit_x": 1},
        { 'unit_x': 1.25 },
        { 'unit_x': 1.5 },
        { 'unit_x': 1.75 },
        { 'unit_x': 2 }
    ],
    3: [
        {"unit_x": 1},
        # { 'unit_x': 1, 'depth': 3.6 },
        {"unit_x": 1.25},
        {"unit_x": 1.5},
        {"unit_x": 1.75},
        {"unit_x": 2},
        {"unit_x": 2.25},
        {"unit_x": 2.75},
        {"unit_x": 3},
    ],
    4: [
        {"unit_x": 1},
        { 'unit_x': 1.25 },
        # { 'unit_x': 1.5 },
        { 'unit_x': 1.75 },
        # { 'unit_x': 2 },
        { 'unit_x': 2.25 },
        # { 'unit_x': 1.25   , 'convex': True },
        # { 'unit_x': 1.5    , 'convex': True },
        # { 'unit_x': 1.75   , 'convex': True },
        { 'unit_x': 2      , 'convex': True },
        # { 'unit_x': 2.25   , 'convex': True },
        # { 'unit_x': 2.75   , 'convex': True },
        { 'unit_x': 3.00   , 'convex': True },
    ],
    5: [
        {"unit_x": 1},
        { 'unit_x': 1.25},
        { 'unit_x': 1.50},
        # { 'unit_x': 1.75},
        # { 'unit_x': 1.25, 'convex': True },
        # { 'unit_x': 1.5 , 'convex': True },
        # { 'unit_x': 1.75, 'convex': True },
        {"unit_x": 2, "convex": True},
        {"unit_x": 2.25, "convex": True},
        {"unit_x": 2.75, "convex": True},
        {"unit_x": 3, "convex": True},
        # { 'unit_x': 6.25, 'convex': True },
        # { 'unit_x': 7   , 'convex': True }
    ],
}

# About 2mm lower than matt3o's original
rows = [
    {"angle": 13, "height": 14, "keys": keys[0]},  # row 0, function row
    {"angle": 9, "height": 12, "keys": keys[1]},  # row 1, numbers row
    {"angle": 8, "height": 9.75, "keys": keys[2]},  # row 2, QWERT
    {"angle": -6, "height": 8.75, "keys": keys[3]},  # row 3, ASDFG
    {"angle": -8, "height": 10.5, "keys": keys[4]},  # row 4, ZXCVB
    {"angle": 0, "height": 10.5, "keys": keys[5]},  # row 5, bottom row
]


def export_keys(key_rows=rows, export=False, export_assy=False, tol:float=0.0005, angular_tol:float=0.05):
    assy = cq.Assembly()

    y = 0
    for i, r in enumerate(key_rows):
        x = 0
        for k in r["keys"]:
            name = "row{}_U{}".format(i, k["unit_x"])
            convex = False
            if "convex" in k:
                convex = k["convex"]
                name += "_convex"

            depth = 2.8
            if "depth" in k:
                if k["depth"] > depth:
                    name += "_homing"
                depth = k["depth"]

            print("Generating: ", name)
            cap = make_keycap(
                angle=r["angle"],
                height=r["height"],
                unit_x=k["unit_x"],
                convex=convex,
                depth=depth,
                stem_type="alps"
            )
            # Export one key at the time

            if export:
                # exporters.export(
                #     cap,
                #     "./export/STEP/" + name + ".step",
                #     tolerance=tol,
                #     angularTolerance=angular_tol
                # )
                exporters.export(
                    cap,
                    "./export/STL/" + name + ".stl",
                    tolerance=tol,
                    angularTolerance=angular_tol
                )
            w = 19.05 * k["unit_x"] / 2
            x += w
            assy.add(cap, name=name, loc=cq.Location(cq.Vector(x, y, 0)))
            x += w
        y -= 19.05

    if "show_object" in locals():
        show_object(assy)

    if export_assy:
        exporters.export(
            assy.toCompound(), "./export/opk_keycaps_all.stl", tolerance=tol, angularTolerance=angular_tol
        )
        exporters.export(
            assy.toCompound(),
            "./export/opk_keycaps_all.step",
            tolerance=tol,
            angularTolerance=angular_tol,
        )

    return assy

if __name__ == "__main__":
    export_keys(rows, export=True, export_assy=True)
