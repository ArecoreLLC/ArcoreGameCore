"""Build the Horde Defense RTS design workbook for designers aged 10 to 12.

Requires python-docx. Run from any directory. Rebuilding overwrites the Word
file, so keep completed copies elsewhere. Each section is one printed page.
Reuses helpers from ../build_workbooks.py and ../build_shammyverse_sequel_workbook.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from docx.shared import Pt  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
import build_workbooks as _bw  # noqa: E402
import build_shammyverse_sequel_workbook as _sv  # noqa: E402
from build_workbooks import para  # noqa: E402
from build_shammyverse_sequel_workbook import page, setup, hint  # noqa: E402

# Extra writing room for handwriting: enlarge response boxes and table rows.
SPACE = 1.3


def box(d, label, height=.65):
    return _bw.box(d, label, height * SPACE)


def grid(d, headers, rows, widths, row_height=.5, first_col=None):
    return _sv.grid(d, headers, rows, widths, row_height * SPACE, first_col)


def rule_boxes(d):
    for label in ('WHEN something happens', '\u2193 CHECK a yes or no question',
                  'YES \u2192 What does the game do?', 'NO \u2192 What does the game do instead?'):
        box(d, label, .38)


NAME = 'Horde_Defense_RTS_Design_Workbook_Ages_10_12.docx'
PAGES = 16
DOWN = '\u2193'


def build():
    d = setup()
    d.core_properties.title = 'Horde Defense RTS Design Workbook'
    d.core_properties.subject = 'Printable RTS horde-defense game design workbook for ages 10 to 12'
    f = d.sections[0].footer.paragraphs[0]
    for r in list(f.runs):
        r.text = r.text.replace('ShammyVerse sequel  |  Game design workbook', 'Horde Defense RTS  |  Design workbook')

    # 1 Cover
    d.add_paragraph('Horde Defense RTS Workbook', 'Title')
    para(d, 'Design a real-time strategy game where you defend your base from waves of enemies', 14, True)
    para(d, 'Do one or two pages per sitting. Words, sketches, tables and numbers are all welcome. Numbers are first guesses: you will change them after playtesting.')
    para(d, 'Designer ____________________    Date ______________', 11)
    box(d, 'My game is called', .5)
    box(d, 'Draw the cover. Show your base and the horde coming.', 3.6)
    box(d, 'Pitch it in one sentence: "Build and command ___ to protect ___ from ___ until ___."', .9)

    # 2
    page(d, '1. World and story', 'Why are the enemies attacking? What are you protecting?')
    box(d, 'Theme (fantasy, space, robots, animals, something new)', .5)
    box(d, 'What is your base, and why does it matter? (Your base has a core that must survive.)', .8)
    box(d, 'Who or what are the enemies, and what do they want?', .8)
    box(d, 'What is the one thing that makes your game different from other defense games?', .8)
    box(d, 'How does the game end if you win? If you lose?', .8)
    hint(d, 'Keep it fun and cartoonish: enemies poof or tumble away.')

    # 3
    page(d, '2. Hero and controls', 'A strategy game gives the player many choices. Controls must stay simple.')
    box(d, 'Who is your hero? Draw them and list their special move.', 2.2)
    grid(d, ['Player action', 'How do you do it? (click, tap, drag)'], 5, [2.6, 4.4], .5,
         ['Select units', 'Move or attack', 'Build', 'Send next wave early', 'Pause and plan'])
    box(d, 'What would make the controls confusing? How will you avoid it?', .9)

    # 4
    page(d, '3. Pillars and the goal', 'Pillars are the promises your game keeps. Choose three.')
    box(d, 'Pillar 1 (example: "Prepare, then react")', .6)
    box(d, 'Pillar 2 (example: "Every choice has a cost")', .6)
    box(d, 'Pillar 3 (example: "Fair losses")', .6)
    box(d, 'What does the player do over and over? Why is it fun?', .8)
    box(d, 'How many waves to win? How many minutes should a match take? (Try 10 waves, 12 to 20 minutes.)', .8)
    box(d, 'What makes the player lose? What will they learn when they lose?', .8)

    # 5
    page(d, '4. Resources', 'Pick two or three. Short supply forces choices.')
    grid(d, ['Resource name', 'Where does it come from?', 'What is it spent on?', 'Why does it exist?'], 3, [1.4, 1.9, 1.9, 1.8], .85)
    grid(d, ['Starting stock', 'Amount'], 3, [3.5, 3.5], .4, ['Resource 1', 'Resource 2', 'Resource 3'])
    box(d, 'A worker gathers ___ per ___ seconds and costs ___ . Is that fast enough to matter before wave 1?', .8)
    box(d, 'Where are the safe resources and the risky resources on your map?', .8)

    # 6
    page(d, '5. Buildings and towers', 'Design 4 to 6. Give each a clear job and a weakness.')
    grid(d, ['Name', 'Cost', 'Job', 'Strong against', 'Weak against'], 6, [1.5, 1.0, 1.9, 1.3, 1.3], .62)
    box(d, 'Draw your favorite tower. Show how it attacks.', 2.0)

    # 7
    page(d, '6. Units you command', 'Keep it to 3 or 4 types, plus a hero.')
    grid(d, ['Unit', 'Cost', 'Role', 'Health', 'Counter note'], 5, [1.3, 1.0, 2.1, .9, 1.7], .65)
    box(d, 'Draw each unit so a player can tell them apart at a glance (shape, not only color).', 2.0)
    box(d, 'Army size limit and why', .6)

    # 8
    page(d, '7. Costs check', 'Do the math before building anything.')
    para(d, 'Add up what a player can afford before wave 1 and wave 3.', 12)
    grid(d, ['Question', 'My answer'], 5, [3.8, 3.2], .55,
         ['Starting resources total', 'Cheapest useful defense costs', 'Gathered before wave 1 (prep time x rate)',
          'Can the player afford 2 things by wave 1?', 'Is anything too cheap or too strong?'])
    box(d, 'Upgrade paths: pick one tower and give it two upgrade choices (A or B). What is each good for?', 1.3)
    box(d, 'What do you unlock every two waves so the game keeps changing?', .8)

    # 9
    page(d, '8. The horde: enemy types', 'Design 4 to 6, plus a boss.')
    grid(d, ['Enemy', 'Health', 'Speed', 'What it does', 'First wave'], 6, [1.4, .9, .9, 2.8, 1.0], .62)
    box(d, 'Draw your enemies in a row, small to big.', 1.7)

    # 10
    page(d, '9. Counters and the boss', 'A counter system: every enemy has an answer, and no answer works against everything.')
    box(d, 'Draw your counter triangle: A beats B, B beats C, C beats A. What are A, B and C in your game?', 2.4)
    box(d, 'Boss name and drawing', 1.5)
    box(d, 'Boss warning: how does the player know a big attack is coming? (Red circle, sound, delay?)', .8)
    box(d, 'How do players beat the boss using what they learned in waves 1 to 4?', .8)

    # 11
    page(d, '10. Wave script', 'Plan the order. Each wave should teach one thing.')
    grid(d, ['Wave', 'Enemies and numbers', 'Prep time', 'What it teaches'], 10, [.7, 3.1, .9, 2.3], .5,
         [str(i) for i in range(1, 11)])

    # 12
    page(d, '11. Map', 'Plan where enemies enter and where you fight.')
    box(d, 'Draw your map. Mark: base core, enemy gates, resources, 2 good defense spots, 1 risky tempting spot, choke points.', 4.6)
    box(d, 'Is there always a path for enemies? (If walls fully block it, what happens?)', .7)
    box(d, 'How does the player see where each wave comes from before it arrives?', .7)

    # 13
    page(d, '12. Rules', 'Trigger, condition, action. Example: WHEN an enemy enters range, CHECK is it nearest? YES fire, NO keep targeting.')
    for n in (1, 2):
        para(d, f'Rule {n}', 12, True)
        rule_boxes(d)

    # 14
    page(d, '13. Paper playtest', 'Use coins, tokens, slips for resources and one die. One turn is 5 seconds.')
    grid(d, ['Wave', 'What I built', 'What broke', 'How it felt'], 6, [.7, 2.3, 2.0, 2.0], .6,
         ['1', '2', '3', '4', '5', '6'])
    box(d, 'Could the tester explain what each enemy does after wave 3?', .7)
    box(d, 'Did the tester make a plan without help?', .7)

    # 15
    page(d, '14. Balance and changes', 'Change one number at a time and write down why.')
    for lab in ('A player who builds nothing loses by wave 3. True?', 'A player who builds only one tower type loses by wave 6. True?',
                'Which choice did every tester pick? Is it too strong?', 'Top three problems from playtest'):
        box(d, lab, .7)
    grid(d, ['What I changed', 'Old number', 'New number', 'Result'], 3, [2.8, 1.1, 1.1, 2.0], .55)

    # 16
    page(d, '15. Build plan and helper notes', 'Build the smallest game that is fun, then add.')
    box(d, 'Smallest game: 1 map, 1 resource, 2 towers, 2 enemies, 3 waves. What is yours?', .8)
    box(d, 'What gets added next? Then next?', .8)
    box(d, 'Where will it run first (PC, tablet, both)?', .5)
    para(d, 'Helper notes', 13, True)
    para(d, 'Ask "why" rather than telling. Keep scope small. Check costs are never free and that losses have a visible cause. '
            'See DESIGN_PACKET.md for sample numbers, schedule and balance checks. Nothing here is implemented or playtested yet. '
            'Use first names or initials only for testers.', 11)

    path = HERE / NAME
    d.save(path)
    print(path.name)


if __name__ == '__main__':
    build()
