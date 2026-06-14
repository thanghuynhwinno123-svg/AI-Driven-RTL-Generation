import asyncio
import os
from pathlib import Path

from .vcs_log_parser import parse_vcs_log


class VCSAgent:
    def __init__(self, mcp_client, read_log_from_url, log, archive_log):
        self.mcp_client = mcp_client
        self.read_log_from_url = read_log_from_url
        self.log = log
        self.archive_log = archive_log

    async def run(self, working_directory: str, files, top: str, title: str, timeout=120.0):
        args = ["-full64", "-sverilog"] + list(files) + ["-top", top, "-R"]
        vcs_call = self.mcp_client.call_tool("call_vcs", {"working_directory": working_directory, "args": args})
        log_text = await self.read_log_from_url(await asyncio.wait_for(vcs_call, timeout=timeout))
        archive_path = await self.archive_log(f"FULL VCS LOG: {title}", log_text)
        await self.log(f"\n>>>>>>>>>> ĐÃ CHẠY VCS (full log: {archive_path}) >>>>>>>>>>")
        return log_text, parse_vcs_log(log_text), archive_path
