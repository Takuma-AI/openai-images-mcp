#!/usr/bin/env python3
"""
OpenAI Image Generation MCP Server
Enables Claude to create visual images using DALL-E 3
"""

import os
import json
from typing import Optional, Dict, Any
from openai import OpenAI
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load .env file - first try project root, then local
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../..'))
root_env = os.path.join(project_root, '.env')
local_env = os.path.join(script_dir, '.env')

if os.path.exists(root_env):
    load_dotenv(root_env)
elif os.path.exists(local_env):
    load_dotenv(local_env)

# Initialize MCP server
mcp = FastMCP("openai-images")

# Get credentials from environment or saved file
def load_credentials() -> Dict[str, str]:
    """Load credentials from environment or saved file"""
    # Check environment variables (now loaded from .env if exists)
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Try loading from saved file if not in environment
    if not api_key:
        # First try local credentials file
        local_creds = os.path.join(os.path.dirname(__file__), 'credentials.json')
        if os.path.exists(local_creds):
            with open(local_creds, 'r') as f:
                creds = json.load(f)
                api_key = creds.get('api_key')
    
    return {
        'api_key': api_key
    }

CREDS = load_credentials()

@mcp.tool()
async def generate_image(
    prompt: str,
    size: Optional[str] = "1024x1024",
    quality: Optional[str] = "standard",
    style: Optional[str] = "vivid"
) -> Dict[str, Any]:
    """
    Generate an image using OpenAI's DALL-E 3.
    
    Args:
        prompt: Text description of the image to generate (max 4000 chars)
        size: Image dimensions - "1024x1024", "1792x1024", or "1024x1792"
        quality: "standard" (faster, lower cost) or "hd" (higher quality, slower)
        style: "vivid" (dramatic, hyper-real) or "natural" (more natural, less stylized)
    
    Returns:
        Dict with success status, image URL, and revised prompt
    """
    
    if not CREDS.get('api_key'):
        return {
            "success": False,
            "error": "Missing OpenAI API credentials. Please set OPENAI_API_KEY environment variable."
        }
    
    # Validate parameters
    valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    if size not in valid_sizes:
        return {
            "success": False,
            "error": f"Invalid size. Must be one of: {', '.join(valid_sizes)}"
        }
    
    valid_qualities = ["standard", "hd"]
    if quality not in valid_qualities:
        return {
            "success": False,
            "error": f"Invalid quality. Must be one of: {', '.join(valid_qualities)}"
        }
    
    valid_styles = ["vivid", "natural"]
    if style not in valid_styles:
        return {
            "success": False,
            "error": f"Invalid style. Must be one of: {', '.join(valid_styles)}"
        }
    
    if len(prompt) > 4000:
        return {
            "success": False,
            "error": "Prompt too long. Maximum 4000 characters for DALL-E 3."
        }
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=CREDS['api_key'])
        
        # Generate image
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,  # DALL-E 3 only supports n=1
            size=size,
            quality=quality,
            style=style,
            response_format="url"
        )
        
        # Extract the image data
        image_data = response.data[0]
        
        return {
            "success": True,
            "image_url": image_data.url,
            "revised_prompt": image_data.revised_prompt,
            "parameters": {
                "size": size,
                "quality": quality,
                "style": style
            },
            "message": "Image generated successfully. The URL will expire after 1 hour."
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Provide helpful error messages
        if "api_key" in error_msg.lower():
            return {
                "success": False,
                "error": "API key authentication failed. Please check your OpenAI API key."
            }
        elif "rate_limit" in error_msg.lower():
            return {
                "success": False,
                "error": "Rate limit exceeded. Please wait before trying again."
            }
        elif "quota" in error_msg.lower():
            return {
                "success": False,
                "error": "API quota exceeded. Please check your OpenAI account billing."
            }
        else:
            return {
                "success": False,
                "error": f"Failed to generate image: {error_msg}"
            }

if __name__ == "__main__":
    mcp.run()