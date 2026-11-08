# Credits

## MRI imaging

**Adapted from:** Vivekanandan, J. N., & Usman, J. B. (2026). *A Three-Dimensional Lower Extremity Musculoskeletal
Geometry Model of An Asian Male* [Dataset]. Universiti Malaya Research Data Repository.
<https://doi.org/10.22452/RD/5T6TZ7> — released under **CC0 1.0 Universal (public domain)**; credited here for the
record. It's the same leg as the MR-I Ready tibia + fibula simulator.

One healthy adult male volunteer, right lower limb from hip to foot, acquired as multi-station **3D sagittal**
volumes and shared as DICOM exported from 3D Slicer (scanner model and field strength not recorded in the files).
Series used:

- `RT T1 VIBE SAG DIXON_IN` — 3D T1 VIBE Dixon, in-phase (1.15 × 1.15 × 1.2 mm) → the **T1** images
- `RT T2 FS SPC SAG L-LIMB` — 3D T2 SPACE with fat saturation (1.07 × 1.07 × 1.1 mm) → the **T2 FS** images

The volunteer had no injury. The clinical request in the simulator (a runner with thigh and groin pain) is fictional.

### Changes made

1. **Cropped** to the slab from about 30 mm above the top of the femoral head (acetabular roof) to about 35 mm below
   the knee joint (tibial tuberosity, fibular head): 560 mm, with the crop faces perpendicular to the femoral shaft.
2. **Medial edge.** The source sagittal slab ends 70 mm left of midline, so at hip level it cuts through the pelvis
   and groin. Everything medial of that edge is blanked (4 mm feather), and the coronal images use a rectangular
   left–right FOV whose medial edge sits just inside it. The axial FOV (220 mm, one thigh) stays inside it.
3. **Station seam flattened.** The hip/thigh and knee/calf table stations meet just above the knee, with the lower
   one about 1.3–1.4× brighter. A smooth per-level gain evens it out.
4. **Reconstructions.** The axial, coronal and sagittal series are **reformatted** from the 3D volumes (trilinear,
   slab-averaged), in the orientation a radiographer would plan them: axial perpendicular to the femoral shaft
   (which lies within 1.8° of the bore axis here), coronal parallel to the posterior femoral condyles (−11.3° on the
   axial: the leg lies slightly rolled out), sagittal perpendicular to that. Coronal + sagittal: 3.5 mm every
   4.2 mm, 580 mm FOV at 448 px. Axial: 6 mm every 7 mm (80 slices), 220 mm FOV at 320 px.
5. **The 3-plane localiser is synthesised.** The study's own localiser wasn't stored. Three straight localiser images
   were rebuilt from the 3D T1: 8 mm slab average, 580 mm FOV, 256 matrix, 40–46 % rectangular phase FOV on the
   coronal and sagittal, coil shading and Rician noise.
6. Pixel values were windowed to 8-bit and saved as JPEG (series) and PNG (localisers).
7. The geometry of every image is kept in `assets/calib.json` and drives the planning overlays. Eighteen landmarks
   (acetabular roof, femoral head and neck, greater trochanter, femoral shaft and anterior cortex, thigh edges,
   patella, both condyles, posterior condyles, knee joint, tibial tuberosity, fibular head) were picked by hand
   (±5 mm).
8. In the browser: the localiser k-space animation is a real Fourier transform of the localiser images; each scan
   shows the reconstructed slices that fall inside your stack, cropped to your FOV. Your exact angle doesn't
   re-slice the volume — the reference-orientation slices are shown, and your angle is graded against the reference
   (±10°). The leg position doesn't change the images.
9. The 3-D room shows a generic closed-bore magnet, not the real system.
10. Sequences other than T1 and T2 FS are listed for teaching only. There are no images for them.

Educational simulation. It isn't a medical device and isn't for clinical use.
