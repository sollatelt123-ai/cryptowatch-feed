# Crypto Watch feed — schema v1

The app downloads one JSON document from the **Data source** URL (Settings → Data). The document can be:

- today: `feed/feed.json` served from GitHub, or any other public HTTPS location;
- later: the Crypto Watch backend (for example `GET https://api.example/v1/feed`).

The UI never depends on the URL, only on this schema. `feed/feed.json` is also bundled in the APK. It is loaded on first launch, so the app works offline immediately.

Rules:

- **No secrets.** Never put API keys or tokens in the feed or the URL.
- **Never invent addresses.** Leave `address` as `null` until it is published or detected. The app then shows *NOT PUBLISHED* or *NOT DETECTED*.
- `id` values must be stable. They are how the app deduplicates entries and keeps read/unread and watch state.
- The feed is authoritative. A project, signal or alert that disappears from the feed disappears from the app, but user watchlist, notes, read state and settings stay.
- Timestamps: ISO‑8601 (`2026-09-24T16:00:00Z`, offsets allowed) or epoch seconds/milliseconds.
- Unknown fields are ignored. Newer `schemaVersion` values are rejected, and the app keeps its cache.

## Top level

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-09-24T16:00:00Z",
  "projects": [ ... ],
  "signals":  [ ... ],
  "alerts":   [ ... ]
}
```

## Project

```json
{
  "id": "balcore",
  "name": "Balcore",
  "categories": ["DeFi Infrastructure"],
  "status": "EARLY",                 // EARLY | UPCOMING | LIVE
  "chain": "Solana",                 // null → TBA
  "tge": "Q4 2026",                  // free text, null → TBA
  "description": "…",
  "logoUrl": "https://…",            // optional, https only
  "bannerUrl": "https://…",          // optional
  "monitoring": "ACTIVE",
  "lastUpdateAt": "…",               // optional, defaults to newest update
  "metrics": [{ "label": "Testnet users", "value": "120k" }],
  "links": [
    { "type": "WEBSITE", "url": "https://…" }   // WEBSITE | X | TELEGRAM | DISCORD | DOCS | EXPLORER | GITHUB | OTHER
  ],
  "wallets": [
    {
      "type": "TOKEN_CA",            // TOKEN_CA | OFFICIAL_WALLET | TREASURY | CREATOR | FUNDER | CLUSTER | OTHER
      "label": null,                 // optional custom label
      "address": null,               // null until published/detected
      "chain": "solana",
      "source": "Official X post",
      "firstDetectedAt": "…",
      "verification": "OFFICIAL"     // OFFICIAL | DETECTED | UNVERIFIED
    }
  ],
  "updates": [
    {
      "id": "balcore-2026-09-24-devlog",
      "title": "…",
      "description": "…",
      "source": "Balcore blog",
      "url": "https://…",            // opened when the news item is tapped
      "timestamp": "…",
      "priority": "NORMAL"           // LOW | NORMAL | HIGH | CRITICAL
    }
  ]
}
```

## Signal (Solana scanner)

```json
{
  "id": "sig-7Xb…-first",
  "type": "FIRST",                   // FIRST | RECALL
  "signalTime": "…",
  "entryMcap": 82000,                // USD
  "currentMcap": 190000,
  "liquidity": 32000,
  "athMcap": 240000,
  "maxX": 2.9,                       // optional, otherwise athMcap / entryMcap
  "status": "ACTIVE",                // ACTIVE counts in "Active Signals"
  "token": {
    "ca": "…mint address…",          // null → NOT DETECTED
    "name": "…",
    "symbol": "…",
    "logoUrl": "https://…",
    "chain": "solana",
    "createdAt": "…",                // token age
    "creator": "…",
    "funder": "…",
    "cluster": "…"
  },
  "wallets": [ /* optional, same shape as project wallets */ ],
  "history": [
    { "kind": "SIGNAL",    "title": "FIRST signal", "detail": "MCAP $82K", "timestamp": "…" },
    { "kind": "MILESTONE", "title": "2x reached",   "timestamp": "…" },
    { "kind": "WALLET",    "title": "Funder detected", "detail": "…", "timestamp": "…" }
  ]
}
```

## Alert

```json
{
  "id": "balcore-ca-detected",
  "type": "CA_DETECTED",
  "title": "Official token contract detected",
  "message": "…",
  "source": "Balcore official X",
  "timestamp": "…",
  "priority": "CRITICAL",
  "projectId": "balcore",            // tap → Project detail
  "signalId": null,                  // tap → Signal detail
  "address": "…"                     // shown in the notification as CA: …
}
```

Alert types and the Settings switch that controls their notifications:

| type | switch |
|---|---|
| `NEW_PROJECT` | New projects |
| `PROJECT_UPDATE` (HIGH/CRITICAL only) | Important project updates |
| `TGE`, `LAUNCH` | TGE / Launch |
| `CA_DETECTED`, `OFFICIAL_WALLET_DETECTED`, `WALLET_CHANGED`, `CREATOR_DETECTED`, `FUNDER_DETECTED`, `CLUSTER_DETECTED` | Wallet / CA detected |
| `FIRST`, `RECALL` | Solana signals |
| `MILESTONE_1_5X`, `MILESTONE_2X`, `MILESTONE_3X`, `MILESTONE_5X` (aliases `1.5x`, `2x`, `3x`, `5x+`) | Milestones |
| `PRICE_ALERT` | Watchlist / price alerts |
| `SYSTEM` | in-app only |

## Push (FCM data message)

The backend sends a data message with the same keys as an alert: `id`, `type`, `title`, `message`, `source`, `timestamp`, `priority`, `projectId`, `signalId` and `address`. The app stores it and notifies according to Settings. Tapping it opens the matching detail screen. The app then syncs the full feed.

Devices register their token with `POST {CW_PUSH_REGISTER_URL}` and the body `{"token","platform","appId","version"}`.
