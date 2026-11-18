import type {Media} from './types';

export function iterationLabel(media: Media): string {
 const tag=media.iteration;
 if(!tag)return 'Iteration unknown';
 const revision=tag.revision?.slice(0,8)||(tag.status==='no-commit'?'No commits yet':'Git unavailable');
 const state=tag.modified===true?'modified':tag.modified===false?'clean':'state unknown';
 return `${tag.observed_at.slice(0,10)} · ${revision} · ${state} (at import)`;
}
