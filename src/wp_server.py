"""MCP server exposing WordPress diagnostics to support agents."""
from fastmcp import FastMCP

from src.mcp_server.wp_client import WPError, wp_get

mcp = FastMCP("wordpress-support")


@mcp.tool()
def get_env_info() -> dict:
    """Get the WordPress site environment: versions, theme, and site URL.

    Use this before diagnosing any bug report. Returns WordPress version,
    PHP version, active theme, and whether debug mode is enabled.
    """
    try:
        site = wp_get("")
        health = wp_get("wp-site-health/v1/directory-sizes")
    except WPError as error:
        return {"error": str(error)}

    return {
        "site_name": site.get("name"),
        "site_url": site.get("url"),
        "wp_version": site.get("wp_version", "unknown"),
        "namespaces": site.get("namespaces", []),
        "directory_sizes_available": bool(health),
    }


if __name__ == "__main__":
    mcp.run()