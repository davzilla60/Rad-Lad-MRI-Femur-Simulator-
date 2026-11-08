"""One-off: turn the tibia + fibula app.js (copied here) into the femur app.js."""
import re
p = "app.js"; s = open(p, encoding="utf-8").read()

SEQPOS = r'''var SEQ = {
  ax:  { name:"AXIAL", dirName:"superior", ideal:"ax_t2fs",
         start:{ c:[-45,20,-145], ang:0, n:45, thk:6, gap:1, fov:200 },
         regions:[[-225,"proximal tibia · tibial tuberosity"],[-200,"knee joint"],[-165,"femoral condyles"],[-125,"patella · suprapatellar pouch"],[-60,"distal femoral shaft"],[80,"femoral shaft"],[150,"proximal shaft · lesser trochanter"],[205,"femoral neck · trochanters"],[245,"femoral head"],[1e9,"acetabular roof · iliac bone"]],
         key:[["acet","Above the femoral head (acetabular roof)"],["head","Femoral head + neck"],["gt","Greater trochanter"],["fmid","Femoral shaft"],["kj","Knee joint"],["tt","Below the knee (tibial tuberosity)"],["itb","Whole thigh in the FOV (lateral edge)"],["ham","Whole thigh in the FOV (back of the thigh)"]],
         hint:"Axial, perpendicular to the femur: from above the femoral head (acetabular roof) to below the knee (tibial tuberosity) — about 550 mm, a long stack. FOV just wider than the thigh at its widest (≈ 200–220 mm), one thigh only.",
         seqs:[
           { id:"t2fs", name:"T2 FS / STIR", why:"marrow and periosteal oedema: stress reaction, fracture, muscle and tendon injury, collections", have:"ax_t2fs" },
           { id:"t1",   name:"T1", why:"marrow fat, the cortex and any fracture line in cross-section", have:"ax_t1" },
           { id:"dwi",  name:"DWI", why:"if a marrow or soft-tissue lesion is found (tumour, abscess)", rec:true },
           { id:"gad",  name:"T1 FS + gadolinium", why:"infection or tumour: enhancement, abscess, skip lesions — not needed for a stress injury" } ] },
  cor: { name:"CORONAL", dirName:"posterior", ideal:"cor_t1",
         start:{ c:[-45,20,-145], ang:0, n:26, thk:3.5, gap:0.5, fov:480 },
         regions:[[-55,"quadriceps · front of the thigh"],[-38,"patella · anterior femur"],[-5,"femoral shaft · femoral head"],[20,"greater trochanter · linea aspera"],[45,"posterior condyles"],[1e9,"hamstrings · back of the thigh"]],
         key:[["afem","Anterior femoral cortex"],["fmid","Femoral shaft"],["head","Femoral head + neck"],["gt","Greater trochanter"],["pcond","Posterior femoral condyles"],["acet","Acetabular roof (hip joint)"],["kj","Knee joint"],["fh","Fibular head (below the knee)"]],
         hint:"Coronal: parallel to the posterior condyles of the knee on the axial, along the femur on the sagittal. Front of the femur to behind the condyles, and a long FOV (≈ 550–580 mm) from above the hip joint to below the knee — both joints on every slice. The coronal STIR is the key sequence for a femoral neck stress fracture.",
         seqs:[
           { id:"t1",   name:"T1", why:"the whole femur: marrow, cortex, a fracture line (a femoral neck stress fracture is a low-signal line on the medial / compression side)", have:"cor_t1" },
           { id:"t2fs", name:"STIR / T2 FS", why:"marrow oedema along the neck and shaft; muscle and tendon injury", have:"cor_t2fs" },
           { id:"hip",  name:"Small-FOV coronal STIR of the hip", why:"if the pain is in the groin: a focused look at the femoral neck", rec:true } ] },
  sag: { name:"SAGITTAL", dirName:"lateral", ideal:"sag_t2fs",
         start:{ c:[-45,20,-145], ang:90, n:30, thk:3.5, gap:0.5, fov:480 },
         regions:[[-60,"adductors · medial thigh"],[-30,"femoral head · medial condyle"],[-10,"medial femur"],[12,"femoral shaft"],[40,"greater trochanter · lateral condyle"],[1e9,"vastus lateralis · iliotibial band"]],
         key:[["head","Femoral head (medial)"],["mcond","Medial femoral condyle"],["fmid","Femoral shaft"],["gt","Greater trochanter (lateral)"],["lcond","Lateral femoral condyle"],["pat","Patella"],["acet","Acetabular roof"]],
         hint:"Sagittal: perpendicular to the coronal on the axial, along the femur on the coronal. Femoral head and medial condyle to the greater trochanter and lateral condyle side to side, long FOV hip to knee.",
         seqs:[
           { id:"t2fs", name:"T2 FS / STIR", why:"the anterior and posterior cortex, quadriceps and hamstring injuries, the knee extensor mechanism", have:"sag_t2fs" },
           { id:"t1",   name:"T1", why:"cortical thickening, marrow fat, a fracture line", have:"sag_t1" } ] }
};
var POS = {
  straight: { label:"LEGS STRAIGHT · FEET TOGETHER, TURNED IN", desc:"Both legs straight, big toes together with the feet turned slightly inward, taped, pads either side.",
          cap:"SUPINE · FEET FIRST · FEET TURNED IN", sub:"feet together, slight internal rotation, taped", short:"legs straight, feet turned in",
          fit:"Legs straight, <b>feet together and turned slightly in (≈ 15° internal rotation)</b>, taped · pads and sandbags",
          note:"Turning the feet in brings the femoral neck out of its natural anteversion, so it lies flat in the coronal plane — the femoral neck is shown in profile, end to end. Taped and padded, the leg stays still.",
          cls:"ok" },
  rotated: { label:"FOOT FALLEN OUTWARD", desc:"Legs straight but unsupported — the right foot rolls out into external rotation.",
          cap:"SUPINE · FEET FIRST · FOOT ROLLED OUT", sub:"no pads: the leg drifts into external rotation", short:"foot rolled out (unsupported)",
          fit:"Legs straight, right foot left to roll outward (no pads)",
          note:"External rotation foreshortens the femoral neck on the coronal (exactly where a stress fracture hides), and an unsupported leg drifts during a 30-minute scan. Feet together, turned in, taped.",
          cls:"warn" },
  flexed: { label:"KNEE BENT ON A WEDGE", desc:"Knee flexed over a foam wedge for comfort.",
          cap:"SUPINE · FEET FIRST · KNEE FLEXED", sub:"knee bent over a wedge", short:"knee bent on a wedge",
          fit:"Knee bent over a foam wedge",
          note:"Comfortable, but the femur now slopes up out of the bore axis, the hip flexes and the arrays can't sit evenly along the thigh — the coverage, hip to knee, needs a much bigger box. Keep the legs straight.",
          cls:"warn" }
};
'''
a = s.index("var SEQ = {"); b = s.index("function regionName")
s = s[:a] + SEQPOS + s[b:]

R = [
 ("MR-I READY — MRI TIBIA + FIBULA planning simulator (demonstration)", "MR-I READY — MRI FEMUR planning simulator (demonstration)"),
 ("Set-up (leg position, flexible arrays round the lower leg, feet first)", "Set-up (leg position, flexible arrays round the thigh, feet first)"),
 ("AXIAL first (perpendicular to the tibia, knee to ankle)", "AXIAL first (perpendicular to the femur, hip to knee)"),
 ("MR-I&nbsp;READY&nbsp;·&nbsp;TIBIA&nbsp;+&nbsp;FIBULA", "MR-I&nbsp;READY&nbsp;·&nbsp;FEMUR"),
 ('var LIM = { ax:  { nmax:100, tmin:2, tmax:8, fmin:120, fmax:320, coarse:260, narrow:150, over:560 },\n            cor: { nmax:70,  tmin:2, tmax:6, fmin:250, fmax:520, coarse:520, narrow:0,   over:200 },\n            sag: { nmax:60,  tmin:2, tmax:6, fmin:250, fmax:520, coarse:520, narrow:0,   over:170 } };',
  'var LIM = { ax:  { nmax:100, tmin:2, tmax:8, fmin:140, fmax:320, coarse:280, narrow:180, over:620 },\n            cor: { nmax:70,  tmin:2, tmax:6, fmin:300, fmax:580, coarse:580, narrow:0,   over:200 },\n            sag: { nmax:70,  tmin:2, tmax:6, fmin:300, fmax:580, coarse:580, narrow:0,   over:220 } };'),
 ("function scanBlockReason(q)", "function scanBlockReason(q)"),
 ('log("workflow: choose the leg position (straight | rotated | flexed)', 'log("workflow: choose the leg position (straight | rotated | flexed)'),
 ("the axial is kept straight on the axial — tilt it on the sagittal with the ⟳ handles to follow the tibia.", "the axial is kept straight on the axial — tilt it on the sagittal or coronal with the ⟳ handles to follow the femur."),
 ('var P=POS[S.pos||"straight"];\n  return [ "Request checked: <b>MRI right tibia + fibula</b> — runner, 6 weeks of diffuse shin pain, X-rays normal; query stress reaction / fracture anywhere along the shaft · MR safety questionnaire done, metal removed",\n           "Supine, <b>feet first</b> — only the legs go into the bore, the head stays near the entrance",\n           P.fit,\n           "<b>Two flexible arrays</b> wrapped round the lower leg, overlapping, <b>knee to ankle</b> (with the table\'s posterior array) — or a dedicated long-leg / peripheral coil",\n           "<b>Skin marker</b> (oil capsule) taped over the most tender point",\n           "Straps snug, hands by the side · ear protection + call bell",\n           "Landmark laser on the coil centre (mid-shin) · sent to isocentre" ];',
  'var P=POS[S.pos||"straight"];\n  return [ "Request checked: <b>MRI right femur</b> — runner, 6 weeks of thigh and groin pain on running, X-rays normal; query stress fracture of the femoral neck or shaft · MR safety questionnaire done, metal removed",\n           "Supine, <b>feet first</b> — the head stays near the bore entrance",\n           P.fit,\n           "<b>Two flexible body arrays</b> wrapped round the thigh, overlapping, <b>hip to knee</b> (with the table\'s spine array behind) — the top one over the greater trochanter",\n           "<b>Skin marker</b> (oil capsule) taped over the most tender point",\n           "Straps snug, hands on the chest or by the side clear of the thigh · ear protection + call bell",\n           "Landmark laser on the coil centre (mid-thigh) · sent to isocentre" ];'),
 ("Keep the axial square to the tibia: the shaft leans about '+C.real.tilt+'° (the ankle sits further back than the knee). Drag a ⟳ handle on the <b>SAG</b> panel to tilt the stack to match (tilt now '+tiltOf(q)+'°).",
  "Keep the axial square to the femoral shaft. In this patient the shaft runs within about '+C.real.tilt+'° of the bore axis, so a straight axial is fine — on another patient, drag a ⟳ handle on the <b>SAG</b> or <b>COR</b> panel to tilt it (tilt now '+tiltOf(q)+'°)."),
 (" Tilt it on the '+(q===\"cor\"?\"<b>SAG</b>\":\"<b>COR</b>\")+' panel to follow the tibia (tilt now '+tiltOf(q)+'°).", " Tilt it on the '+(q===\"cor\"?\"<b>SAG</b>\":\"<b>COR</b>\")+' panel if the femur needs it (tilt now '+tiltOf(q)+'°)."),
 ("The leg lies a little rolled out, so straight won't do.", "The leg lies a little rolled out, so straight won't do — and don't line it up on the femoral neck, which points forwards (anteversion)."),
 ('railTitle.textContent="Patient set-up"; railDesc.textContent="Tibia + fibula · flexible arrays, feet first";', 'railTitle.textContent="Patient set-up"; railDesc.textContent="Femur · flexible arrays, feet first";'),
 ("How should the <b>right leg</b> lie for a 25-minute scan of the whole tibia and fibula, knee to ankle?", "How should the <b>legs</b> lie for a 30-minute scan of the whole right femur, hip to knee?"),
 ('railDesc.textContent="3-plane gradient echo · 500 mm FOV";', 'railDesc.textContent="3-plane gradient echo · 580 mm FOV";'),
 ('["FOV","500 mm · 256 matrix · 8 mm"],["Phase FOV","62 % on the sagittal + coronal (the leg is narrow)"]', '["FOV","580 mm · 256 matrix · 8 mm"],["Phase FOV","40–46 % on the sagittal + coronal (one thigh only)"]'),
 ("This study\\'s own localiser wasn\\'t stored, so these three are rebuilt from the volunteer\\'s real 3D T1 (see the credits). A 500 mm FOV only just reaches from above the knee to below the ankle.",
  "This study\\'s own localiser wasn\\'t stored, so these three are rebuilt from the volunteer\\'s real 3D T1 (see the credits). The femur is long: even 580 mm only just reaches from above the hip to below the knee."),
 ('+(d?(ok?"✓ SCANNED":"⚠ SCANNED · GAPS")', '+(d?(ok?"✓ SCANNED":"⚠ SCANNED · GAPS")'),
 ('"Knee to ankle covered"', '"Hip to knee covered"'),
 ('"“keep your leg as still as you can — this one is noisy”"', '"“keep your legs as still as you can — this one is long and noisy”"'),
 ("'<b>PROTOCOL · TIBIA + FIBULA (RIGHT)</b><div>Position: '+POS[S.pos].short+' · feet first · flexible arrays knee to ankle</div>'",
  "'<b>PROTOCOL · FEMUR (RIGHT)</b><div>Position: '+POS[S.pos].short+' · feet first · flexible arrays hip to knee</div>'"),
 ("Order matters: the <b>axial</b> goes first, square to the tibia, from above the patella to past the ankle. The <b>coronal</b> and <b>sagittal</b> are then angled on those real axial images — the coronal parallel to the back of the femoral condyles, the sagittal perpendicular — and both run the full length, knee joint to ankle joint.",
  "Order matters: the <b>axial</b> goes first, square to the femur, from above the femoral head to below the knee. The <b>coronal</b> and <b>sagittal</b> are then angled on those real axial images — the coronal parallel to the back of the femoral condyles, the sagittal perpendicular — and both run the full length, hip joint to knee joint."),
 ('" · flexible arrays knee to ankle" : "supine, feet first, arrays round the right lower leg — choose how the leg lies"', '" · flexible arrays hip to knee" : "supine, feet first, arrays round the right thigh — choose how the legs lie"'),
 ('log("MRI right tibia + fibula requested — a runner with 6 weeks of diffuse shin pain and normal X-rays; query stress reaction or fracture anywhere along the shaft, so image knee to ankle. The patient is on the table, supine, feet first, with flexible arrays wrapped round the lower leg.","sys");',
  'log("MRI right femur requested — a runner with 6 weeks of thigh and groin pain and normal X-rays; query stress fracture of the femoral neck or shaft, so image hip to knee. The patient is on the table, supine, feet first, with flexible arrays wrapped round the thigh.","sys");'),
 ('log("laser on — mid-shin landmarked.","sys");', 'log("laser on — mid-thigh landmarked.","sys");'),
 ('"in the bore: the shin sits at isocentre, the head is outside"', '"in the bore: the mid-thigh sits at isocentre"'),
 ("fast gradient echo, one slice per plane, 500 mm FOV", "fast gradient echo, one slice per plane, 580 mm FOV"),
 ('pl.fov = q==="ax" ? 180 : 500;', 'pl.fov = q==="ax" ? 210 : 560;'),
 ('vpBR.textContent="FOV "+S.plan[q].fov+" mm\\nR TIB/FIB · 3D reformat";', 'vpBR.textContent="FOV "+S.plan[q].fov+" mm\\nR FEMUR · 3D reformat";'),
 ("Demonstration only: how much of the tibia and fibula your plans cover and how well the coronal and sagittal are angled.", "Demonstration only: how much of the femur your plans cover and how well the coronal and sagittal are angled."),
 ('"Knee to ankle, square to the bone"', '"Hip to knee, square to the bone"'),
 ("The tibia and fibula should run the full height of the coronal and sagittal, knee joint to ankle joint.", "The femur should run the full height of the coronal and sagittal, hip joint to knee joint."),
 ("A routine tibia + fibula MRI pairs T1", "A routine femur MRI pairs T1"),
 ('" The marker needs the leg straight with the foot supported in neutral."', '" The marker needs the legs straight, feet together and turned slightly in."'),
 ('(the tibia leans "+C.real.tilt+"°)', '(the femur leans "+C.real.tilt+"°)'),
 ("knee to ankle in every plane, coronal and sagittal square to the knee — marker unlocked.", "hip to knee in every plane, coronal and sagittal square to the knee — marker unlocked."),
 ("One healthy adult male volunteer, right lower limb, hip to foot, multi-station 3D sagittal T1 VIBE Dixon and T2 SPACE ± fat sat (≈ 1.1 mm isotropic). The clinical request is fictional — the volunteer had no injury. ",
  "One healthy adult male volunteer, right lower limb, hip to foot, multi-station 3D sagittal T1 VIBE Dixon and T2 SPACE ± fat sat (≈ 1.1 mm isotropic) — the same leg as the MR-I Ready tibia + fibula simulator. The clinical request is fictional — the volunteer had no injury. "),
 ("cropped to the slab from ≈ 40 mm above the patella to ≈ 60 mm below the ankle joint (crop faces perpendicular to the tibia); the brightness step where two table stations join at mid-shin was flattened; the axial, coronal and sagittal series are <b>reformatted</b> from the 3D volumes (T1 = in-phase VIBE, T2 FS = SPACE fat sat) in the orientation a radiographer would plan — axial square to the tibia, coronal parallel to the posterior condyles (−11° on the axial), sagittal perpendicular; the 3-plane localiser is <b>synthesised</b> from the 3D T1 (8 mm slab, 500 mm FOV, coil shading, noise, rectangular FOV);",
  "cropped to the slab from ≈ 30 mm above the femoral head to ≈ 35 mm below the knee joint (crop faces perpendicular to the femur); the source slab ends just medial to the hip, so tissue beyond it (pelvis, groin) is blanked and the coronals use a rectangular left–right FOV; the brightness step where two table stations join above the knee was flattened; the axial, coronal and sagittal series are <b>reformatted</b> from the 3D volumes (T1 = in-phase VIBE, T2 FS = SPACE fat sat) in the orientation a radiographer would plan — axial square to the femur, coronal parallel to the posterior condyles (−11° on the axial), sagittal perpendicular; the 3-plane localiser is <b>synthesised</b> from the 3D T1 (8 mm slab, 580 mm FOV, coil shading, noise, rectangular FOV);"),
 ("    else { pl.fov=Math.max(pl.fov, 480); renderSeries(id, k, cv, pl); }", "    else { pl.fov=Math.max(pl.fov, 560); renderSeries(id, k, cv, pl); }"),
 ('var P = q==="ax" ? CONDYLES : LM.tmid, k=list[closestIn(id, list, P)];', 'var P = q==="ax" ? CONDYLES : LM.fmid, k=list[closestIn(id, list, P)];'),
 ("Math.max(HH[i]-(i===2?330:200), Math.min(HH[i]+(i===2?330:200), v))", "Math.max(HH[i]-(i===2?340:200), Math.min(HH[i]+(i===2?340:200), v))"),
]
for a2, b2 in R:
    assert a2 in s, "missing: " + a2[:90]
    s = s.replace(a2, b2)
open(p, "w", encoding="utf-8").write(s)
left = [w for w in ["tibia", "Tibia", "TIB", "ankle", "shin", "knee to ankle"] if w in s]
for w in left:
    for m in re.finditer(w, s):
        ln = s.count("\n", 0, m.start()) + 1
        print("left:", w, "line", ln, s[max(0, m.start()-50):m.start()+40].replace("\n", " "))
