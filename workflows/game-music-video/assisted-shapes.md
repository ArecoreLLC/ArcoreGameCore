# Help Poofy find the shapes

Status: agreed walkthrough design, not an implemented in-game upload/editor UI.
Start with circles/ovals. Triangles and rectangles can be added later. Always offer
**Skip shapes — draw and paint** for personal artwork.

## Guided sequence

1. **Find the middle.** “Drag this line down the middle of your picture.” Place the
   vertical mirror line first. Do not assume the animal is centered on the page.
2. **Line things up.** “Drag this short line across the face or body.” Add a short
   horizontal cross-guide, with draggable position and width. It aligns eyes/ears;
   it is not a second mirror axis. Both guides remain editable.
3. **Start with a big shape.** Show an animal example's head/body guide. “Click the
   top of the oval.” Then “Now click the bottom.” Then “Click one side to make it
   wide or narrow.” Show a live preview, Back and Undo at each step.
4. **Make it fit.** “Drag your oval into place.” Give it center/edge handles for
   movement/resizing and optional rotation. A circle is simply an equal-radius oval.
5. **Try the other side.** Offer “Mirror this shape” for paired features. Reflect
   across the vertical line, then allow independent drag/resize of the copy. No
   hidden permanent symmetry constraint. Approximate symmetry is normal in drawings.
6. **Add smaller shapes.** Head/body/large ears first; eyes, nose and paws second.
   Name the parts. Do not require every contour to fit an oval or a fixed shape count.
7. **Check with Poofy.** Toggle artwork, guides and combined view; preview drawing
   order. “Do these shapes fit your picture?” Correct and save. This produces review
   evidence; a Done button is not automatic anatomical certification.

Instructions must work without hearing lyrics. Include large touch targets, zoom,
undo, active-step feedback and keyboard movement/resizing. No timed interactions.
Moving the mirror line after creating copies must not silently reposition them:
offer a re-mirror preview. The cross-guide is only a visual alignment aid.

## Existing animal examples

| Animal | Big shapes | Details / mirror guidance |
|---|---|---|
| Koala | Broad head/body, large ear circles | Nose, eyes, foot pads; best first guided example |
| Butterfly | Narrow body, upper/lower wing masses | Demonstrate mirroring while preserving hand-drawn differences |
| Red panda | Broad head, body, curled-tail mass | Muzzle, eyes, paws; tail remains asymmetric |
| Cat | Head and seated body ovals | Muzzle/paws; pointed ears do not need forced oval outlines |
| Monkey | Head/body and ear circles | Paired face-mask lobes, muzzle/paws; freeform tail |
| Unicorn | Head/body and tail mass | Profile pose: normally turn mirroring off |
| Elephant | Head/body and broad ear masses | Eyes/feet; trunk gesture may need a later optional line tool |

Show the consumer's saved references and actual reviewed construction overlays.
Do not present a generic starter oval as a reviewed fit to arbitrary personal art.

## Implementation geometry

Use the existing 1280×698 letterboxed lesson coordinates, converting pointer positions
through the view transform. Zooming must not change saved coordinates. Given top T,
bottom B, side S: center C=(T+B)/2; axis V=normalize(B−T); half-height h=|B−T|/2;
perpendicular U=(V.y,−V.x); half-width w=abs(dot(S−C,U)). Sample
`C + h*cos(t)*V + w*sin(t)*U`. This supports tilted ovals as well as upright ones.
Reject coincident top/bottom or negligible width with a friendly correction prompt.

Mirror sampled points with `x'=2*mirror_x−x`, retaining y. Drag a copy by adding its
own translation. Save mirror/cross-guide positions as separate authoring metadata,
not required drawn strokes. Main forms serialize as stage 0; small forms as stage 1.
Reference/guide edits invalidate the manifest's review fingerprints.

Acceptance checks: zoom/letterbox mapping, rotated ovals, mirror coordinates,
independent dragging, moving guides after copies exist, undo/redo, zero-size handling,
off-canvas correction, keyboard/touch controls, correct stage ordering, profile
animals without forced mirroring, and successful trace-only rendering with no shapes.
