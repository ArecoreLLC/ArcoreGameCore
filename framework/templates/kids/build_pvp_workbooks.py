"""Build two three-page PvP worksheet sets. Requires python-docx.

Rebuilding replaces blank templates; save completed worksheets elsewhere.
"""
from pathlib import Path

from build_phase_workbooks import setup
from build_workbooks import box, flow, heading, para

ROOT = Path(__file__).resolve().parent / 'player-vs-player'


def make(young):
    band = 'Grades K–3' if young else 'Grades 4–12'
    d = setup(band, 'Player vs Player Game Design', 0 if young else 4)
    para(d, 'Make a game where people play against each other. Characters are optional!')
    para(d, 'Try a game with tiles, cards, shapes, paddles, words, puzzles, or racing pieces.', 11)
    para(d, 'Designer ____________________    Date ______________', 11)
    if young:
        para(d, 'Draw, point, or tell. A helper can read and write your words.', 11)
    else:
        para(d, 'Use words or drawings. Start with the main prompts; the stretch tasks are optional.', 11)
    heading(d, '1. My game idea')
    box(d, 'What is your game called?', .4)
    box(d, 'How many people play? Alone against each other, or in teams?', .5)
    box(d, 'What does each player move, choose, or control?', .65)
    box(d, 'Draw the board, table, or screen. Show where each player starts.', 1.8)
    box(d, 'How do you win? What if nobody wins or the score is tied?', .65)

    d.add_page_break()
    heading(d, '2. Our rules')
    if young:
        box(d, 'What do we need to play? How do we set it up?', .7)
        box(d, 'Who goes first? Do we take turns or play at the same time?', .6)
        box(d, 'What can you do on your turn or while playing?', .7)
        box(d, 'How do you get points or get closer to winning?', .6)
        box(d, 'What happens if someone tries a move that is not allowed?', .6)
        box(d, 'How do we give both players a fair chance?', .65)
        box(d, 'How does the game stop? How do we start a new game?', .65)
        para(d, 'Try it: show one turn or one short round with paper pieces.', 12)
    else:
        box(d, 'List materials, starting positions, resources, and what each player can see.', .7)
        box(d, 'Turn order or simultaneous play? Define legal actions and their limits.', .7)
        box(d, 'How are points or progress tracked? When does a round or match end?', .7)
        box(d, 'Resolve ties, simultaneous scores, illegal moves, and a player who cannot move.', .8)
        box(d, 'What meaningful choice can each player make? How can an opponent respond?', .7)
        box(d, 'What keeps the first player or one strategy from always winning?', .7)
        para(d, 'Optional stretch: explain how luck, hidden information, or different starting abilities affect fairness. How could you test that?', 11)
        box(d, 'Stretch notes / how to reset the game', .6)

    d.add_page_break()
    heading(d, '3. Try a rule and improve it')
    para(d, 'Example: two players take turns placing one tile in an empty square. First to make a row of three wins; a full board with no row is a tie.', 11)
    flow(d, 'A player chooses a square', 'Is the square empty?',
         'Place one tile; check for a win or tie; otherwise switch turns',
         'Keep the board and turn unchanged; choose another square')
    para(d, 'Make your own rule. Fill in both answers.', 11, True)
    box(d, 'WHEN: What happens first?', .36)
    box(d, 'CHECK: Ask a yes or no question.', .36)
    box(d, 'YES → What happens next?', .36)
    box(d, 'NO → What happens instead?', .36)
    heading(d, 'Play with someone')
    para(d, ('Try both answers to your rule. Play again and swap who starts. Try a tie. '
             'Can both players explain how to win?') if young else
         ('Test both rule paths, a tie, and an illegal move. Play several rounds, swapping '
          'starting positions or roles. Record who started and who won; a few games are clues, not proof of balance.'), 11)
    box(d, 'What happened? Was anything confusing or unfair?' if young else
        'Results: who started / who won / choices used / confusing or unfair moments', .65)
    box(d, 'Change one thing. Play again. Did it help?', .55)
    assert len(d.tables) == 18
    name = 'Grades_K-3' if young else 'Grades_4-12'
    path = ROOT / f'{name}_Player_vs_Player_Workbook.docx'
    d.save(path)
    print(path.name)


if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    for young in (True, False):
        make(young)
