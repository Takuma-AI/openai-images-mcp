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
import httpx
from datetime import datetime
from pathlib import Path

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

# Default save location - in takuma-os local directory (gitignored)
DEFAULT_SAVE_PATH = os.path.join(project_root, 'local', 'generated-images')

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
    style: Optional[str] = "vivid",
    model: Optional[str] = "dall-e-3"
) -> Dict[str, Any]:
    """
    Generate an image using OpenAI's image generation models.
    
    Args:
        prompt: Text description of the image to generate (max 4000 chars)
        size: Image dimensions - "1024x1024", "1792x1024", or "1024x1792"
        quality: "standard" (faster, lower cost) or "hd" (higher quality, slower)
        style: "vivid" (dramatic, hyper-real) or "natural" (more natural, less stylized)
        model: Model to use - "dall-e-3" (default), "dall-e-2", or "gpt-image-1" (if available)
    
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
        # Note: gpt-image-1 may require additional access/approval from OpenAI
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,  # Most models only support n=1
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

@mcp.tool()
async def save_generated_image(
    image_url: str,
    filename: Optional[str] = None,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download and save a generated image locally.
    
    Args:
        image_url: The URL of the generated image from OpenAI
        filename: Optional custom filename (without extension). If not provided, uses timestamp
        save_path: Optional custom save directory. If not provided, uses default location
    
    Returns:
        Dict with success status and local file path
    """
    
    try:
        # Determine save directory
        if save_path:
            # Use provided path relative to project root if not absolute
            if not os.path.isabs(save_path):
                save_dir = os.path.join(project_root, save_path)
            else:
                save_dir = save_path
        else:
            # Use default location
            save_dir = DEFAULT_SAVE_PATH
        
        # Create directory if it doesn't exist
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dalle_image_{timestamp}"
        
        # Ensure filename doesn't have extension (we'll add .png)
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            filename = os.path.splitext(filename)[0]
        
        # Full file path
        file_path = os.path.join(save_dir, f"{filename}.png")
        
        # Download the image
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download image: HTTP {response.status_code}"
                }
            
            # Save the image
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Get relative path from project root for cleaner display
            relative_path = os.path.relpath(file_path, project_root)
            
            return {
                "success": True,
                "file_path": file_path,
                "relative_path": relative_path,
                "filename": f"{filename}.png",
                "size_bytes": len(response.content),
                "message": f"Image saved successfully to {relative_path}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save image: {str(e)}"
        }

@mcp.tool()
async def generate_and_save_image(
    prompt: str,
    size: Optional[str] = "1024x1024",
    quality: Optional[str] = "standard",
    style: Optional[str] = "vivid",
    model: Optional[str] = "dall-e-3",
    filename: Optional[str] = None,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an image and automatically save it locally.
    Combines generation and saving in one step.
    
    Args:
        prompt: Text description of the image to generate (max 4000 chars)
        size: Image dimensions - "1024x1024", "1792x1024", or "1024x1792"
        quality: "standard" (faster, lower cost) or "hd" (higher quality, slower)
        style: "vivid" (dramatic, hyper-real) or "natural" (more natural, less stylized)
        model: Model to use - "dall-e-3" (default), "dall-e-2", or "gpt-image-1" (if available)
        filename: Optional custom filename (without extension)
        save_path: Optional custom save directory
    
    Returns:
        Dict with success status, image URL, local file path, and revised prompt
    """
    
    # Generate the image first
    generation_result = await generate_image(prompt, size, quality, style, model)
    
    if not generation_result.get('success'):
        return generation_result
    
    # Save the generated image
    save_result = await save_generated_image(
        image_url=generation_result['image_url'],
        filename=filename,
        save_path=save_path
    )
    
    if not save_result.get('success'):
        # Still return the generation result with save error
        return {
            **generation_result,
            "save_error": save_result.get('error'),
            "message": f"Image generated but failed to save: {save_result.get('error')}"
        }
    
    # Combine both results
    return {
        "success": True,
        "image_url": generation_result['image_url'],
        "revised_prompt": generation_result['revised_prompt'],
        "parameters": generation_result['parameters'],
        "file_path": save_result['file_path'],
        "relative_path": save_result['relative_path'],
        "filename": save_result['filename'],
        "message": f"Image generated and saved to {save_result['relative_path']}"
    }

if __name__ == "__main__":
    mcp.run()