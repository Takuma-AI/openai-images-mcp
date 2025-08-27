# OpenAI Image Generation MCP Server

Enables Claude to create visual images using OpenAI's DALL-E 3.

## What This Enables

Through this MCP server, Claude can:
- Generate high-quality images from text descriptions
- Create visuals in different sizes and styles
- Produce both standard and HD quality images
- Transform ideas into visual representations

This extends Takuma OS's capabilities by adding visual creation to its toolkit, allowing for richer communication and documentation.

## Setup

### 1. Get OpenAI API Key

1. Sign up or log in at [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys section
3. Create a new API key
4. Save it securely - you'll need it for configuration

### 2. Install Dependencies

```bash
cd tools/servers/openai-images
./venv/bin/pip install -r requirements.txt
```

### 3. Configure Credentials

Option A: Environment Variable (Recommended)
```bash
# Add to your .env file in takuma-os root
echo "OPENAI_API_KEY=sk-your-api-key-here" >> /Users/kate/Projects/takuma-os/.env
```

Option B: Local credentials.json (for testing)
```bash
cp credentials.example.json credentials.json
# Edit credentials.json with your API key
```

### 4. Test Connection

```bash
./venv/bin/python tests/test_connection.py
```

### 5. Add to Claude Code

```bash
# From takuma-os root directory
claude mcp add openai-images \
  "$PWD/tools/servers/openai-images/venv/bin/python $PWD/tools/servers/openai-images/server.py"
```

## Usage Examples

Once connected, you can ask Claude:

- "Generate an image of a peaceful mountain landscape at sunset"
- "Create a cyberpunk-style illustration of a city street"
- "Make an HD image of a steampunk inventor's workshop"
- "Generate a natural-style portrait of a friendly robot"

## Default Save Location

Generated images are automatically saved to:
- `takuma-os/local/generated-images/` (gitignored directory)

You can override this by specifying a custom `save_path` parameter.

## Available Tools

### 1. generate_image

Generates an image using DALL-E 3 and returns a temporary URL.

**Parameters:**
- `prompt` (required): Text description of the image (max 4000 characters)
- `size`: Image dimensions
  - `"1024x1024"` (default, square)
  - `"1792x1024"` (landscape)
  - `"1024x1792"` (portrait)
- `quality`: Image quality
  - `"standard"` (default, faster and lower cost)
  - `"hd"` (higher quality but slower)
- `style`: Visual style
  - `"vivid"` (default, dramatic and hyper-real)
  - `"natural"` (more natural, less stylized)

**Returns:**
- `success`: Whether generation succeeded
- `image_url`: URL to the generated image (expires after 1 hour)
- `revised_prompt`: The expanded prompt DALL-E actually used
- `parameters`: The settings used for generation
- `error`: Error message if generation failed

### 2. save_generated_image

Downloads and saves a generated image locally.

**Parameters:**
- `image_url` (required): The URL of the generated image from OpenAI
- `filename`: Optional custom filename (without extension, defaults to timestamp)
- `save_path`: Optional custom save directory (defaults to `local/generated-images`)

**Returns:**
- `success`: Whether save succeeded
- `file_path`: Absolute path to saved file
- `relative_path`: Path relative to project root
- `filename`: The filename used
- `size_bytes`: Size of the saved file

### 3. generate_and_save_image

Generates an image and automatically saves it locally in one step.

**Parameters:**
- `prompt` (required): Text description of the image
- `size`: Image dimensions (same as generate_image)
- `quality`: Image quality (same as generate_image)
- `style`: Visual style (same as generate_image)
- `filename`: Optional custom filename (without extension)
- `save_path`: Optional custom save directory

**Returns:**
- All fields from generate_image plus:
- `file_path`: Absolute path to saved file
- `relative_path`: Path relative to project root
- `filename`: The filename used

**This is the recommended tool for most use cases** as it handles both generation and saving automatically.

## Cost Considerations

- Standard quality 1024x1024: ~$0.040 per image
- Standard quality 1792x1024 or 1024x1792: ~$0.080 per image
- HD quality 1024x1024: ~$0.080 per image
- HD quality 1792x1024 or 1024x1792: ~$0.120 per image

## Limitations

- DALL-E 3 only generates 1 image at a time (n=1)
- Image URLs expire after 1 hour
- Content policy applies - inappropriate requests will be rejected
- Rate limits apply based on your OpenAI account tier

## Troubleshooting

### Missing API Key
Ensure OPENAI_API_KEY is set in your environment or credentials.json

### Rate Limit Errors
Wait a moment and try again, or upgrade your OpenAI account tier

### Authentication Failed
Verify your API key is correct and has not been revoked

### Quota Exceeded
Check your OpenAI account billing and add credits if needed