# IETF vCon Spec Notes

Captured from the IETF vCon Working Group document list and the core container draft.
Source: https://datatracker.ietf.org/group/vcon/documents/

## Working Group documents (as of 2026-07)

| Draft | Title | Status | Rev |
|-------|-------|--------|-----|
| `draft-ietf-vcon-vcon-core-03` | The JSON format for vCon — Conversation Data Container | Adopted WG draft (core) | 03, exp 2026-06-30 |
| `draft-ietf-vcon-overview-01` | The vCon — Conversation Data Container — Overview | Adopted WG draft | 01, exp 2026-03-02 |
| `draft-ietf-vcon-cc-extension-02` | The JSON vCon — Contact Center Extension | Adopted WG draft (extension) | 02, exp 2026-06-30 |
| `draft-ietf-vcon-privacy-primer-01` | Privacy Primer for vCon Developers | Adopted WG draft | 01, exp 2026-05-04 |
| `draft-ietf-vcon-mimi-messages-00` | (MIMI messages) | Expired | 00, exp 2025-10-19 |

The **core container format** is `draft-ietf-vcon-vcon-core` (not "vcon-container";
that was the older name). Container version string for this revision: **`0.4.0`**.

## vCon object model (core-03)

### Top-level object
| Property | Type | Req | Notes |
|----------|------|-----|-------|
| `vcon` | String | — | Syntax/version, "0.4.0" |
| `uuid` | String | Yes | Globally unique, prefer UUIDv8 |
| `created_at` | RFC3339 date | Yes | Immutable |
| `updated_at` | RFC3339 date | No | |
| `subject` | String | No | Free-form topic |
| `extensions` | String[] | No | Non-core schema extensions in use |
| `critical` | String[] | No | Extensions a consumer MUST support |
| `redacted` | object | No | Ref to prior unredacted vCon (mutually excl. with `amended`) |
| `amended` | object | No | Ref to prior vCon with additions |
| `parties` | Party[] | Yes | Participants |
| `dialog` | Dialog[] | No | Media/text exchanges |
| `analysis` | Analysis[] | No | Analysis results |
| `attachments` | Attachment[] | No | Ancillary docs |

### Party object
`tel`, `sip`, `stir`, `mailto`, `name`, `did`, `validation`, `gmlpos`,
`civicaddress`, `uuid`, `type` ("person"|"bot"|"organization"), `org`, `dept`.
All optional. `name`="anonymous" for privacy.

### Dialog object
- `type` (Yes): **"recording" | "recording-set" | "text" | "transfer" | "incomplete"**
- `start` (Yes): date
- `duration`: number (seconds)
- `parties`: int | int[] (party indices; required for text/recording)
- `originator`: int (party index)
- `mediatype`: MIME type (required for inline)
- `filename`, `application`, `message_id`, `session_id`, `party_history`
- Inline content: `body` + `encoding` ("base64url" | "json" | "none")
- External content: `url` + `content_hash` (required with url)
- `incomplete` needs `disposition`: "no-answer"|"congestion"|"failed"|"busy"|"hung-up"|"voicemail-no-message"
- `transfer`/`recording-set` have their own required index fields, no content.

`party_history` event enum: "join","drop","hold","unhold","mute","unmute","keydown","keyup".

### Analysis object
- `type` (Yes): **"report" | "sentiment" | "summary" | "transcript" | "translation" | "tts"**
- `dialog`: int|int[] (dialog indices covered)
- `attachment`: int|int[]
- `vendor` (Yes), `product`, `schema`
- `mediatype`, `filename`
- Inline: `body` + `encoding`; External: `url` + `content_hash`

### Attachment object
- `start` (Yes): date
- `party` (Yes): int (distributing party index)
- `dialog` (Yes): int (related dialog index)
- `purpose`, `mediatype`, `filename`
- Inline: `body` + `encoding`; External: `url` + `content_hash`

### Content encoding rules
- Inline: `{ "body": <...>, "encoding": "base64url" | "json" | "none" }`
  - `json`: body is a JSON value; `none`: body is a plain JSON string; `base64url`: RFC4648.
- External: `{ "url": "https://...", "content_hash": "sha512-<b64url>" }`
- ContentHash format: `<alg><hyphen><Base64url(digest)>`, SHA-512 mandatory.
- Array elements referenced by zero-based index; do not reorder.

## Mapping intuition: agent trajectory -> vCon
- Each trajectory = one vCon (`uuid`, `created_at`, `subject` = task).
- Parties: the agent (`type`="bot", `name`=model), the user/task-setter (`type`="person"),
  and each tool/environment as a party (`type`="bot"/"organization"), or represent tools via roles.
- Dialog: one `text` dialog per message/turn (system, user, assistant, tool), with
  `originator` = party index, `start` = step timestamp, `body`=content, `encoding`="none"/"json".
  Tool calls & tool results can be `text` dialogs with JSON bodies (encoding="json").
- Analysis: rewards/scores/success flags/final judgments -> `analysis` type "report"
  with `vendor` = "mythos" and `body` (encoding="json") carrying the metrics.
- Attachments: task spec / system prompt / rubric as attachments.
