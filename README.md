# Crypto Watch feed

Public data feed for the **Crypto Watch** Android app (`lt.cryptowatch.app`).

The app downloads this file:

```
https://raw.githubusercontent.com/sollatelt123-ai/cryptowatch-feed/main/feed.json
```

Anything committed to `feed.json` on `main` shows up in the app after its next sync (at most 15 minutes, or at once with *Sync now*). No APK rebuild is needed. This covers new projects, project updates, wallets and contract addresses (CAs), creators, funders, clusters, Solana signals and alerts.

## Rules
- **This repository is public. Never commit API keys, tokens, passwords or private wallet keys.**
- **Never invent addresses.** Leave `address: null` until an address is published or detected. The app then shows *NOT PUBLISHED* or *NOT DETECTED*.
- Keep `id` values stable. The app uses them for deduplication, read/unread state and watchlists.
- Every push is checked by `scripts/validate.py` in the *Validate feed* workflow. Don't merge a red run.

The format is described in [FEED_SCHEMA.md](FEED_SCHEMA.md).

## Future backend
When the Crypto Watch backend exists, it serves the same schema, for example at `GET /v1/feed`. Switch the app to it in Settings → Data → Data source, or through the `CW_FEED_URL` variable in the app repository. The UI does not change.
