# Oh My Cassette

Hermes Agent plugin for sending QQ and Telegram gateway media to the Cassette web editor, supervising the browser workflow with Playwright, exporting the result, and delivering status/media back through the originating gateway.

Weixin/WeChat compatibility is still present in the codebase for existing deployments, but QQ and Telegram are the primary supported gateways.

Runtime state is stored outside the repository under `~/.hermes/cassette` by default.

## Requirements

- macOS or Linux.
- Hermes Agent installed and gateway configuration handled by Hermes.
- Python 3.10+.
- `ffmpeg`, used only to normalize incoming gateway videos to H.264 MP4 before upload.
- A Cassette account for `https://sg.trycassette.online/agent` or `https://trycassette.online/agent`.

If Hermes Agent is not installed yet:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Install system tools:

```bash
# macOS
brew install uv ffmpeg

# Debian/Ubuntu Linux
sudo apt-get update
sudo apt-get install -y ffmpeg
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install

```bash
git clone https://github.com/YOUR_ACCOUNT/oh-my-cassette.git
cd oh-my-cassette
python3 scripts/install_plugin.py
```

The installer:

- installs the plugin into `~/.hermes/plugins/cassette` as a symlink by default;
- asks whether to enable the plugin with `hermes plugins enable cassette`;
- asks which Cassette URL to use:
  - `https://sg.trycassette.online/agent` (Asia, default)
  - `https://trycassette.online/agent` (America)
- optionally saves Cassette login and Jamendo credentials into `~/.hermes/.env`;
- detects `ffmpeg` and `ffprobe` paths for service environments;
- installs Python Playwright and Chromium into the Hermes Python environment;
- restarts the Hermes gateway service.

To copy files instead of creating a symlink:

```bash
python3 scripts/install_plugin.py --copy --force
```

For non-interactive installs:

```bash
python3 scripts/install_plugin.py \
  --skip-plugin-enable \
  --skip-cassette-url \
  --skip-cassette-auth \
  --skip-jamendo-auth
```

## Configuration

The installer writes normal runtime settings to `~/.hermes/.env`. You can also edit that file manually.

Minimum useful values:

```bash
CASSETTE_URL=https://sg.trycassette.online/agent
CASSETTE_AUTH_EMAIL=you@example.com
CASSETTE_AUTH_PASSWORD=your-generated-cassette-password
CASSETTE_ASSET_ROOT=$HOME/.hermes/cassette
CASSETTE_HEADLESS=true
CASSETTE_FORCE_H264=true
```

Default media source roots:

```text
~/.hermes/qqbot
~/.hermes/telegram
~/.hermes/weixin
~/.hermes/cache
~/.hermes/tmp
```

If your gateway stores media elsewhere:

```bash
CASSETTE_ALLOWED_SOURCE_ROOTS="$HOME/.hermes/qqbot:$HOME/.hermes/telegram:$HOME/.hermes/cache:$HOME/.hermes/tmp:/path/to/media"
```

Optional Jamendo smart BGM configuration:

```bash
JAMENDO_CLIENT_ID=your_client_id
JAMENDO_CLIENT_SECRET=your_client_secret
```

`JAMENDO_CLIENT_SECRET` is reserved for future use. It is not sent to Jamendo and is not written to job metadata.

## Diagnose

Run:

```bash
python3 scripts/diagnose_install.py
```

The diagnostic checks:

- plugin install path;
- whether the plugin is enabled in Hermes;
- `~/.hermes/.env` values, with secrets redacted;
- `ffmpeg` and `ffprobe`;
- Playwright in the Hermes Python environment;
- Cassette URL reachability;
- Cassette login credentials by opening the Agent page in Chromium;
- Hermes gateway status.

If incoming media fails with `transcoder_missing`, run the installer again so it records explicit `CASSETTE_FFMPEG_BIN` and `CASSETTE_FFPROBE_BIN` paths:

```bash
python3 scripts/install_plugin.py \
  --skip-plugin-enable \
  --skip-cassette-url \
  --skip-cassette-auth \
  --skip-jamendo-auth \
  --skip-playwright-install
```

## Usage

In QQ or Telegram:

1. Send one or more video, image, or audio files.
2. Wait for the saved-material acknowledgement.
3. Send an edit instruction in the same conversation, or prefix it with `/edit`.
4. On the first edit in a Hermes session, choose the Cassette model and thinking level.
5. On the first edit in a Hermes session, choose whether Hermes should optimize the edit brief and whether it should smart-match BGM.
6. The plugin uploads saved assets to Cassette, drives the chat panel, monitors progress, exports the MP4, and sends final status/media back through the gateway when supported.

Useful commands:

```text
/edit <instruction>
/refine <instruction>
/music <BGM request>
/cut
/check_assets
/cassette_model
/cassette language zh
/cassette language en
/cassette status <job_id>
/cassette cancel <job_id>
```

Use `/new` or `/reset` to start a fresh Hermes session and clear the live Cassette browser session for that conversation.

## Behavior

- Cassette is the only editing engine.
- `ffmpeg` is used only for transparent gateway ingest compatibility normalization, not local editing.
- Upload uses the Cassette `/agent` programmatic file input.
- Same-session follow-up edits reuse the live Cassette browser page when possible.
- QQ defaults to Chinese Cassette UI/replies; Telegram defaults to English. Use `/cassette language zh|en` to override.
- Telegram Bot API uploads are limited to 50 MB. Oversized exports are sent as a compressed preview while the original export remains under `${CASSETTE_ASSET_ROOT}/exports/...`.
- Job state and exports are stored under `${CASSETTE_ASSET_ROOT:-~/.hermes/cassette}`.

## Smart BGM

Smart BGM matching can add audio as a normal asset in the active Cassette session.

Provider priority:

1. Exact song/artist search using public music sources.
2. Jamendo matching when `JAMENDO_CLIENT_ID` is configured.
3. Free To Use category/tag matching as fallback.

Exact BGM downloads are saved under:

```text
${CASSETTE_ASSET_ROOT}/downloads/exact_bgm/
${CASSETTE_ASSET_ROOT}/metadata/exact_bgm/
```

Jamendo downloads are saved under:

```text
${CASSETTE_ASSET_ROOT}/downloads/jamendo/
${CASSETTE_ASSET_ROOT}/metadata/jamendo/
```

## Development

Create a local test environment:

```bash
uv venv .venv
uv pip install --python .venv/bin/python pytest playwright
.venv/bin/python -m playwright install chromium
```

Run checks:

```bash
python3 -m compileall -q .
.venv/bin/python -m pytest -q
```

Run the local Cassette E2E harness:

```bash
.venv/bin/python scripts/e2e_local_cassette.py \
  --media tests/fixtures/sample.mp4 \
  --instruction "Make a short captioned video under 10 seconds."
```

Real gateway E2E tests are opt-in only and are skipped by default:

```bash
RUN_CASSETTE_E2E=1 .venv/bin/python -m pytest -q -m e2e
```

## Public Repository Safety

Do not commit:

- `.env` or `.env.e2e`;
- real gateway tokens, account IDs, chat IDs, or raw `wxid` values;
- Cassette credentials;
- Jamendo credentials;
- downloaded media, exports, job state, browser traces, or local runtime cache.

Runtime state belongs under `~/.hermes/cassette`, not in this repository.

## License

MIT. See [LICENSE](LICENSE).
