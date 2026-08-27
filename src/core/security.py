from fastapi import Header, HTTPException


async def get_tenant_id(x_omniledger_tenant_id: int = Header(...)) -> int:
    return x_omniledger_tenant_id