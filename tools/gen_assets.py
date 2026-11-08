"""Build ../assets for the FEMUR simulator from the same leg MRI as the tibia + fibula one
(Prometheus "MRI/Tibia and fibula/Patient 2", DICOM.zip; Universiti Malaya RDR doi:10.22452/RD/5T6TZ7, CC0).

    python -I tools/gen_assets.py "<folder holding the unzipped DICOM/ folder>"

Source: a whole right lower limb (hip to toes) acquired as multi-station 3D SAGITTAL volumes (T1 VIBE Dixon and
T2 SPACE ± fat sat, ~1.1 mm isotropic), exported by 3D Slicer. The sagittal slab only reaches x = +70 mm, so at hip
level the pelvis is cut off medially: everything medial of x = 68 mm is blanked (feathered), and the coronal images
use a rectangular left-right FOV so the cut never shows as a hard edge.
  * CROP: from ~30 mm above the top of the femoral head (acetabular roof) to ~35 mm below the knee joint (tibial
    tuberosity, fibular head) - 560 mm, crop faces perpendicular to the femoral shaft.
  * STATION SEAM: the hip/thigh and knee/calf table stations meet just above the knee with a brightness step;
    flattened with a smooth per-level gain.
  * RECONSTRUCTIONS: AXIAL (perpendicular to the femoral shaft), CORONAL (parallel to the posterior femoral
    condyles) and SAGITTAL (perpendicular to that), reformatted (trilinear, slab-averaged) from the 3D volumes.
  * LOCALISER: a straight 3-plane localiser is SYNTHESISED (8 mm slab, 256 matrix, 580 mm FOV, coil shading, noise,
    rectangular phase FOV).
Writes loc_*.png, <series>_NN.jpg and calib.json / calib.js. All coordinates are DICOM patient (LPS) millimetres.
"""
import sys, os, glob, json
import numpy as np, pydicom, cv2
from scipy.ndimage import map_coordinates, gaussian_filter1d, median_filter

ROOT = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
QA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "qa")
os.makedirs(OUT, exist_ok=True); os.makedirs(QA, exist_ok=True)
rng = np.random.default_rng(12)
NAMES = {"t1": "RT T1 VIBE SAG DIXON_IN", "t2fs": "RT T2 FS SPC SAG L-LIMB"}
ZLO, ZHI = -470.0, 178.0                        # native rows kept in memory (crop margin)
XMED = 68.0                                     # medial edge of the source slab (data ends at x = 70)

def unit(a): a = np.asarray(a, float); return a / np.linalg.norm(a)

# ------------------------------------------------------------------ native 3D sagittal volumes
def load_native(key):
    fs = sorted(glob.glob(os.path.join(ROOT, "DICOM", NAMES[key], "*")))
    hs = [pydicom.dcmread(f) for f in fs]
    hs.sort(key=lambda h: float(h.ImagePositionPatient[0]))
    assert [round(float(v), 4) for v in hs[0].ImageOrientationPatient] == [0, 1, 0, 0, 0, -1]
    xs = np.array([float(h.ImagePositionPatient[0]) for h in hs]); assert np.all(np.diff(xs) > 0)
    y0, z0, ps = float(hs[0].ImagePositionPatient[1]), float(hs[0].ImagePositionPatient[2]), float(hs[0].PixelSpacing[0])
    for h in hs: assert abs(float(h.ImagePositionPatient[1]) - y0) < 1e-3 and abs(float(h.ImagePositionPatient[2]) - z0) < 1e-3
    r0, r1 = max(0, int((z0 - ZHI) / ps)), int((z0 - ZLO) / ps) + 1
    v = np.stack([h.pixel_array[r0:r1] for h in hs]).astype(np.float32)        # [x slice, row (-z), col (+y)]
    nat = dict(v=v, xs=xs, y0=y0, z0=z0 - r0 * ps, ps=ps)
    seam_fix(nat, key)
    return nat

def seam_fix(nat, key):
    """The hip/thigh and knee/calf stations meet just above the knee; the lower one is brighter. Gain = 1 above the
    blend zone, the measured ratio below it, level-matched inside it (measured on the thigh muscle either side)."""
    v, ps, z0 = nat["v"], nat["ps"], nat["z0"]
    zr = z0 - np.arange(v.shape[1]) * ps
    thr = 0.3 * np.percentile(v, 99.5)
    m = np.array([np.median(v[:, r][v[:, r] > thr]) if np.any(v[:, r] > thr) else np.nan for r in range(v.shape[1])])
    m = median_filter(np.nan_to_num(m), size=13)
    za, zb = -180.0, -240.0
    hi = np.median(m[(zr < -150) & (zr > za)]); lo = np.median(m[(zr < zb) & (zr > -262)])
    ratio = hi / lo
    f = np.ones_like(zr); f[zr <= zb] = ratio
    mid = (zr < za) & (zr > zb); f[mid] = hi / np.maximum(m[mid], 1e-3)
    f = gaussian_filter1d(f, 3)
    v *= f[None, :, None]
    print(key, "seam gain below %.0f mm: x%.3f" % (zb, ratio))

def sample(nat, P):
    fi = np.interp(P[..., 0], nat["xs"], np.arange(len(nat["xs"])), left=-10, right=len(nat["xs"]) + 10)
    fr = (nat["z0"] - P[..., 2]) / nat["ps"]; fc = (P[..., 1] - nat["y0"]) / nat["ps"]
    return map_coordinates(nat["v"], [fi, fr, fc], order=1, mode="constant", cval=0.0)

NAT = {k: load_native(k) for k in NAMES}

# ------------------------------------------------------------------ anatomy (picked on 0.5 mm axial reformats of the T1)
FEM = np.array([[-50.0, 5.0, -60], [-52.5, -2.5, -150], [-52.5, 0.0, -240]])      # femoral shaft centres
c0 = FEM.mean(0); _, _, vt = np.linalg.svd(FEM - c0); LUP = unit(vt[0] * np.sign(vt[0][2]))
ZMID = -145.0
A0 = c0 + LUP * ((ZMID - c0[2]) / LUP[2])
S_HALF = 280.0                                   # crop: z ≈ +135 (above the femoral head) to ≈ -425 (below the knee)
COND = -11.3                                     # posterior condylar line on the axial (same knee as the tibia sim)
def keep(P):
    s = (P - A0) @ LUP
    return np.clip((S_HALF - np.abs(s)) + 0.5, 0, 1) * np.clip((XMED - P[..., 0]) / 4.0, 0, 1)

def planes_frame(t_deg):
    t = np.radians(t_deg); d = np.array([np.cos(t), np.sin(t), 0])
    u = unit(d - LUP * (d @ LUP)); v = unit(-(LUP - u * (LUP @ u)))
    return u, v, np.cross(u, v)
UC, VC, NC = planes_frame(COND)
US, VS, NS = NC, VC, np.cross(NC, VC)
UA = unit(np.array([1.0, 0, 0]) - LUP * LUP[0]); VA = np.cross(LUP, UA); NA = LUP
print("femoral axis (superior):", LUP.round(4), "tilt %.1f deg" % np.degrees(np.arccos(LUP[2])), "A0", A0.round(1))

def to8(a, hi): return np.clip(a / hi * 255, 0, 255).astype(np.uint8)
HI = {k: float(np.percentile(n["v"][n["v"] > 0], 99.6 if k == "t1" else 99.2)) for k, n in NAT.items()}

# ------------------------------------------------------------------ reconstructions
def recon(key, ctr, u, v, n, N, fov, thk, sp, count, band=None):
    ps = fov / N
    I, J = np.meshgrid(np.arange(N) - (N - 1) / 2, np.arange(N) - (N - 1) / 2)
    ipps, imgs = [], []
    first = ctr - n * sp * (count - 1) / 2
    colmask = 1.0
    if band is not None:                              # rectangular left-right FOV (coronal)
        colmask = np.clip((I * ps - band[0]) / 3.0, 0, 1) * np.clip((band[1] - I * ps) / 3.0, 0, 1)
    for k in range(count):
        c = first + n * sp * k
        base = c + I[..., None] * ps * u + J[..., None] * ps * v
        acc = np.zeros((N, N), np.float32)
        offs = np.linspace(-thk / 2 + thk / 10, thk / 2 - thk / 10, 5)
        for t in offs:
            P = base + n * t
            acc += sample(NAT[key], P) * keep(P)
        imgs.append(acc / len(offs) * colmask)
        ipps.append(c - u * ps * (N - 1) / 2 - v * ps * (N - 1) / 2)
    return imgs, ipps, ps

calib = {"ser": {}}
LEGC = np.array([-48.0, 20.0, ZMID])             # middle of the thigh cross-section
STACKS = [  # id, src, plane, label, params, u, v, n, N, FOV, thk, spacing, count, s/slice
    ("cor_t1",   "t1",   "cor", "T1",    "3D T1 VIBE (in-phase) · reformatted 3.5 mm",      UC, VC, NC, 448, 580, 3.5, 4.2, 41, 3.4),
    ("cor_t2fs", "t2fs", "cor", "T2 FS", "3D T2 SPACE fat sat · reformatted 3.5 mm",        UC, VC, NC, 448, 580, 3.5, 4.2, 41, 4.6),
    ("sag_t2fs", "t2fs", "sag", "T2 FS", "3D T2 SPACE fat sat · reformatted 3.5 mm",        US, VS, NS, 448, 580, 3.5, 4.2, 48, 4.6),
    ("sag_t1",   "t1",   "sag", "T1",    "3D T1 VIBE (in-phase) · reformatted 3.5 mm",      US, VS, NS, 448, 580, 3.5, 4.2, 48, 3.4),
    ("ax_t2fs",  "t2fs", "ax",  "T2 FS", "3D T2 SPACE fat sat · reformatted 6 mm / 7 mm",   UA, VA, NA, 320, 220, 6.0, 7.0, 80, 2.6),
    ("ax_t1",    "t1",   "ax",  "T1",    "3D T1 VIBE (in-phase) · reformatted 6 mm / 7 mm", UA, VA, NA, 320, 220, 6.0, 7.0, 80, 1.9),
]
for sid, src, plane, label, params, u, v, n, N, fov, thk, sp, cnt, spl in STACKS:
    if plane == "ax": ctr = A0 + UA * (-45.0 - A0[0]) + VA * (20.0 - A0[1])
    elif plane == "sag": ctr = LEGC + n * (-(-40.0 - LEGC[0]))      # stack centred at x ≈ -40 (head -15 … lateral thigh -140)
    else: ctr = LEGC + n * 0.0
    band = (-150.0, 108.0) if plane == "cor" else None    # lateral wide open; medial edge just inside the data limit
    imgs, ipps, ps = recon(src, ctr, u, v, n, N, fov, thk, sp, cnt, band)
    for k, a in enumerate(imgs):
        cv2.imwrite(os.path.join(OUT, "%s_%02d.jpg" % (sid, k)), to8(a, HI[src]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    calib["ser"][sid] = {"task": plane, "plane": plane, "seq": label, "params": params, "n": cnt,
                         "ipp": [[round(float(x), 2) for x in p] for p in ipps], "row": [round(float(x), 5) for x in u],
                         "col": [round(float(x), 5) for x in v], "ps": round(ps, 6), "cols": N, "rows": N,
                         "nrm": [round(float(x), 5) for x in n], "sp": sp, "thk": thk, "spl": spl, "pad": 2}
    print(sid, cnt, "slices")

# ------------------------------------------------------------------ synthetic 3-plane localiser (straight, at isocentre)
LOC_FOV, LN = 580.0, 256
LPS = LOC_FOV / LN
LOC_C = np.array([-50.0, 20.0, ZMID])
LOC = {   # plane: row dir, col dir, slice offset, phase axis (array axis), phase FOV
    "sag": (np.array([0, 1.0, 0]), np.array([0, 0, -1.0]), np.array([10.0, 0, 0]), 1, 0.46),
    "cor": (np.array([1.0, 0, 0]), np.array([0, 0, -1.0]), np.array([0, -10.0, 0]), 1, 0.40),
    "ax":  (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 45.0]), 0, 1.0),
}
calib["loc"] = {"n": LN, "fov": LOC_FOV}
for p, (r, c, off, phase, pf) in LOC.items():
    n = np.cross(r, c); ctr = LOC_C + off
    SS = 2; N2 = LN * SS
    I, J = np.meshgrid((np.arange(N2) + 0.5) / SS - LN / 2, (np.arange(N2) + 0.5) / SS - LN / 2)
    base = ctr + I[..., None] * r * LPS + J[..., None] * c * LPS
    img = np.mean([sample(NAT["t1"], base + n * t) * keep(base + n * t) for t in np.linspace(-3.5, 3.5, 6)], axis=0)
    img = cv2.resize(img.astype(np.float32), (LN, LN), interpolation=cv2.INTER_AREA)
    Pc = ctr + ((np.arange(LN) + 0.5) - LN / 2)[None, :, None] * r * LPS + ((np.arange(LN) + 0.5) - LN / 2)[:, None, None] * c * LPS
    dxy = np.hypot(Pc[..., 0] + 45, Pc[..., 1] - 20)            # flexible arrays round the thigh
    coil = 0.72 + 0.28 * np.clip(dxy / 95, 0, 1) ** 1.5
    coil *= 0.55 + 0.45 * np.exp(-((Pc[..., 2] - ZMID) / 290) ** 4)
    img = img * coil
    img = gaussian_filter1d(img, 0.8, axis=phase)
    sig = 0.02 * np.percentile(img, 99.5)
    img = np.hypot(img + rng.normal(0, sig, img.shape), rng.normal(0, sig, img.shape))
    if pf < 1:
        band = np.abs(np.arange(LN) + 0.5 - LN / 2) <= LN * pf / 2
        img = img * (band[None, :] if phase == 1 else band[:, None])
    hi = np.percentile(img[img > 0], 99.6)
    cv2.imwrite(os.path.join(OUT, "loc_" + p + ".png"), np.clip((img / hi) ** 0.9 * 255, 0, 255).astype(np.uint8))
    ipp = ctr - r * LPS * LN / 2 - c * LPS * LN / 2 + (r + c) * LPS / 2
    calib["loc"][p] = {"ipp": [round(float(x), 2) for x in ipp], "row": r.tolist(), "col": c.tolist(), "ps": round(LPS, 6), "cols": LN, "rows": LN}

# ------------------------------------------------------------------ landmarks (±5 mm, picked on the T1 reformats)
calib["lm"] = {
    "conf":  [round(float(x), 1) for x in LEGC],   # reference centre (mid-thigh) for "mm from centre" readouts
    "acet":  [-20.0, 5.0, 110.0],     # acetabular roof, above the femoral head
    "head":  [-15.0, 10.0, 82.0],     # femoral head centre
    "neck":  [-38.0, 18.0, 70.0],     # femoral neck
    "gt":    [-65.0, 25.0, 65.0],     # greater trochanter
    "fmid":  [-51.0, 0.0, -100.0],    # mid femoral shaft
    "afem":  [-51.0, -15.0, -100.0],  # anterior femoral cortex
    "quad":  [-50.0, -50.0, -100.0],  # front of the thigh (quadriceps)
    "ham":   [-40.0, 90.0, -60.0],    # back of the thigh (hamstrings)
    "itb":   [-112.0, 20.0, -60.0],   # lateral thigh (vastus lateralis / iliotibial band)
    "add":   [35.0, 40.0, -60.0],     # medial thigh (adductors)
    "pat":   [-60.0, -25.0, -290.0],  # patella
    "mcond": [-25.0, 32.0, -338.0],   # medial femoral condyle
    "lcond": [-82.0, 38.0, -338.0],   # lateral femoral condyle
    "pcond": [-55.0, 50.0, -335.0],   # posterior femoral condyles
    "kj":    [-55.0, 35.0, -355.0],   # knee joint
    "tt":    [-57.0, 2.0, -392.0],   # tibial tuberosity (below the knee)
    "fh":    [-101.0, 57.0, -368.0],  # fibular head
}
calib["real"] = {"cor": COND, "sag": round(COND + 90, 1), "lup": [round(float(x), 5) for x in LUP],
                 "tilt": round(float(np.degrees(np.arccos(LUP[2]))), 1), "a0": [round(float(x), 1) for x in A0], "half": S_HALF}
json.dump(calib, open(os.path.join(OUT, "calib.json"), "w"), indent=1)
open(os.path.join(OUT, "calib.js"), "w").write("window.MRS_CALIB=" + json.dumps(calib, separators=(",", ":")) + ";\n")

def qa(sid, keys):
    s = calib["ser"][sid]; ipp = np.array(s["ipp"]); r = np.array(s["row"]); c = np.array(s["col"]); nrm = np.array(s["nrm"])
    tiles = []
    for key in keys:
        P = np.array(calib["lm"][key]); k = int(np.argmin(np.abs((P - ipp) @ nrm)))
        im = cv2.cvtColor(cv2.imread(os.path.join(OUT, "%s_%02d.jpg" % (sid, k)), 0), cv2.COLOR_GRAY2BGR)
        x, y = (P - ipp[k]) @ r / s["ps"], (P - ipp[k]) @ c / s["ps"]
        cv2.circle(im, (int(x), int(y)), 6, (0, 0, 255), 1); cv2.putText(im, key, (int(x) + 8, int(y)), 0, 0.45, (0, 255, 255), 1)
        tiles.append(im)
    cv2.imwrite(os.path.join(QA, "qa_" + sid + ".png"), np.hstack(tiles))
qa("cor_t1", ["head", "gt", "fmid", "pcond", "kj", "fh"])
qa("sag_t1", ["head", "gt", "fmid", "mcond", "lcond", "pat"])
qa("ax_t1", ["acet", "head", "gt", "fmid", "itb", "tt"])
print("ok")
