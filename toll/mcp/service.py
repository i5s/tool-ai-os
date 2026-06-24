"""MCP service facade."""
from __future__ import annotations

import json

from .client import BaseMCPConnector, FilesystemConnector, GitConnector, SQLiteConnector


class MCPService:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self._fs: FilesystemConnector | None = None
        self._git: GitConnector | None = None
        # sqlite uses a dedicated db path under project
        self._sqlite = SQLiteConnector(db_path=f"{project_root}/tool.db")

    def connectors(self):
        yield "filesystem", self.fs()
        yield "git", self.git()
        yield "sqlite", self.sqlite()

    def fs(self) -> FilesystemConnector:
        if self._fs is None:
            self._fs = FilesystemConnector(self.project_root)
        return self._fs

    def git(self) -> GitConnector:
        if self._git is None:
            self._git = GitConnector(self.project_root)
        return self._git

    def sqlite(self) -> SQLiteConnector:
        return self._sqlite

    def call(self, server: str, tool: str, arguments: dict) -> dict:
        mapping = {
            "filesystem": self.fs(),
            "git": self.git(),
            "sqlite": self.sqlite(),
        }
        connector = mapping.get(server)
        if connector is None:
            return {"success": False, "error": f"Unknown MCP server: {server}"}
        result = connector.call_tool(tool, arguments)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "server": result.server,
            "tool": result.tool,
        }
