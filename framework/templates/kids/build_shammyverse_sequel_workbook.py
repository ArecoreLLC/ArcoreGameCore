"""Build the ShammyVerse sequel whole-game design workbook for ages 7 to 8.

Requires python-docx. Rebuilding overwrites the generated Word file, so keep
completed workbooks in a separate location. Every section is one printed page,
so pages can be handed out one at a time or copied (quests, rules, playtests).
"""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from build_workbooks import box, para, heading, flow

ROOT = Path(__file__).resolve().parent
NAME = 'ShammyVerse_Sequel_Game_Design_Workbook_Ages_7_8.docx'
PAGES = 20  # one printed page per section; checked by verify_in_word.ps1


def hint(d, text):
    return para(d, text, 11)


def grid(d, headers, rows, widths, row_height=.5, first_col=None):
    """Fill-in table: a header row plus empty rows tall enough for a child to write in."""
    t = d.add_table(rows=rows + 1, cols=len(headers)); t.style = 'Table Grid'; t.autofit = False
    for r, row in enumerate(t.rows):
        row.height = Inches(.3 if r == 0 else row_height)
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for c, cell in enumerate(row.cells):
            cell.width = Inches(widths[c])
            p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            text = headers[c] if r == 0 else (first_col[r - 1] if first_col and c == 0 else '')
            if text:
                run = p.add_run(text); run.bold = True; run.font.size = Pt(11)
    spacer = para(d, '', size=2)
    spacer.paragraph_format.space_after = Pt(0); spacer.paragraph_format.line_spacing = Pt(2)


def setup():
    d = Document(); s = d.sections[0]
    s.page_width = Inches(8.5); s.page_height = Inches(11)
    s.top_margin = s.bottom_margin = Inches(.6); s.left_margin = s.right_margin = Inches(.75)
    normal = d.styles['Normal']; normal.font.name = 'Arial'; normal.font.size = Pt(13)
    normal.paragraph_format.space_after = Pt(6)
    for name, size in [('Title', 23), ('Heading 1', 17)]:
        st = d.styles[name]; st.font.name = 'Arial'; st.font.size = Pt(size); st.font.color.rgb = RGBColor(0, 0, 0)
    d.styles['Heading 1'].paragraph_format.space_before = Pt(0)
    for st in d.styles:
        for border in list(st.element.iter(qn('w:pBdr'))): border.getparent().remove(border)
    d.core_properties.title = 'ShammyVerse Sequel Game Design Workbook'
    d.core_properties.subject = 'Printable whole-game design workbook for ages 7 to 8'
    d.core_properties.author = 'Arcore3dGameDesignFramework'
    f = s.footer.paragraphs[0]; f.add_run('ShammyVerse sequel  |  Game design workbook  |  ')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); f._p.append(field)
    for r in f.runs: r.font.size = Pt(9)
    return d


def page(d, title, intro=None):
    d.add_page_break(); heading(d, title)
    if intro: para(d, intro)


def rule_boxes(d):
    box(d, 'WHEN something happens', .38)
    box(d, '↓ CHECK a yes or no question', .38)
    box(d, 'YES → What does the game do?', .38)
    box(d, 'NO → What does the game do instead?', .38)


def build():
    d = setup()

    # 1 Cover
    d.add_paragraph('ShammyVerse Sequel Workbook', 'Title')
    para(d, 'Plan a whole new game for Poofy and friends', 14, True)
    para(d, 'This is a big book. Do one or two pages at a time. Use words, pictures, or both. A helper can read and write your words.')
    para(d, 'Designer ____________________    Date ______________', 11)
    box(d, 'My new game is called', .5)
    box(d, 'Draw the cover of your game.', 4.2)
    box(d, 'What is this game about? Say it in one sentence.', .75)

    # 2 Looking back
    page(d, '1. The first game', 'Think about the first ShammyVerse game. What should the new game remember?')
    box(d, 'My favorite thing to do in the first game', .7)
    box(d, 'My favorite place or friend, and why', .7)
    grid(d, ['Keep these 3 things in the new game'], 3, [7], .5)
    box(d, 'One thing I want to make better', .7)
    box(d, 'One brand new thing nobody has seen yet. Draw it or tell about it.', 2.3)

    # 3 Story
    page(d, '2. The big story', 'A whole game needs a big story. Small adventures fit inside it.')
    box(d, 'BEGINNING. What surprise starts the new adventure?', .95)
    box(d, 'Who needs help, and what is the big problem?', .95)
    box(d, 'MIDDLE. What makes it tricky? What does Poofy learn?', .95)
    box(d, 'END. How is the big problem solved?', .95)
    box(d, 'Draw the most exciting moment in the story.', 2.6)

    # 4 World map
    page(d, '3. The whole world', 'Draw every island and place in the new game. Give each one a name.')
    box(d, 'My world map. Mark where the game STARTS and where it ENDS.', 4.3)
    hint(d, 'Draw arrows to show how the player travels. Swim? Fly? Ride? Something new?')
    grid(d, ['Island or place', 'What is special about it?'], 5, [2.5, 4.5], .52)

    # 5 Journey
    page(d, '4. The journey', 'Put your places in order. Each place gives the player something for the next one.')
    grid(d, ['', 'Place', 'What do you do there?', 'What do you get or learn?'], 5, [.7, 1.8, 2.4, 2.1], .95,
         ['1st', '2nd', '3rd', '4th', 'Last'])
    box(d, 'Which place is easy, for learning how to play?', .6)
    box(d, 'Which place is the hardest? What makes it hard?', .6)
    hint(d, 'For each place, fill in a ShammyVerse Island Design sheet. Print one for every island.')

    # 6 Cast
    page(d, '5. Everyone in the game', 'List the friends, helpers, and troublemakers. Old friends can come back!')
    grid(d, ['Name', 'Friend, helper, or troublemaker?', 'Special move', 'Where do they live?'], 7,
         [1.5, 2.2, 1.7, 1.6], .62)
    box(d, 'Who is brand new in this game? Draw them saying hello.', 2.5)
    hint(d, 'For each new character, fill in a ShammyVerse Character Design sheet.')

    # 7 Poofy's moves
    page(d, '6. What Poofy can do', 'The player is Poofy. What can the player do in the new game?')
    grid(d, ['Moves Poofy already knows', 'Keep it? YES or NO'], 4, [5, 2], .45)
    box(d, 'A NEW move for Poofy. What is it called?', .5)
    box(d, 'Draw Poofy doing the new move.', 2.0)
    box(d, 'Where does the new move help?', .6)
    box(d, 'When does it NOT work? This keeps the game fair.', .6)
    box(d, 'How does Poofy learn it? Who teaches it?', .6)

    # 8 Helping friends
    page(d, '7. Friends who help', 'Some jobs are too big for Poofy alone. Pick a friend who comes along.')
    box(d, 'Which friend helps Poofy?', .5)
    box(d, 'What can this friend do that Poofy cannot?', .7)
    box(d, 'How does the player ask the friend for help?', .7)
    box(d, 'What does the friend need before they can help? Rest? A snack? A kind word?', .7)
    box(d, 'Draw Poofy and the friend working together.', 2.5)
    box(d, 'How does Poofy help the friend back?', .7)

    # 9 Trouble
    page(d, '8. The big trouble', 'Something makes the adventure hard. It can be a troublemaker, a storm, or a puzzle.')
    box(d, 'Who or what causes the trouble?', .6)
    box(d, 'Why? Are they grumpy, lonely, lost, or just silly?', .8)
    box(d, 'Draw the trouble.', 2.3)
    box(d, 'What does the trouble do to the islands?', .7)
    box(d, 'How do Poofy and friends fix it in a kind way?', .8)
    box(d, 'What happens to the troublemaker at the end?', .7)

    # 10 Collect
    page(d, '9. Things to find', 'Players love finding things. What can they collect in your game?')
    grid(d, ['Thing to find', 'Where is it?', 'What is it for?'], 5, [2.2, 2.2, 2.6], .62)
    box(d, 'Draw your three best things to find.', 2.2)
    box(d, 'How many does the player need to finish the game?', .55)
    box(d, 'Is there a secret one that is extra hard to find? Where?', .7)

    # 11 Quests
    page(d, '10. Quests', 'A quest is a job a friend asks you to do. A whole game needs lots of small quests.')
    grid(d, ['Who asks?', 'What do they need?', 'What is the reward?'], 7, [1.7, 3.3, 2], .72)
    box(d, 'Which quest must the player finish to win the game? Put a star next to it.', .6)
    box(d, 'Which quests are just for fun?', .6)
    hint(d, 'Need more quests? Copy this page.')

    # 12 Rules
    page(d, '11. Game rules')
    hint(d, 'A trigger starts a rule. A condition asks a yes or no question. An action is what the game does next.')
    para(d, 'Made up example', 11, True)
    flow(d, 'Poofy talks to a friend with a quest', 'Has Poofy found what they need?',
         'The friend says thank you and gives a reward', 'The friend gives a clue about where to look')
    para(d, 'Your turn. Write two rules for your game.')
    rule_boxes(d)
    para(d, '', 6)
    rule_boxes(d)

    # 13 Try again
    page(d, '12. Oops and try again', 'Good games are kind when things go wrong.')
    box(d, 'What can go wrong for Poofy? Name two things.', .8)
    box(d, 'What happens then? Where does the player start again?', .8)
    box(d, 'What does the player get to keep after an oops?', .7)
    box(d, 'When does the game remember what you did, so you can stop and play later?', .8)
    box(d, 'How can a stuck player get a hint?', .7)
    box(d, 'Draw a friend cheering Poofy on after an oops.', 2.2)

    # 14 Sounds and songs
    page(d, '13. Songs and sounds', 'Music tells the player how a place feels.')
    grid(d, ['Place', 'How does its music feel? Happy, sleepy, brave, spooky, silly?'], 4, [2.5, 4.5], .5)
    box(d, 'Write some words for a song in your game.', 1.7)
    box(d, 'Who sings it, and when?', .55)
    grid(d, ['When this happens', 'The game makes this sound'], 4, [3.5, 3.5], .5,
         ['Poofy finds something', 'A quest is finished', '', ''])

    # 15 Screen
    page(d, '14. What the player sees', 'The screen shows the player what they have and what to do next.')
    box(d, 'Draw the screen while playing. Show what the player has collected and what the quest is.', 3.2)
    box(d, 'How does the player know where to go next?', .7)
    box(d, 'Draw the very first screen, with the game name and a START button.', 2.9)

    # 16 Talk
    page(d, '15. What they say', 'Write the words your characters say. Short is best!')
    box(d, 'The first thing anyone says in the game. Who says it?', .95)
    box(d, 'What a friend says when they ask for help', .95)
    box(d, 'What a friend says when a quest is finished', .95)
    box(d, 'What the troublemaker says', .95)
    box(d, 'Something silly that makes the player laugh', .95)
    box(d, 'The last thing anyone says in the game', .95)

    # 17 Ending
    page(d, '16. The ending', 'The ending shows the player that what they did mattered.')
    box(d, 'Draw the last scene of the game.', 3.6)
    box(d, 'How do the islands look different now?', .8)
    box(d, 'How do the friends celebrate?', .8)
    box(d, 'Is there a surprise after the end? A new place? A hint about another game?', 1.2)

    # 18 Playtest
    page(d, '17. Try it on paper', 'You do not need a computer yet. Use your map and a coin or a paper Poofy.')
    hint(d, 'Ask a tester to play one quest. Read them what the friend says. Do not tell them where to go. Watch what they do.')
    box(d, 'Which quest did we try? Who was the tester?', .6)
    grid(d, ['What the tester did', 'Was it fun, tricky, or confusing?'], 4, [4, 3], .72)
    box(d, 'What made the tester smile?', .7)
    box(d, 'Where did the tester get stuck?', .7)
    box(d, 'One thing I will change and try again', .7)
    hint(d, 'Copy this page and test a different quest each time.')

    # 19 Build order
    page(d, '18. What we build first', 'A whole game is built one small piece at a time. Pick the order.')
    grid(d, ['When', 'What we build'], 4, [1.6, 5.4], 1.05,
         ['FIRST. The smallest game we can play', 'NEXT', 'LATER', 'MAYBE. Only if there is time'])
    box(d, 'The part I am most excited to play', .7)
    box(d, 'The part I want to help make myself. Drawing? Voices? Songs? Testing?', .8)
    hint(d, 'After each piece is built, play it and compare it with your pages. Then choose the next piece.')

    # 20 Helper notes
    page(d, 'For the grown-up helper')
    for text in [
        'Each page stands alone. One or two pages in a sitting is plenty; the order can follow the child\'s interest. Record their words before suggesting changes, and keep the filled-in pages so they can compare the playable game with their design.',
        'Pages 1 to 5 set the scope of the whole game: story, places, order, and cast. Pair them with the ShammyVerse Island and Character Worksheet, one copy per island and per new character.',
        'Pages 6 to 12 describe behavior: moves, companion help, obstacles, collectibles, quests, rules, and retry and saving. Each quest row and each WHEN, CHECK, YES, NO rule can become one implementation task with both paths tested.',
        'Pages 13 to 16 cover music, sound, screens, dialogue, and the ending. Pages 17 and 18 are the loop: test one quest on paper, change one thing, and agree the smallest playable version before adding more.',
        'Copy pages 10, 11, and 17 as often as needed. Nothing here is a commitment to build everything; page 18 is where the child helps choose what comes first and what can wait.',
    ]:
        para(d, text, 11)
    box(d, 'Notes', 3)

    path = ROOT / NAME; d.save(path); print(path.name)


if __name__ == '__main__':
    build()
