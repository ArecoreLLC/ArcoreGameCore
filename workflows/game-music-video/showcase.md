# Finished video handoff to Showcase

Use the GameCore hub MCP tool `showcase_production`, starting with
`{"operation":"tools/list","arguments":{}}`. Showcase is registered in
`shared/ecosystem.json`; agents do not need a separate Showcase MCP registration.

The Windows provider is in `../ArcoreUATFramework/ArcoreShowcase`. Its
`scripts/Start-GameCoreMCP.ps1` uses the installed backend agent environment and
the existing DPAPI-protected publishing credential. The active service runs in
Fleet, not the local source checkout. The configured local endpoint is
`http://localhost:23439/api/v1`; the Showcase desktop SSH profile or an SSH
tunnel must connect that port to the Fleet Showcase frontend. No credentials
belong in this registry, receipts, or workflow.

1. Read `youtube_status` and `youtube_manager` to select the actual connected
   channel and project policy. Channel routing is independent of video branding.
2. Call `finished_video_import` with `project_id`, an absolute MP4 `file_path`,
   an absolute `receipt_path`, and `reviewed=true` only for owner-approved media.
   The receipt records `engine` (`godot` or `unreal`), `status=passed`, real
   validation `checks` with `passed=true`, `video`, and an `artifacts` entry
   matching that video path and SHA256. Include source assembly provenance.
3. The tool verifies the checksum and imports the exact finished MP4 as a
   completed original publication. It does not invoke the branding renderer:
   no additional splash, closing card, rescale, audio mix, or re-encode.
   Repeating the same project/checksum resumes the same catalog entry.
4. Save reviewable private upload metadata using `youtube_prepare`. Queue a
   private upload with `youtube_queue` only when requested. Public release
   remains a separate owner decision. Check `youtube_upload_status` afterwards.
5. After the owner explicitly approves public release, confirm the publication's
   `video_id` and `channel_id` with `youtube_upload_status`. Call
   `youtube_approve_public` with that `publication_id`, exact `video_id`, and
   `approve_public=true`. `sync_playlist` defaults to true. This changes the
   existing upload's visibility without rendering or uploading again. Check
   `youtube_upload_status` again for `status=public` and the expected channel.
   Private-upload approval alone never authorizes this step.

For newly rendered Showcase publications, `branding_profile=null` explicitly
overrides a project's splash default; omission inherits the project setting.
`branding_select(profile=null)` disables branding for future project renders.
Do not disable the entire Games project's branding just to import one finished
master. YouTube clickable end-screen elements are a separate Studio operation.

## Acceptance evidence

Baseline: existing ArcoreCut exact-master assembly on Windows / Godot 4.7.2.
Scope: provider discovery, exact-byte catalog import, private metadata plan;
no changes to the approved picture/audio or gameplay runtime.
Validate registry and hub tests, discover schemas through the hub, verify live
channel status, and compare the downloaded Showcase original SHA256 to the
approved local master. Store production receipts under GameVideo, outside Git.
