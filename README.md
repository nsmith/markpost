# Markpost

An MCP server that takes Markdown content and syndicates it to **Twitter/X**, **Threads**, and a **static blog on S3**. Designed to be used by AI agents like Claude Code — write a post in Markdown, and Markpost handles the formatting and publishing for each platform.

## What it does

- **Formats per platform** — Strips Markdown to plain text for social media, renders full HTML for blog
- **Auto-splits into threads** — Long content is split at `---` separators or sentence boundaries, respecting each platform's character limit (280 for Twitter, 500 for Threads)
- **Previews before publishing** — Dry-run tool shows exactly how content will be formatted and split
- **Syndicates everywhere at once** — Publish to all platforms with a single tool call, or pick specific ones

## Tools

| Tool | Description |
|------|-------------|
| `publish_post` | Format and publish Markdown to one or more platforms |
| `preview_post` | Preview formatting and thread splits without publishing |
| `ping` | Health check |

## Quick start

### 1. Install

```bash
git clone <this-repo> && cd markpost
uv venv && uv pip install -e ".[dev]"
```

### 2. Configure API keys

Copy the example config and fill in your credentials:

```bash
mkdir -p ~/.markpost
cp config.example.toml ~/.markpost/config.toml
```

Edit `~/.markpost/config.toml`:

```toml
[twitter]
api_key = "your-api-key"
api_secret = "your-api-secret"
access_token = "your-access-token"
access_token_secret = "your-access-token-secret"

[threads]
access_token = "your-long-lived-access-token"
user_id = "your-threads-user-id"

[blog]
s3_bucket = "my-blog-bucket"
s3_prefix = "posts/"
base_url = "https://blog.example.com"

[blog.aws]
region = "us-east-1"
```

You can also set a custom config path via the `MARKPOST_CONFIG` environment variable.

### 3. Connect to an MCP client

See the sections below for your specific client.

## Running the server

### stdio mode (default)

stdio is the standard transport for local MCP clients. The server reads JSON-RPC messages from stdin and writes responses to stdout.

```bash
uv run python src/markpost/server.py
```

Or using the FastMCP CLI:

```bash
uv run fastmcp run src/markpost/server.py
```

### HTTP mode (remote / SSE)

For remote access or web-based clients, run in HTTP mode:

```bash
uv run fastmcp run src/markpost/server.py --transport http --host 0.0.0.0 --port 9000
```

The server will be available at `http://localhost:9000`. Clients connect via the Streamable HTTP transport.

## Client setup

### Claude Code

Register the server with the `claude` CLI:

```bash
claude mcp add markpost -- uv run --directory /path/to/markpost fastmcp run src/markpost/server.py
```

Verify it's registered:

```bash
claude mcp list
```

The `publish_post` and `preview_post` tools will now be available in Claude Code sessions.

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "markpost": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/markpost",
        "fastmcp", "run", "src/markpost/server.py"
      ]
    }
  }
}
```

Restart Claude Desktop after saving.

### Other MCP clients (HTTP)

Start the server in HTTP mode (see above), then point your client at `http://localhost:9000`.

## Getting API keys

### Twitter/X

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a Project and App
3. Set app permissions to **Read and Write**
4. Generate your API Key, API Secret, Access Token, and Access Token Secret
5. If you changed permissions after generating tokens, **regenerate them**

The free tier allows 1,500 tweets/month.

### Threads

1. Go to the [Meta Developer Dashboard](https://developers.facebook.com/)
2. Create a new app and add the **Threads API** product
3. Your Threads account must be **public**
4. Complete the OAuth flow to get an access token:
   - Authorize at `https://threads.net/oauth/authorize?client_id={app_id}&redirect_uri={uri}&scope=threads_basic,threads_content_publish&response_type=code`
   - Exchange the code for a short-lived token at `https://graph.threads.net/oauth/access_token`
   - Exchange for a long-lived token (60 days) at `https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret={secret}&access_token={short_token}`
5. Get your user ID: `GET https://graph.threads.net/v1.0/me?access_token={token}`

### S3 Blog

1. Create an S3 bucket configured for static website hosting
2. Configure your AWS credentials via the standard methods (`~/.aws/credentials`, environment variables, or IAM role)
3. Set `s3_bucket`, `s3_prefix`, and `base_url` in your config

The `base_url` should be the public URL where your blog is served (e.g., your CloudFront distribution or S3 website endpoint).

## Thread splitting

Long content is automatically split into threads. You control splits two ways:

**Explicit separators** — Use `---` in your Markdown to force a split:

```markdown
Here is the first tweet in my thread.

---

And here is the second one.
```

**Auto-splitting** — If any section exceeds the platform's character limit, it's split at sentence boundaries. If a single sentence is too long, it falls back to word boundaries.

The `preview_post` tool lets you see exactly how content will be split before publishing.

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/ -v

# Run a specific test file
uv run pytest tests/test_formatter.py -v
```

## Project structure

```
src/markpost/
  server.py              # FastMCP server — ping, publish_post, preview_post
  config.py              # TOML config loading
  formatter.py           # markdown_to_plain, split_into_thread, markdown_to_html
  publishers/
    twitter.py           # Twitter/X via tweepy
    threads.py           # Threads via httpx (async)
    blog.py              # S3 upload via boto3
```

## License

Apache 2.0
