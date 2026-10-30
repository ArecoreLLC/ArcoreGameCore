"""Build the printable grade-level Word workbooks with python-docx."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
# Grade labels guide prompt complexity; these are not curriculum standards.
LEVELS = [
('Kindergarten', 'Draw and tell', 'Who is your hero?', 'Where does your hero play?', 'What does your hero want to find?', 'What is in the way?', 'Who can help?', 'How does the adventure end?', 'Touch a gate', 'Have a star?', 'Open the gate', 'Show a star picture', 'Draw one thing the player can touch.', 'Point to the start. Move a paper hero to the finish.', 'Ask a helper to read. Draw, point, or tell your answers. A helper can write your words.'),
('Grade 1', 'Beginning middle and end', 'What is your hero called?', 'Where does the story begin?', 'What does your hero want?', 'What goes wrong in the middle?', 'What can your hero try?', 'What happens at the end?', 'Touch a bridge', 'Have a plank?', 'Fix the bridge', 'Show the missing plank', 'Draw a helpful object and tell what it does.', 'Move a paper hero. Tell a helper what happens first, next, and last.', 'Draw or write short answers. Tell a helper any words you want them to write.'),
('Grade 2', 'A goal and a helpful choice', 'Who is your hero and what do they like?', 'What is special about this place?', 'Who needs help and why?', 'What stops your hero?', 'What choice helps solve the problem?', 'How is the place different at the end?', 'Meet a lost friend', 'Have a map?', 'Show the way home', 'Ask the player to find a map', 'Draw two paths. Choose one and say why your hero takes it.', 'Ask someone to follow your map without telling them where to go.', 'Use words, pictures, or both. Plan one small adventure you can act out with paper pieces.'),
('Grade 3', 'Clues and consequences', 'What makes your hero interesting?', 'What clue makes this world feel mysterious?', 'What must the player discover?', 'What obstacle hides the answer?', 'How does a clue help the player choose?', 'What does the hero learn?', 'Examine a stone door', 'Have both clues?', 'Reveal the hidden room', 'Point toward the missing clue', 'Place two clues on your map. Explain how each helps.', 'Test the door with no clues, one clue, and both clues.', 'Plan a short adventure. Use a clue to connect your story to a game rule.'),
('Grade 4', 'A quest with clear rules', 'What strength and weakness does your hero have?', 'What rule makes your world different?', 'What quest matters to someone in this world?', 'How does the obstacle test the hero?', 'What must the player do before the final challenge?', 'How does the ending show what changed?', 'Use the shrine', 'Have 3 crystals?', 'Spend 3 crystals and restore the garden', 'Show how many crystals are missing', 'Add a safe practice area and a final challenge.', 'Try the shrine with 2 crystals and 3 crystals. Try it again after success.', 'Create one quest with a beginning, a challenge, and a finish. Keep the first version small.'),
('Grade 5', 'Choices that change the story', 'What does your hero want and what do they need?', 'Which world detail affects how people behave?', 'What problem gives the player a reason to act?', 'What two choices could solve the problem?', 'How does each choice change what happens next?', 'How can both endings show the result of a choice?', 'Speak to the keeper', 'Helped the village?', 'Offer the forest route', 'Offer a task to earn trust', 'Draw a choice with two routes and label the consequence of each.', 'Play both choices. Check that the ending remembers the chosen route.', 'Design a short branching quest. Give each choice a visible consequence.'),
('Grade 6', 'A repeatable gameplay loop', 'What motivates your main character?', 'What world rule creates a useful limit?', 'What short mission introduces the larger problem?', 'How does the challenge grow over three attempts?', 'What reward helps the next attempt?', 'What changes after the mission is complete?', 'Enter the workshop', 'Have 2 parts and power on?', 'Spend 2 parts and build a tool', 'Show which requirement is missing', 'Map explore, collect, build, and return. Mark where the loop ends.', 'Test each requirement separately, then both together. Check parts are spent once.', 'Connect the story to a repeatable loop. Plan a paper prototype before choosing an engine.'),
('Grade 7', 'Characters and changing states', 'Which belief drives your main character?', 'How does the setting challenge that belief?', 'What event forces a decision?', 'Which character wants a different outcome?', 'What action changes their relationship?', 'How does the ending reflect that relationship?', 'Talk to the guide', 'Trust is at least 2?', 'Set guide state to ally and unlock a route', 'Keep guide cautious and offer a trust task', 'Map cautious, ally, and departed states. Label the action that changes each state.', 'Test trust below, at, and above 2. Talk again after the guide becomes an ally.', 'Track how one character or object changes state. Make those changes visible to the player.'),
('Grade 8', 'Branching stories that reconnect', 'What tension makes your protagonist act?', 'Which world detail creates competing needs?', 'What event introduces the central dilemma?', 'What does each choice cost or protect?', 'Where can the branches reconnect without erasing the choice?', 'Which earlier decision changes the final scene?', 'Enter the council room', 'Rescued the scout?', 'Scout reveals a safe route', 'Council offers a riskier route', 'Draw two branches that reconnect. Keep one consequence after they rejoin.', 'Follow both branches to the shared scene. Verify the earlier choice still matters.', 'Design a manageable branching story. Track one lasting consequence instead of expanding every scene.'),
('Grade 9', 'Systems with narrative consequences', 'What conflict exists between the hero and the community?', 'How do resources or power shape this world?', 'What player action starts the conflict?', 'Which system makes the choice difficult?', 'What short term benefit creates a later cost?', 'How does the ending reflect accumulated choices?', 'Request passage', 'Reputation >= 3 and supplies >= 2?', 'Spend 2 supplies and unlock passage once', 'Explain each unmet requirement', 'Map a resource loop. Show one story consequence of gaining or spending a resource.', 'Test thresholds, missing requirements, and a repeated request after passage unlocks.', 'Connect a small resource system to a story consequence. Define exact rules that someone else can implement.'),
('Grade 10', 'A small game with a testable design goal', 'What player role creates your intended experience?', 'How does the setting support that experience?', 'What central question drives the story?', 'Which mechanic makes the player confront that question?', 'How do two meaningful choices express different values?', 'What evidence in the ending reflects the player actions?', 'Activate the beacon', 'All relays on and beacon not activated?', 'Mark beacon activated and start the finale once', 'Show an unmet relay or indicate already active', 'Map the smallest complete experience. Mark optional scenes to cut first.', 'Test every relay combination, repeated activation, and restarting from the beginning.', 'Choose an experience you can observe in a playtest. Build the smallest complete version that can test it.'),
]

def para(d, text='', size=None, bold=False):
    p=d.add_paragraph(); r=p.add_run(text); r.bold=bold
    if size: r.font.size=Pt(size)
    return p

def heading(d,text): d.add_paragraph(text,'Heading 1')

def box(d,label,height=0.65):
    para(d,label,bold=True)
    t=d.add_table(rows=1,cols=1); t.autofit=False; t.columns[0].width=Inches(7)
    c=t.cell(0,0); c.width=Inches(7); t.rows[0].height=Inches(height)
    pr=c._tc.get_or_add_tcPr(); borders=OxmlElement('w:tcBorders')
    for edge in ('top','left','bottom','right'):
        el=OxmlElement('w:'+edge); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'5'); el.set(qn('w:color'),'999999'); borders.append(el)
    pr.append(borders)
    # Prevent a response area from splitting between pages.
    trpr=t.rows[0]._tr.get_or_add_trPr(); trpr.append(OxmlElement('w:cantSplit'))
    c.paragraphs[0].paragraph_format.space_after=Pt(0)
    spacer=para(d,'',size=2)
    spacer.paragraph_format.space_after=Pt(0)
    spacer.paragraph_format.line_spacing=Pt(2)

def flow(d,trigger,condition,yes,no):
    # Editable Word boxes with explicit directional arrows and both branches.
    for label in (f'WHEN  {trigger}', '↓', f'CHECK  {condition}', '↓', f'YES → {yes}', f'NO  → {no}'):
        p=para(d,label,11,True); p.paragraph_format.space_after=Pt(5)
        p.paragraph_format.keep_with_next=True

def make(i,data):
    grade,focus,hero,world,goal,obstacle,choice,end,trigger,condition,yes,no,maptask,test,opening=data
    d=Document(); s=d.sections[0]; s.page_width=Inches(8.5); s.page_height=Inches(11)
    s.top_margin=s.bottom_margin=Inches(.6); s.left_margin=s.right_margin=Inches(.75)
    normal=d.styles['Normal']; normal.font.name='Arial'; normal.font.size=Pt(13 if i<3 else 11)
    normal.paragraph_format.space_after=Pt(6)
    for name,size in [('Title',23),('Heading 1',17)]:
        st=d.styles[name]; st.font.name='Arial'; st.font.size=Pt(size); st.font.color.rgb=RGBColor(0,0,0)
    # Some bundled default templates carry a decorative blue title border.
    for st in d.styles:
        for border in list(st.element.iter(qn('w:pBdr'))):
            border.getparent().remove(border)
    d.core_properties.title=f'{grade} Game Design Workbook'
    d.core_properties.subject='Printable story and game design activities'
    d.core_properties.author='Arcore3dGameDesignFramework'
    d.add_paragraph(f'{grade} Game Design Workbook','Title')
    para(d,focus,14,True); para(d,opening)
    para(d,'Designer ____________________    Date ______________',11)
    heading(d,'My story')
    para(d,'Stuck? Pick a place, a character, and a surprise. For example: a floating garden, a tiny inventor, and a missing bridge.',11)
    for label in [hero,world,goal,obstacle,choice,end]: box(d,label,.44 if i<3 else .47)
    d.add_page_break()
    heading(d,'My world and what the player does')
    box(d,'Game name',.4)
    box(d,'Draw your map or screen. Mark the start, the goal, and something to interact with.',2.1)
    box(d,maptask,.72)
    if i<3:
        box(d,'What can the player do? Draw or name two moves.',.6)
        box(d,'How will the player know they reached the goal?',.6)
    else:
        box(d,'What does the player do again and again? What makes it fun?',.6)
        box(d,'How does the game show progress, success, or a chance to try again?',.6)
    para(d,'Paper prototype: use a coin or a small drawing as the player. Move it on your map and act out your rules.',11)
    d.add_page_break()
    heading(d,'My game rules')
    para(d,'A trigger starts a rule. A condition asks a yes or no question. An action is what the game does next.',11)
    flow(d,trigger,condition,yes,no)
    para(d,'Your turn. Draw arrows between your boxes. Give your question a YES path and a NO path.',11)
    box(d,'WHEN something happens',.43)
    box(d,'↓ CHECK a yes or no question',.43)
    box(d,'YES → What does the game do?',.43)
    box(d,'NO → What does the game do instead?',.43)
    heading(d,'Try it and make it better')
    para(d,test,11)
    para(d,'Try both your YES and NO paths. Do you see the result you expected?',11)
    box(d,'What did your tester do or say?',.43)
    box(d,'One thing I will change and try again',.43)
    # Useful identifier on loose printed worksheets.
    f=s.footer.paragraphs[0]; f.add_run(f'{grade}  |  Game design  |  ')
    field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); f._p.append(field)
    for r in f.runs: r.font.size=Pt(9)
    name='Kindergarten' if i==0 else f'Grade_{i:02d}'
    path=ROOT/f'{name}_Game_Design_Workbook.docx'; d.save(path); print(path.name)

if __name__=='__main__':
    for i,data in enumerate(LEVELS): make(i,data)
