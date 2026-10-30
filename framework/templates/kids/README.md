# Printable game design workbooks

Four separate editable Word documents per grade, from kindergarten through grade 10, for 44 documents total. Print on US Letter paper at actual size. The initial design workbook has three pages; each phase-specific worksheet has two. Each document includes creative prompts, drawing space, an example trigger/condition/action diagram with yes and no paths, a blank rule to design, and a paper playtest reflection.

These are flexible creative activities, not curriculum standards or assessments. Choose a workbook by the child's comfort with reading, writing, and game rules. Children can draw, dictate, or use extra paper at any level. Use one page at a time if that suits the child.

## Choose a phase and grade

- **Initial design:** start a game with a story outline, world map, player actions, and basic rules. These are the original game design workbooks.
- **New features:** add one behavior to an existing game, plan its smallest version, and identify what must keep working.
- **New level design:** plan a setting, story purpose, route, completion goal, obstacles, and ways to retry.
- **Character design:** describe a character's role, motivation, appearance, movement, abilities, limits, and reactions.

| Grade | Initial design | New features | New level design | Character design |
|---|---|---|---|---|
| Kindergarten | [Word](Kindergarten_Game_Design_Workbook.docx) | [Word](new-features/Kindergarten_New_Feature_Design.docx) | [Word](new-levels/Kindergarten_New_Level_Design.docx) | [Word](characters/Kindergarten_Character_Design.docx) |
| 1 | [Word](Grade_01_Game_Design_Workbook.docx) | [Word](new-features/Grade_01_New_Feature_Design.docx) | [Word](new-levels/Grade_01_New_Level_Design.docx) | [Word](characters/Grade_01_Character_Design.docx) |
| 2 | [Word](Grade_02_Game_Design_Workbook.docx) | [Word](new-features/Grade_02_New_Feature_Design.docx) | [Word](new-levels/Grade_02_New_Level_Design.docx) | [Word](characters/Grade_02_Character_Design.docx) |
| 3 | [Word](Grade_03_Game_Design_Workbook.docx) | [Word](new-features/Grade_03_New_Feature_Design.docx) | [Word](new-levels/Grade_03_New_Level_Design.docx) | [Word](characters/Grade_03_Character_Design.docx) |
| 4 | [Word](Grade_04_Game_Design_Workbook.docx) | [Word](new-features/Grade_04_New_Feature_Design.docx) | [Word](new-levels/Grade_04_New_Level_Design.docx) | [Word](characters/Grade_04_Character_Design.docx) |
| 5 | [Word](Grade_05_Game_Design_Workbook.docx) | [Word](new-features/Grade_05_New_Feature_Design.docx) | [Word](new-levels/Grade_05_New_Level_Design.docx) | [Word](characters/Grade_05_Character_Design.docx) |
| 6 | [Word](Grade_06_Game_Design_Workbook.docx) | [Word](new-features/Grade_06_New_Feature_Design.docx) | [Word](new-levels/Grade_06_New_Level_Design.docx) | [Word](characters/Grade_06_Character_Design.docx) |
| 7 | [Word](Grade_07_Game_Design_Workbook.docx) | [Word](new-features/Grade_07_New_Feature_Design.docx) | [Word](new-levels/Grade_07_New_Level_Design.docx) | [Word](characters/Grade_07_Character_Design.docx) |
| 8 | [Word](Grade_08_Game_Design_Workbook.docx) | [Word](new-features/Grade_08_New_Feature_Design.docx) | [Word](new-levels/Grade_08_New_Level_Design.docx) | [Word](characters/Grade_08_Character_Design.docx) |
| 9 | [Word](Grade_09_Game_Design_Workbook.docx) | [Word](new-features/Grade_09_New_Feature_Design.docx) | [Word](new-levels/Grade_09_New_Level_Design.docx) | [Word](characters/Grade_09_Character_Design.docx) |
| 10 | [Word](Grade_10_Game_Design_Workbook.docx) | [Word](new-features/Grade_10_New_Feature_Design.docx) | [Word](new-levels/Grade_10_New_Level_Design.docx) | [Word](characters/Grade_10_Character_Design.docx) |

Start with initial design when inventing a game. Once a small playable version exists, use the other worksheets whenever a new idea arises. Level and character design can also happen during initial planning; use the sheets in the order that helps the child express the idea.

## Ages roughly 5 to 9

| Workbook | Focus |
|---|---|
| [Kindergarten](Kindergarten_Game_Design_Workbook.docx) | Draw and tell a character, place, problem, and ending |
| [Grade 1](Grade_01_Game_Design_Workbook.docx) | Beginning, middle, and end |
| [Grade 2](Grade_02_Game_Design_Workbook.docx) | A goal and a helpful choice |
| [Grade 3](Grade_03_Game_Design_Workbook.docx) | Clues and consequences |
| [Grade 4](Grade_04_Game_Design_Workbook.docx) | A quest with clear rules |

## Ages roughly 10 to 15

| Workbook | Focus |
|---|---|
| [Grade 5](Grade_05_Game_Design_Workbook.docx) | Choices that change the story |
| [Grade 6](Grade_06_Game_Design_Workbook.docx) | A repeatable gameplay loop |
| [Grade 7](Grade_07_Game_Design_Workbook.docx) | Characters and changing states |
| [Grade 8](Grade_08_Game_Design_Workbook.docx) | Branching stories that reconnect |
| [Grade 9](Grade_09_Game_Design_Workbook.docx) | Systems with narrative consequences |
| [Grade 10](Grade_10_Game_Design_Workbook.docx) | A small game with a testable design goal |

## Working together

Let the child choose the hero, problem, and solution. Record their words before suggesting changes. A parent or development partner can turn the completed map and rules into implementation tasks in the [project brief](../PROJECT_BRIEF.md). Keep the original worksheet so the child can compare the playable result with their design. Use the [iteration record](../ITERATION_RECORD.md) to record what changed after playtesting.

No game engine is required. Start with a paper map and a coin as the player. Act out each rule, including both answers to the condition. Ask what the tester did, then change one thing and try again.

## Editing and rebuilding

Edit the Word files directly for a one-off activity. To change the reusable set, update `LEVELS` or the layout in [build_workbooks.py](build_workbooks.py) and run it with Python and `python-docx`. Rebuilding replaces the generated Word files; copy completed worksheets elsewhere first. The examples are generic and can later be tailored to the family's own game development contributions.

Run [build_phase_workbooks.py](build_phase_workbooks.py) to regenerate the 33 feature, level, and character documents. It imports the initial workbook's grade data and drawing/diagram helpers. Each grade has its own example rules and design challenges; younger grades use larger text and invite adult transcription.

[verify_in_word.ps1](verify_in_word.ps1) opens the generated files read-only in Microsoft Word, checks page counts, and exports temporary PDFs to a specified QA folder. It requires installed Microsoft Word. Preview files are not part of the workbook set.

To verify the phase documents, use `-Recurse -FilePattern '*_Design.docx'` along with `-OutputDirectory`. To verify all 44 documents, use `-Recurse` with the default file pattern.
