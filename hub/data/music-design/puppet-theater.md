# Music design: Puppet Theater

Game: `puppet-theater` (roadmap)  
Status: **in_progress**  
Archetype: storybook-orchestral  
Setting: cloth-curtain puppet stage

Recommendation: Staging a two-minute puppet scene fits playful woodwinds, marimba, and brush snare.

## Puppet Theater - main theme (`puppet-theater-A`)

Status: generated | Vocals: none | BPM: 96

Suno: https://suno.com/song/393374d7-0b4b-43a4-ad4c-41031d281fb9 (clip `393374d7-0b4b-43a4-ad4c-41031d281fb9`, model v6 (MCP audio-create + audio-analysis), 2026-11-18T18:46:35Z)

**Suno MCP Audio Analysis (0-credit beat/key/section map)**

- Detected BPM: `195.3` | Key: `G minor` | Meter: `3/4` | Bars: `144` | Sections: `10`
- Recommended 32-bar loop window: Bar `29` (`26.425s`–`58.658s`)
- Tags / terms: `instrumental, no voice, violin, cello, clarinet, western classical, orchestral`

**Generated Takes Comparison**

| Take | Clip ID | Duration | Detected BPM | Key | Bars | Sections | Instrumental Prob | Score | URL |
|---|---|---|---|---|---|---|---|---|---|
| Take 1 **(Recommended)** | `393374d7-0b4b-43a4-ad4c-41031d281fb9` | 139.64s | 195.3 | G minor | 144 | 10 | 0.980 | 20.35 | https://suno.com/song/393374d7-0b4b-43a4-ad4c-41031d281fb9 |
| Take 2 | `a94d99bc-3890-4b5a-9f8e-5697ea2e037e` | 0.0s | 96.0 | Unknown | 0 | 0 | 0.000 | 0.00 | https://suno.com/song/a94d99bc-3890-4b5a-9f8e-5697ea2e037e |

**Style prompt**

```
Whimsical storybook chamber ensemble score, clean mix, dry studio recording, minimalist frequency separation, enchanting, curious and heartwarming, cloth-curtain puppet stage atmosphere, Piano, Clarinet, Cello, Harp, Glockenspiel, Percussion, 96 BPM, strict quantize, steady 4/4 rhythm, memorable repeating melodic motif, instrumental
```

**Instruments and Advanced Split stems**

| Instrument | Stem category | Keep |
|---|---|---|
| Piano | Piano | yes |
| Clarinet | Clarinet | yes |
| Cello | Cello | yes |
| Harp | Harp | yes |
| Glockenspiel | Glockenspiel | no |
| Percussion | Percussion | no |

Stems requested: Cello, Clarinet, Harp, Piano

**Lyrics / section structure**

```
[Instrumental]
[Tempo: 96 BPM, strict quantize, steady rhythm]

[Intro]
[Bass stem only: clean pulsing Piano, dry low-end, minimal]
[Verse 1 - Exploration Layer]
[Add percussion stem: delicate Harp arpeggios, warm Piano, pizzicato Cello]
[Pre-Chorus - Tension Build]
[Add melody stem: playful Clarinet phrase, twinkling Glockenspiel]
[Chorus - Combat Layer]
[Add combat layer: sweeping Cello melody, expressive Piano, light chamber Percussion]
[Bridge - Danger / Boss State]
[Maximum intensity: mysterious Clarinet and low Cello interplay]
[Outro]
[Strip back: bass pulse and distant drum fade out]
```

Notes: Generated 2 takes via Suno MCP (v6) & analyzed via 0-credit audio-analysis:
- Take 1 (393374d7-0b4b-43a4-ad4c-41031d281fb9): https://suno.com/song/393374d7-0b4b-43a4-ad4c-41031d281fb9 — 139.64s, detected 195.3 BPM, G minor, 144 bars, 10 sections, loop bars 29..61 (26.425s–58.658s), score=20.352
- Take 2 (a94d99bc-3890-4b5a-9f8e-5697ea2e037e): https://suno.com/song/a94d99bc-3890-4b5a-9f8e-5697ea2e037e — 0.0s, detected 96.0 BPM, Unknown, 0 bars, 0 sections, loop bars 3..35 (5.0s–85.0s), score=0.0
Selected for stem split: Take 1 (393374d7-0b4b-43a4-ad4c-41031d281fb9).

## Puppet Theater - alternate region (lofi-workshop) (`puppet-theater-B`)

Status: prompt_ready | Vocals: none | BPM: 86

**Style prompt**

```
Warm lo-fi Rhodes and tactile tabletop craft beats, clean mix, dry studio recording, minimalist frequency separation, relaxed, focused and playful, cloth-curtain puppet stage atmosphere, Electric Piano, Upright Bass, Drums, Vibraphone, Acoustic Guitar, Shaker, 86 BPM, strict quantize, steady 4/4 rhythm, different key, blended sub-archetype palette, new motif, instrumental
```

**Instruments and Advanced Split stems**

| Instrument | Stem category | Keep |
|---|---|---|
| Electric Piano | Electric Piano | yes |
| Upright Bass | Upright Bass | yes |
| Drums | Drums | yes |
| Vibraphone | Vibraphone | yes |
| Acoustic Guitar | Acoustic Guitar | no |
| Shaker | Shaker | no |

Stems requested: Drums, Electric Piano, Upright Bass, Vibraphone

**Lyrics / section structure**

```
[Instrumental]
[Tempo: 86 BPM, strict quantize, steady rhythm]

[Intro - Bass Stem Only]
[Deep pulsing Upright Bass, clean low-end drone, minimal]

[Part 1 - Add Percussion Stem]
[warm Electric Piano chords, soft Shaker groove, Upright Bass, steady 4/4 rhythm]

[Part 2 - Add Melody Stem]
[sparkling Vibraphone arpeggios, gentle fingerpicked Acoustic Guitar, high frequency separation, dry studio]

[Part 3 - Add Combat & Climax Layer]
[crisp lo-fi Drums, walking Upright Bass, bright Electric Piano hook; syncopated Vibraphone solo, tighter Drum groove]

[Outro - Strip Back]
[Sub-bass pulse and distant percussion fade out]
```

Notes: Clean Stem-Builder variation (storybook-orchestral, parent: cozy).

## Puppet Theater - late-game variation (cosmic-ambient + medieval-siege) (`puppet-theater-C`)

Status: prompt_ready | Vocals: none | BPM: 104

**Style prompt**

```
Ethereal sci-fi orbital ambient and crystalline synth score blended with Medieval castle siege orchestral and folk-warfare score, clean mix, dry studio recording, minimalist frequency separation, vast, wondrous and weightless, cloth-curtain puppet stage atmosphere, Synth Pad, Arpeggiator, Piano, Strings, Synth Bass, Bells, Brass, 104 BPM, strict quantize, steady 4/4 rhythm, darker harmony, hybrid escalation palette, motif reprised, instrumental
```

**Instruments and Advanced Split stems**

| Instrument | Stem category | Keep |
|---|---|---|
| Synth Pad | Synth Pad | yes |
| Arpeggiator | Arpeggiator | yes |
| Piano | Piano | yes |
| Strings | Strings | yes |
| Synth Bass | Synth Bass | no |
| Bells | Bells | no |

Stems requested: Arpeggiator, Piano, Strings, Synth Pad

**Lyrics / section structure**

```
[Instrumental]
[Tempo: 104 BPM, strict quantize, steady rhythm]

[Intro - Bass Stem Only]
[Deep pulsing Synth Bass, clean low-end drone, minimal]

[Part 1 - Add Percussion Stem]
[evolving Synth Pad, resonant Piano notes, soft Bells, steady 4/4 rhythm]

[Part 2 - Add Melody Stem]
[shimmering Arpeggiator pulse, deep Synth Bass swell, high frequency separation, dry studio]

[Part 3 - Add Combat & Climax Layer]
[soaring Strings over sequenced Arpeggiator and Synth Bass; urgent crystalline Bells, dramatic Synth Pad swells]

[Outro - Strip Back]
[Sub-bass pulse and distant percussion fade out]
```

Notes: Clean Stem-Builder variation (storybook-orchestral, parent: cozy).
