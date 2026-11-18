import genreDoc from '../data/genre-taxonomy.json';

export type MainGenre = (typeof genreDoc.main_genres)[number];
export type SubGenre = (typeof genreDoc.sub_genres)[number];

export const MAIN_GENRES: MainGenre[] = genreDoc.main_genres;
export const SUB_GENRES: SubGenre[] = genreDoc.sub_genres;
export const ORTHOGONAL_FACETS = genreDoc.orthogonal_facets;

export function mainGenreById(id?: string): MainGenre | undefined {
  return MAIN_GENRES.find(g => g.id === id);
}

export function subGenreById(id?: string): SubGenre | undefined {
  return SUB_GENRES.find(s => s.id === id);
}

export function subGenresFor(mainGenreId?: string): SubGenre[] {
  if (!mainGenreId) return SUB_GENRES;
  return SUB_GENRES.filter(s => s.parent_genre === mainGenreId);
}

export function mainGenreLabel(id?: string): string {
  return mainGenreById(id)?.label || id || 'Unclassified';
}

export function subGenreLabel(id?: string): string {
  return subGenreById(id)?.label || id || '';
}

export function matchesGenreFilter(
  genre: string | undefined,
  subGenre: string | undefined,
  genreFilter: string,
  subGenreFilter: string,
): boolean {
  if (subGenreFilter) return subGenre === subGenreFilter;
  if (genreFilter) return genre === genreFilter || subGenreById(subGenre)?.parent_genre === genreFilter;
  return true;
}
