import {describe,it,expect} from 'vitest';
import {gameLanguages,examplesFromGuide} from '../src/moduleCatalog';
describe('module and language catalog metadata',()=>{
 it('reads historical engine labels without overwriting explicit language selections',()=>{
  expect(gameLanguages({engine:'Godot 4.7.2 / GDScript'})).toEqual(['gdscript']);
  expect(gameLanguages({engine:'Unreal / C++',languages:['cpp','python']})).toEqual(['cpp','python']);
  expect(gameLanguages({engine:'Godot / GDScript',languages:[]})).toEqual([]);
 });
 it('shows bounded guide examples as text, including CRLF',()=>{
  expect(examplesFromGuide('Guide\n```gdscript\r\nvar x = 1\r\n```')).toEqual([{language:'gdscript',code:'var x = 1'}]);
  expect(examplesFromGuide('No code')).toEqual([]);
  expect(examplesFromGuide('```text\n<script>literal</script>\n```')[0].code).toContain('<script>');
 });
});
