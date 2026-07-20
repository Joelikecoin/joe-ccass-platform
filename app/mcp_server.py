from fastmcp import FastMCP

from app.services.ccass import get_ccass_service

mcp = FastMCP("Joe CCASS Platform")


@mcp.tool
async def get_ccass_stock_data(code: str, holdings_limit: int = 15) -> dict:
    """Return verified CCASS holdings for a Hong Kong stock code.

    The result includes source/date metadata, T+2 limitations, dual concentration
    denominators and structured warnings. The issue ID is resolved from the stock code;
    it is never guessed.
    """
    result = await get_ccass_service().get_stock_data(code, holdings_limit=holdings_limit)
    return result.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001, path="/mcp")
