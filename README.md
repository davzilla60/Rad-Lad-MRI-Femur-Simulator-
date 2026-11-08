# MR-I Ready — Femur

An embeddable, single-file teaching simulator for the Rad-Lad website, built on the MR-I Ready engine (a fork of
the tibia + fibula simulator). Every diagnostic image is reformatted from **one real 3D MRI of a healthy volunteer's
right leg** (public-domain research data, the same leg as the tibia + fibula simulator — see `CREDITS.md`), cropped
to **above the femoral head → below the knee**, and shown with its true geometry. **It's a demonstration only.**

Marker: **The Thigh's the Limit** — axial square to the femur from above the femoral head to below the knee,
coronal parallel to the posterior condyles, sagittal perpendicular to it, every plane hip joint to knee joint,
with the legs straight and the feet together and turned slightly in.

## Flow

1. **Patient set-up.** Supine, **feet first**, two flexible body arrays wrapped round the right thigh from the greater
   trochanter to just below the knee, skin marker over the tender point. Choose how the legs lie (the 3-D room
   changes pose):
   - legs straight, feet together and turned ~15° in, taped, sandbags — correct (puts the femoral neck in profile);
   - right foot rolled outward, unsupported — foreshortens the neck, and the leg drifts;
   - knee bent over a wedge — the femur slopes out of the bore axis and the arrays can't sit evenly.
2. **Localiser.** A 3-plane localiser (580 mm FOV) is "acquired" line by line from its own k-space. It is
   **synthesised** from the volunteer's 3D T1 (the study's own localiser wasn't stored).
3. **Axial first.** Cover acetabular roof → tibial tuberosity (~550 mm), FOV just wider than the thigh (~200–220 mm).
4. **Coronal + sagittal** unlock once the axial is scanned. Drag (or tap) the axial onto the **AXIAL** panel to unlock
   the rotate handle — it opens at the femoral condyles. Coronal parallel to the posterior condylar line (reference
   −11.3°; straight fails), sagittal perpendicular (78.7°), graded ±10°. Both must hold the femoral head, greater
   trochanter, shaft, both condyles and both joints in a long FOV (~550–580 mm).
5. **Scan → images.** T1 and T2 FS in each plane, cropped to your FOV.
6. **Debrief.** Coverage and angle per plan, position, hero images, a sequences-to-consider table and the marker.

CLI: `straight | rotated | flexed`, `load`, `loc`, `plan ax|cor|sag`, `auto`, `slices`, `thick`, `gap`, `fov`,
`angle`, `use <series>`, `restore <sag|cor|ax>`, `scan`, `back`, `finish`, `help`.

## Files

- `femur.embed.html` is the self-contained deliverable (~3.9 MB, every image inlined). `index.html` is an
  identical copy for one-drop hosting.
- `femur.html` + `app.js` + `room3d.js` + `assets/` are the editable sources. After editing, rebuild with
  `python inline.py`.
- `tools/gen_assets.py` rebuilds `assets/` from the unzipped `DICOM/` folder of the source study:
  `python -I tools/gen_assets.py "<folder holding DICOM/>"`. `tools/patch_app.py` is the one-off script that turned
  the tibia + fibula `app.js` into this one (kept for the record; don't re-run it).
- The 3-D room loads three.js 0.160 from jsDelivr; without it the set-up step falls back to a flat drawing.

Educational simulation — not a medical device, not for clinical use.
