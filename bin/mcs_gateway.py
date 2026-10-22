
#!/usr/bin/env python3

import asyncio
import json
import logging
import os

import websockets
from ncclient import manager
from ncclient.operations import RPCError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcs-gateway")

WS_HOST = os.getenv("MCS_WS_HOST", "127.0.0.1")
WS_PORT = int(os.getenv("MCS_WS_PORT", "8765"))

NETCONF_HOST = os.environ["NETCONF_HOST"]
NETCONF_PORT = int(os.getenv("NETCONF_PORT", "830"))
NETCONF_USER = os.environ["NETCONF_USER"]
NETCONF_PASSWORD = os.environ["NETCONF_PASSWORD"]

# Load only an XML edit-config payload verified against
# the YANG schema actually exposed by this OCUDU deployment.
MCS_EDIT_XML = os.getenv("MCS_EDIT_XML")


def set_max_mcs(mcs: int) -> dict:
    if not 0 <= mcs <= 28:
        raise ValueError("MCS must be between 0 and 28")

    if not MCS_EDIT_XML:
        raise RuntimeError(
            "MCS_EDIT_XML is not configured. "
            "Verify the OCUDU YANG schema first."
        )

    # The XML must contain the real YANG path and namespace.
    # Replace the token only after validating the schema.
    payload = MCS_EDIT_XML.replace("__MAX_MCS__", str(mcs))

    with manager.connect(
        host=NETCONF_HOST,
        port=NETCONF_PORT,
        username=NETCONF_USER,
        password=NETCONF_PASSWORD,
        hostkey_verify=True,
        timeout=15,
        allow_agent=False,
        look_for_keys=False,
    ) as session:
        if not session.server_capabilities:
            raise RuntimeError("NETCONF capabilities unavailable")

        # Candidate is used only if the server supports it.
        if any(":candidate" in cap for cap in session.server_capabilities):
            session.edit_config(
                target="candidate",
                config=payload,
            )
            session.validate(source="candidate")
            session.commit()
        else:
            # Use running only if the exposed model supports
            # direct writes and the change is safe to apply.
            session.edit_config(
                target="running",
                config=payload,
            )

    return {
        "accepted": True,
        "max_mcs": mcs,
        "message": "NETCONF configuration update accepted",
    }


async def handle_client(websocket):
    async for raw in websocket:
        try:
            request = json.loads(raw)

            if request.get("cmd") != "set_max_mcs":
                raise ValueError("Unsupported command")

            mcs = request.get("value")
            if isinstance(mcs, bool) or not isinstance(mcs, int):
                raise ValueError("'value' must be an integer")

            log.info("Requested max MCS: %d", mcs)
            result = await asyncio.to_thread(set_max_mcs, mcs)

            await websocket.send(json.dumps({
                "ok": True,
                **result,
            }))

        except (ValueError, RuntimeError, RPCError) as exc:
            await websocket.send(json.dumps({
                "ok": False,
                "error": str(exc),
            }))
        except Exception:
            log.exception("Command failed")
            await websocket.send(json.dumps({
                "ok": False,
                "error": "Internal error; inspect gateway logs",
            }))


async def main():
    async with websockets.serve(
        handle_client,
        WS_HOST,
        WS_PORT,
        max_size=4096,
    ):
        log.info("MCS Gateway listening on %s:%d", WS_HOST, WS_PORT)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
