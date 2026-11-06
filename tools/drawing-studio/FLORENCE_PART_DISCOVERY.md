# Unprompted part category discovery

Executed 2026-11-02 on Windows CPU, eight threads, float32, the existing pinned Florence-2 Base conversion (00921df66db728a9ceb750f5eca43e5c203a2051), torch 2.10.0+cpu and transformers 4.57.6. Standalone 2D experiment at repository baseline cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc; no engine migration or scaffold changes.

Command: `tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/discover_florence_parts.py`

The model received image pixels and native task tokens only. No subject label, anatomy list, profile, filename or authored coordinates was supplied. Five sequential tasks: DETAILED_CAPTION, MORE_DETAILED_CAPTION, DENSE_REGION_CAPTION, OD, then CAPTION_TO_PHRASE_GROUNDING using the exact generated MORE_DETAILED_CAPTION text. Greedy decoding, maximum 256 new tokens, 29-second worker watchdog.

| Task | Seconds | Observed output |
|---|---:|---|
| Detailed caption | 1.761 | Jumping spider; body, eyes, legs; also erroneous arms |
| More detailed caption | 2.201 | Spider; body, eyes, eight legs, hairs; contradictory standing on all fours and smiley face in eyes |
| Dense region caption | 1.238 | One whole-spider box |
| Object detection | 1.195 | One box labeled spider |
| Ground own caption | 1.361 | Three boxes: spider, eyes, body |

Full worker lifecycle including startup, imports, cached loading, five queries, telemetry, overlay and report export: **12.666709 seconds**. One-time download and parent receipt serialization excluded. This is a single run, not a latency guarantee.

The self-generated body box [656,87,1025,340] covers the abdomen region; the eyes box [424,183,780,365] covers the eye group. No distinct head or palp category was generated. Legs were mentioned but not returned as a localized category in the self-grounding output. These visual findings were checked against the exported overlay. Mentioning eight legs does not establish that eight legs were observed or individually localized.

Conclusion: subject recognition succeeds on this sample; autonomous complete and reliable anatomical categorization does not. This does not prove failure on every subject or all possible prompts. The tested supported native tasks supply evidence that a reusable subject-family vocabulary is still useful for this drawing pipeline. Such a vocabulary can be shared across images of the same family rather than manually supplied per picture. A different model could propose categories, but those would still require validation against visible image evidence.

Artifacts: output/florence-part-discovery.json contains every prompt, raw answer, parsed answer, model revision, image hash, token counts, versions and CPU/GPU/memory samples. output/florence-part-discovery-receipt.json records the full elapsed time; output/florence-part-discovery.png compares localized results. Native location-token whitespace normalization matches the earlier tested processor compatibility fix.

Acceptance: runtime under 30 seconds PASSED; unprompted subject identification PASSED for this sample; complete anatomy category generation FAILED for this sample. No anatomy list was inserted into the discovery prompts after seeing the answers.
