import {describe,it,expect} from 'vitest';
import {iterationLabel} from '../src/iteration';
import type {Media} from '../src/types';
describe('screenshot iteration labels',()=>{
 it('keeps legacy captures unknown',()=>expect(iterationLabel({} as Media)).toBe('Iteration unknown'));
 it('labels the observation as import time and distinguishes unknown state',()=>{
  const media={iteration:{observed_at:'2026-11-13T12:00:00Z',basis:'import',revision:'123456789abcdef',modified:true,status:'available'}} as Media;
  expect(iterationLabel(media)).toBe('2026-11-13 · 12345678 · modified (at import)');
  media.iteration!.modified=null;
  expect(iterationLabel(media)).toContain('state unknown');
 });
});
