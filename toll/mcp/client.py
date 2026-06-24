"""Base MCP connector + concrete connectors."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class MCPCallResult:
    server: str
    tool: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: int = 0


class BaseMCPConnector:
    name: str = ""

    def __init__(self, **kwargs: Any) -> None:
        pass

    def _run(self, tool: str, arguments: dict) -> MCPCallResult:
        raise NotImplementedError

    def call_tool(self, name: str, arguments: dict) -> MCPCallResult:
        return self._run(name, arguments)

    def health_check(self) -> bool:
        try:
            self.call_tool("__health__", {})
            return True
        except Exception:
            return False


class FilesystemConnector(BaseMCPConnector):
    name = "filesystem"

    def __init__(self, base_dir: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_dir = base_dir

    def _run(self, tool: str, arguments: dict) -> MCPCallResult:
        started = time.time()
        if tool == "list_directory":
            path = arguments.get("path") or self.base_dir
            try:
                entries = os.listdir(path)
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=True, output="\n".join(entries), duration_ms=duration)
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
        if tool == "read_file":
            path = arguments.get("path") or self.base_dir
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    content = handle.read()
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=True, output=content, duration_ms=duration)
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
        duration = int((time.time() - started) * 1000)
        return MCPCallResult(server=self.name, tool=tool, success=False, error=f"Unsupported tool: {tool}", duration_ms=duration)


class GitConnector(BaseMCPConnector):
    name = "git"

    def __init__(self, repo_path: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.repo_path = repo_path

    def _run(self, tool: str, arguments: dict) -> MCPCallResult:
        arguments = dict(arguments or {})
        arguments.setdefault("repo_path", self.repo_path)
        started = time.time()
        if tool == "git_status":
            try:
                proc = subprocess.run(["git", "-C", self.repo_path, "status", "--short"], capture_output=True, text=True)
                output = "\n".join(line.strip() for line in (proc.stdout or "").splitlines())
                duration = int((time.time() - started) * 1000)
                if proc.returncode != 0:
                    return MCPCallResult(server=self.name, tool=tool, success=False, error=proc.stderr, duration_ms=duration)
                return MCPCallResult(server=self.name, tool=tool, success=True, output=output, duration_ms=duration)
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
        if tool == "git_diff":
            try:
                proc = subprocess.run(["git", "-C", self.repo_path, "diff"], capture_output=True, text=True)
                duration = int((time.time() - started) * 1000)
                if proc.returncode != 0:
                    return MCPCallResult(server=self.name, tool=tool, success=False, error=proc.stderr, duration_ms=duration)
                return MCPCallResult(server=self.name, tool=tool, success=True, output=proc.stdout, duration_ms=duration)
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
        if tool == "git_log":
            try:
                proc = subprocess.run(["git", "-C", self.repo_path, "log", "--oneline", "--decorate", "-n", str(int(arguments.get("limit", 5)))], capture_output=True, text=True)
                duration = int((time.time() - started) * 1000)
                if proc.returncode != 0:
                    return MCPCallResult(server=self.name, tool=tool, success=False, error=proc.stderr, duration_ms=duration)
                return MCPCallResult(server=self.name, tool=tool, success=True, output=proc.stdout, duration_ms=duration)
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
        if tool == "git_branch":
            try:
                proc = subprocess.run(["git", "-C", self.repo_path, "branch", "--show-current"], capture_output=True, text=True)
                duration = int((time.time() - started) * 1000)
                if proc.returncode != 0:
                    return MCPCallResult(server=self.name, tool=tool, success=False, error=proc.stderr, duration_ms=duration)
                return MCPCallResult(server=self.name, tool=tool, success=True, output=proc.stdout.strip(), duration_ms=duration)
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
        duration = int((time.time() - started) * 1000)
        return MCPCallResult(server=self.name, tool=tool, success=False, error=f"Unsupported tool: {tool}", duration_ms=duration)


class SQLiteConnector(BaseMCPConnector):
    name = "sqlite"

    def __init__(self, db_path: str = ":memory:", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.db_path = db_path

    def _run(self, tool: str, arguments: dict) -> MCPCallResult:
        started = time.time()
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row
                if tool == "sqlite_run":
                    sql = arguments.get("sql", "")
                    if not sql:
                        duration = int((time.time() - started) * 1000)
                        return MCPCallResult(server=self.name, tool=tool, success=False, error="Missing sql argument", duration_ms=duration)
                    cursor = connection.execute(sql)
                    rows = cursor.fetchall()
                    payload = "\n".join(str(dict(row)) for row in rows)
                    duration = int((time.time() - started) * 1000)
                    return MCPCallResult(server=self.name, tool=tool, success=True, output=payload, duration_ms=duration)
                if tool == "list_tables":
                    cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = [row["name"] for row in cursor.fetchall()]
                    duration = int((time.time() - started) * 1000)
                    return MCPCallResult(server=self.name, tool=tool, success=True, output="\n".join(tables), duration_ms=duration)
                duration = int((time.time() - started) * 1000)
                return MCPCallResult(server=self.name, tool=tool, success=False, error=f"Unsupported tool: {tool}", duration_ms=duration)
        except Exception as exc:
            duration = int((time.time() - started) * 1000)
            return MCPCallResult(server=self.name, tool=tool, success=False, error=str(exc), duration_ms=duration)
