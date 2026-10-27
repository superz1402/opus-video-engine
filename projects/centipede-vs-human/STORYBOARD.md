# STORYBOARD — "Why a Centipede Body Is Different From Human"

Method (from the Opus-5.5 prompt archive): storyboard first (@HenrygSing), pure `seek(t)`
deterministic animation (@twoclipping), one strong formal idea per scene + verification
loops (@AstroTheWizard), draw(f) purity (@0xKarmi).

- Format: 1920×1080, 30 fps, single self-contained HTML, Canvas 2D, pure function of time.
- Voice: Sonia via Actions (blocked — see BUILD-REPORT) → fallback Kokoro `af_heart`, one WAV per scene line; scene boundaries = measured line timings + 0.35 s breath gaps.
- Design system: deep ink-teal background (#0d2226) / parchment panels; centipede in amber-green (#9fd356 → #2e933c gradient segments), human in warm coral (#ff8c69) + slate. One accent per organism, used consistently in every diagram. Type: Oswald/Archivo-style condensed for count-ups, clean sans for labels. Every scene: the two body plans side by side or in direct visual rhyme.

## Script (narration, ~220 words ≈ 85 s) + scenes

### S1 — HOOK · "Not a small human" (legs count-up)
- **Picture:** A drawn centipede (21 segments) ripples across frame in a metachronal leg wave; a counter ticks leg pairs 15 → 21 → 23 … 191, always odd, each tick flashing the number plate; it settles on "21 PAIRS". Right side: a minimal human figure stands on "1 PAIR".
- **On-screen text:** title slam "NOT A SMALL HUMAN." / counter "LEG PAIRS: always ODD" / "HUMAN: 1 PAIR".
- **Narration:** "A centipede is not a tiny human with more legs. It's a different body plan — and it starts with the legs. Fifteen pairs. Twenty-one. Sometimes over a hundred. Always odd. You have one pair."
- **Transition:** counter slams to a full-body diagram; camera push into the trunk → S2.

### S2 — SEGMENTS · "One module, repeated"
- **Picture:** The centipede straightens into a diagram; segments light up one by one like train carriages, each stamped with a small "1 PAIR" tag; a "+1 segment" growth beat adds a new rear segment that unfurls legs. Human side: body divided into 3 labelled zones (HEAD / TRUNK / LIMBS) that glow as single blocks — "a few specialised parts".
- **On-screen text:** "THEM: one module × N" vs "YOU: specialised regions".
- **Narration:** "Its trunk is one module repeated: segment, legs, segment, legs — more added as it grows. Yours is the opposite idea: a few specialised parts, each built for one job."
- **Transition:** camera dives to the head → S3.

### S3 — WEAPONS · "The fangs are legs"
- **Picture:** Close-up of the centipede head; the first appendage pair highlights, morphs (draw-on) from leg shape into curved venom claws (forcipules) with a venom drop; a dotted "LEG → CLAW" evolution arrow. Human side: an arm silhouette; its hand stays a hand — a flat "✗ never" stamp.
- **On-screen text:** "FORCIPULES = modified LEGS" / "Your arms never became weapons."
- **Narration:** "Even its weapons are legs. The venom fangs behind its head are the first pair of legs, remodelled into claws. No human arm ever did that."
- **Transition:** head fades to X-ray; the nerve cord lights → S4.

### S4 — NERVOUS SYSTEM · "A chain of little brains"
- **Picture:** X-ray centipede: ventral nerve cord draws itself on, ganglion nodes (one per segment) pulse in sequence and the legs ripple in answer — decapitated-head callout "legs keep stepping". Human X-ray: one big brain node + single spinal cord, signals travel down from the top only.
- **On-screen text:** "THEM: a ganglion per segment" / "YOU: one brain, one cord".
- **Narration:** "No single brain runs the show. A centipede's nerve cord is a chain of small clusters — one per segment — so legs keep stepping on local orders. You run everything from one brain, down one cord."
- **Transition:** cord fades; side pores blink open → S5.

### S5 — BREATHING · "No lungs"
- **Picture:** Centipede flank close-up: spiracle pores open along the side; air particles stream in and branch through a tracheal tree directly to tissue cells. Human side: air flows nose → trachea → lungs; red blood cells pick up O₂ and carry it away. Centipede blood cells pass the tubes by, empty — an "O₂ carried by blood: NONE" tag.
- **On-screen text:** "THEM: spiracles → tracheae → tissue" / "YOU: lungs + blood".
- **Narration:** "It has no lungs. Air enters through pores along its sides, into branching tubes that deliver oxygen straight to the tissues — its blood carries none. Your lungs and blood do both jobs together."
- **Transition:** particles converge into the dorsal line → S6.

### S6 — HEART · "A tube, not a pump"
- **Picture:** Full-body diagram: the centipede's dorsal heart tube lights along its whole length and a pulse wave travels rear-to-front; human side: one heart icon beats in place, 4 chambers flashing in pairs.
- **On-screen text:** "THEM: a heart as long as the body" / "YOU: one pump, 4 chambers".
- **Narration:** "Its heart is a tube as long as its body, pulsing in waves. Yours is one fist-sized pump with four chambers."
- **Transition:** pull back to full bodies, heads highlighted → S7.

### S7 — SENSES · "It feels its way"
- **Picture:** Centipede head: tiny ocelli dots dim to near-black, while the antennae sweep and light up with radiating touch-rings on contact. Human head: big eyes with a vision cone lighting the scene.
- **On-screen text:** "THEM: antennae first" / "YOU: eyes first".
- **Narration:** "Many centipedes are nearly blind — simple eyespots, or none at all. They read the world through their antennae. You navigate by sight; it navigates by touch."
- **Transition:** both full bodies return, shrink to icons → S8.

### S8 — CLOSE · "Two engineering philosophies"
- **Picture:** The two diagrams face off across a centre line: left, the centipede unrolls segment by segment (stamp: "REPEAT THE MODULE"); right, the human diagram assembles from specialised blocks (stamp: "CENTRALISE & SPECIALISE"). Both stamps slam; final line types on.
- **On-screen text:** "Neither is a draft of the other."
- **Narration:** "Two engineering philosophies. Ours: centralise and specialise. Theirs: repeat one simple module, and let every copy do everything. Neither is a draft of the other."
- **Transition:** hold, fade to title card: "WHY A CENTIPEDE IS NOT A SMALL HUMAN — filed under: different plans."

## Fact discipline
- Leg pairs: centipedes always have an **odd** number of leg-bearing segment pairs — 15 to 191 pairs across species (e.g. house centipede 15, many scolopendrids 21/23, geophilomorphs up to 191). Sources: Lewis, *The Biology of Centipedes* (Cambridge UP, 1981); Brusca & Brusca, *Invertebrates*.
- Forcipules: modified first trunk appendages (legs) housing the venom gland — standard chilopod anatomy (Lewis 1981).
- Nerve cord: ventral, with a ganglion per segment; segmental autonomy of stepping is documented in chilopod neuroethology — script hedges to "legs keep stepping on local orders" (no decapitation claim on screen).
- Tracheae: spiracles open into tracheal tubes delivering O₂ to tissues; chilopod hemolymph lacks respiratory pigments / does not transport oxygen (unlike horseshoe crabs/spiders with hemocyanin — centipedes specifically: no O₂ transport role).
- Heart: dorsal vessel, a long tube with ostia, peristaltic waves — standard myriapod anatomy.
- Eyes: simple ocelli; many species (esp. geophilomorphs) eyeless; antennae are the dominant sense organs.
