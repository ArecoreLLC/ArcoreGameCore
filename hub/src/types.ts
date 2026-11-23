export type Capability = {id:string; state:string; evidence:string};
export type Taxon = {id:string; label:string; family:string; description:string; level?:string; group?:string; parent_id?:string; acceptance?:string};
export type Mechanic = {id:string; name:string; capability:string; state:string; rules:string; sources:string; reuse_boundary:string; verification:string};
export type Provider = {provider:string; path:string; asset_id:string; version:string; description:string};
export type Iteration = {observed_at:string; basis:string; revision:string|null; modified:boolean|null; status:string};
export type Media = {iteration?:Iteration|null; id:string; project_id:string; kind:string; title:string; caption:string; alt_text:string; rights:string; credit:string; status:string; source_path:string; stored_path:string; sha256:string; created_at:string; approved_at:string|null; sort_order:number; width:number|null; height:number|null; duration_seconds:number|null; curation?:string; content_role?:string; is_thumbnail?:boolean; review_notes?:string};
export type Game = {
 languages?:string[]; module_keys?:string[];
 id:string; name:string; path:string; engine:string; dimension:string; kind:string; description:string; logic:string; reuse:string; assets:string; limitations:string;
 capabilities:Capability[]; mechanics:Mechanic[]; provider_links:Provider[]; maturity:string;
 marketing:{tagline:string; pitch:string; audience:string; release_status:string; website:string; credits:string; notes:string};
 commands:string[]; review_date:string; build_status:string; playtest_status:string;
 asset_counts:Record<string,number>; asset_file_count:number; source_file_count:number;
 evidence_files:{path:string;sha256:string}[];
 historical_checks:{id:string;status:string;command:string|null;artifact:string|null;record:string;freshness:string}[];
 media_candidates:{path:string;name:string;kind:string}[];
 subgames:{name:string;id:string;description:string;source:string;source_present:boolean;validation:string}[];
 revision:{head:string|null;dirty:boolean;note:string};
 classification?:Record<string,string>;
 variants?:{path:string;relationship:string}[];
 audit:{timestamp_utc:string;errors:string[];method:string};
};
export type FileRecord = {path:string;kind:string;bytes:number;sha256?:string;format?:string;rights?:string};
export type Library = {projects:Game[];taxonomy:Taxon[];media?:Media[];storage:string;schema_version:number};
export type MusicInstrument = {name:string;stem:string;keep:boolean};
export type SunoCandidate = {
 take:number; clip_id:string; url:string; duration_s:number;
 bpm_detected:number; key_detected:string; time_signature:number;
 bars_detected:number; sections_count:number;
 recommended_loop_start_bar?:number; recommended_loop_start_s?:number; recommended_loop_end_s?:number;
 labels?:Record<string,number>; terms?:string[]; quality_score:number;
 liked?:boolean; listen_rating?:number; listen_notes?:string; used_in_game?:boolean;
 sections?:{start_s:number;end_s:number;label:string}[];
 midi_files?:{stem:string;audio_id:string;path?:string;url?:string;tracks?:number;notes_count?:number}[];
};
export type SunoAnalysis = {
 bpm_detected:number; key_detected:string; time_signature:number;
 bars_detected:number; recommended_loop_start_bar?:number;
 recommended_loop_start_s?:number; recommended_loop_end_s?:number;
 sections?:{start_s:number;end_s:number;label:string}[];
 labels?:Record<string,number>; terms?:string[];
};
export type MusicTrack = {
 track_id:string; title:string; status:string; vocals:string; bpm:number;
 style_prompt:string; lyrics:string; instruments:MusicInstrument[];
 stems_requested:string[]; states:{state:string;section:string}[];
 suno:{
  url:string;clip_id:string;model:string;generated_at:string;
  stem_group_id?:string|null;recommended_take?:number;
  in_game_status?:string;in_game_loop_s?:number;in_game_stems?:string[];engine_asset_path?:string;
  analysis?:SunoAnalysis;candidates?:SunoCandidate[];
 };
 files:{path:string;kind?:string;sha256?:string}[]; notes:string;
};
export type RelatedSunoTrack = {
 clip_id:string; title:string; url:string; created_at?:string;
 duration_s?:number; model?:string; style?:string; liked?:boolean;
 match_confidence:'exact'|'high'|'ambiguous';
 matched_terms:string[]; match_candidates?:string[]; dismissed?:boolean;
};
export type MusicDesignRecord = {
 schema_version:number; game_id:string; name:string; scope?:string;
 status:string; exclusion_reason:string;
 recommended_archetype:string|null; recommended_setting:string; recommendation_reason:string;
 archetype:string|null; setting:string;
 sonic_alchemist_project?:string; soundcore_project?:string; modelforge_project?:string;
 related_suno_tracks?:RelatedSunoTrack[];
 tracks:MusicTrack[]; updated_at:string;
};
export type ProviderCatalogItem = {id:string;label:string;kind:string;count?:number;path:string};
export type ProviderCatalogs = Record<string,{root:string;library?:string;projects:ProviderCatalogItem[]}>;

