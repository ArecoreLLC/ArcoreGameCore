# Generic consumer example

Keep the manifest beside the consumer's assets, not in GameCore:

```json
{
  "subjects": [
    {"id": "hero", "svg": "assets/hero.svg"},
    {"id": "guardian", "svg": "assets/guardian.svg"}
  ],
  "character_finish": {"exposure": 0.05, "contrast": 6, "saturation": 4, "shadows": 8, "sharpness": 6},
  "environment": true,
  "environment_finish": {"exposure": 0.15, "contrast": 8, "shadows": 10, "saturation": -5}
}
```

A subject ID names its seed, rendered folder and final atlas. All subjects use identical settings. `receipt.json` and `recipes/` retain provenance; `final/` holds runtime candidates. Review transparency, cell edges, silhouettes, shared scale and motion before copying candidates into the game. Test the exported app on the intended tablet, including reduced motion, interruption and return from practice.
