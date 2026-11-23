import type {Game} from './types';
export const LANGUAGES:Record<string,string>={cpp:'C++',csharp:'C#',gdscript:'GDScript',python:'Python',typescript:'TypeScript',javascript:'JavaScript',rust:'Rust'};
export function gameLanguages(game:Pick<Game,'engine'|'languages'>):string[]{
 if(game.languages)return game.languages;
 const value=game.engine.toLowerCase(),result:string[]=[];
 for(const [term,id] of [['c++','cpp'],['c#','csharp'],['gdscript','gdscript'],['python','python'],['typescript','typescript'],['javascript','javascript'],['rust','rust']])if(value.includes(term))result.push(id);
 return result;
}
export function examplesFromGuide(text:string):{language:string;code:string}[]{
 return [...text.matchAll(/```([^\n]*)\r?\n([\s\S]*?)```/g)].slice(0,6).map(m=>({language:m[1].trim(),code:m[2].trim()}));
}
export type ModuleEntry={key:string;name:string;state:string;reuse:string;engine:string;guide:string;languages:string[];capability_ids:string[];source_project_ids:string[];source_entry?:{limitations?:string;validation_note?:string;version?:string;bundle_version?:string;files?:string[];source?:string;consumer_paths?:string[];tests?:string[];dependencies?:string[];review_decision?:string}};
export type ModuleResults={entries:ModuleEntry[];total:number;next_offset:number|null;capabilities:string[]};
export const REUSE:Record<string,string>={reusable:'Reusable source', 'game-specific':'Game-specific · not extracted',legacy:'Legacy source · review needed'};
