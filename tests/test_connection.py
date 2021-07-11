import pytest
from anthemav import Connection


def test_instantiate_connection():
    Connection()


@pytest.mark.asyncio
async def test_create_connection_auto_reconnect_false():
    conn = await Connection().create(auto_reconnect=False)
    assert conn is not None
