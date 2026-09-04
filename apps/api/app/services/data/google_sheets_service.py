import json
import logging
import math
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import AuthAccount, User

logger = logging.getLogger(__name__)


def col_letter_to_index(col_str: str) -> int:
    """Converts column letter (A, B, O, AA) to 0-based integer index."""
    col = col_str.strip().upper()
    idx = 0
    for char in col:
        if "A" <= char <= "Z":
            idx = idx * 26 + (ord(char) - ord("A") + 1)
    return max(0, idx - 1)


def index_to_col_letter(col_idx: int) -> str:
    """Converts 0-based column index to letter (0 -> A, 14 -> O)."""
    temp = col_idx + 1
    letter = ""
    while temp > 0:
        mod = (temp - 1) % 26
        letter = chr(65 + mod) + letter
        temp = (temp - mod) // 26
    return letter or "A"


def hex_to_google_rgb(hex_color: str) -> Dict[str, float]:
    """Converts #RRGGBB or #AARRGGBB hex color to Google Sheets float RGB (0.0 - 1.0)."""
    clean = hex_color.replace("#", "").strip().upper()
    if len(clean) == 8:
        clean = clean[2:]  # Strip alpha if present
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        clean = "FEF08A"  # Default yellow

    try:
        r = int(clean[0:2], 16) / 255.0
        g = int(clean[2:4], 16) / 255.0
        b = int(clean[4:6], 16) / 255.0
        return {"red": round(r, 4), "green": round(g, 4), "blue": round(b, 4)}
    except Exception:
        return {"red": 0.9961, "green": 0.9412, "blue": 0.5412}


def google_rgb_to_hex(rgb: Optional[Dict[str, Any]]) -> Optional[str]:
    """Converts Google Sheets float RGB object to #RRGGBB string."""
    if not rgb:
        return None
    r = int(round(rgb.get("red", 0.0) * 255))
    g = int(round(rgb.get("green", 0.0) * 255))
    b = int(round(rgb.get("blue", 0.0) * 255))
    return f"#{r:02X}{g:02X}{b:02X}"


class GoogleSheetsService:
    """
    Real Google Sheets API v4 Integration Engine.
    Handles authenticated cell formatting, batchUpdate, verification, and undo.
    """

    GOOGLE_SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

    # In-memory history of original formatting for undo & clear
    _original_formats_cache: Dict[str, Dict[str, Any]] = {}
    _undo_stacks: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def extract_spreadsheet_id(cls, url_or_id: Optional[str]) -> Optional[str]:
        """Extracts the Google spreadsheetId from URL or raw ID string."""
        if not url_or_id or not url_or_id.strip():
            return None
        text = url_or_id.strip()
        # Direct /d/{id} match
        match = re.search(r"/spreadsheets/d/(?:e/)?([a-zA-Z0-9-_]{15,})", text)
        if match:
            return match.group(1)
        # Query id= match
        parsed = urlparse(text)
        if parsed.query:
            q = parse_qs(parsed.query)
            if "id" in q and q["id"]:
                return q["id"][0]
        # Raw alphanumeric ID check
        if re.fullmatch(r"[a-zA-Z0-9-_]{20,}", text):
            return text
        return None

    @classmethod
    def parse_a1_coordinate(cls, coord: str) -> Tuple[int, int]:
        """
        Parses single A1 coordinate (e.g. 'O36') to 0-based (row_idx, col_idx).
        Example: 'O36' -> (35, 14)
        """
        coord = coord.strip().upper()
        match = re.match(r"^([A-Z]+)(\d+)$", coord)
        if not match:
            return (0, 0)
        col_str, row_str = match.groups()
        row_idx = max(0, int(row_str) - 1)
        col_idx = col_letter_to_index(col_str)
        return (row_idx, col_idx)

    @classmethod
    def parse_a1_range_to_grid(
        cls, sheet_id: int, range_str: str, max_cols: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Converts A1 notation or coordinate into Google Sheets GridRange object.
        Examples:
          - 'O36' -> { sheetId: 0, startRowIndex: 35, endRowIndex: 36, startColumnIndex: 14, endColumnIndex: 15 }
          - 'O9:O36' -> { sheetId: 0, startRowIndex: 8, endRowIndex: 36, startColumnIndex: 14, endColumnIndex: 15 }
          - '36' -> { sheetId: 0, startRowIndex: 35, endRowIndex: 36, startColumnIndex: 0, endColumnIndex: max_cols }
        """
        r_str = range_str.strip().upper()
        if "!" in r_str:
            r_str = r_str.split("!", 1)[1].strip()

        # Case 1: Full row number (e.g. "36")
        if r_str.isdigit():
            row_num = int(r_str)
            return {
                "sheetId": sheet_id,
                "startRowIndex": max(0, row_num - 1),
                "endRowIndex": row_num,
                "startColumnIndex": 0,
                "endColumnIndex": max_cols,
            }

        # Case 2: Range (e.g. "O9:O36" or "A1:G10")
        if ":" in r_str:
            start_part, end_part = r_str.split(":", 1)
            start_row, start_col = cls.parse_a1_coordinate(start_part)
            end_row, end_col = cls.parse_a1_coordinate(end_part)
            return {
                "sheetId": sheet_id,
                "startRowIndex": start_row,
                "endRowIndex": end_row + 1,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col + 1,
            }

        # Case 3: Single cell (e.g. "O36")
        row_idx, col_idx = cls.parse_a1_coordinate(r_str)
        return {
            "sheetId": sheet_id,
            "startRowIndex": row_idx,
            "endRowIndex": row_idx + 1,
            "startColumnIndex": col_idx,
            "endColumnIndex": col_idx + 1,
        }

    @classmethod
    async def get_valid_access_token(
        cls,
        user: Optional[User] = None,
        db: Optional[AsyncSession] = None,
        explicit_token: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolves a valid Google OAuth access token.
        Automatically refreshes token if expired and refresh_token is present.
        Returns: (access_token, error_message)
        """
        if explicit_token and explicit_token.strip():
            return explicit_token.strip(), None

        if not user or not db:
            return None, "NO_AUTHENTICATED_USER"

        stmt = select(AuthAccount).where(
            AuthAccount.user_id == user.id,
            AuthAccount.provider == "google",
        )
        res = await db.execute(stmt)
        auth_acc: Optional[AuthAccount] = res.scalars().first()

        if not auth_acc:
            return None, "GOOGLE_ACCOUNT_NOT_LINKED"

        now = datetime.now(timezone.utc)
        # If token is present and not expired (with 60s buffer)
        if auth_acc.access_token:
            if not auth_acc.token_expiry or auth_acc.token_expiry > now:
                return auth_acc.access_token, None

        # Refresh token if available
        if auth_acc.refresh_token:
            client_id = settings.GOOGLE_CLIENT_ID or os.getenv("GOOGLE_CLIENT_ID", "")
            client_secret = settings.GOOGLE_CLIENT_SECRET or os.getenv("GOOGLE_CLIENT_SECRET", "")
            if client_id and client_secret:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(
                            "https://oauth2.googleapis.com/token",
                            data={
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "refresh_token": auth_acc.refresh_token,
                                "grant_type": "refresh_token",
                            },
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            new_access_token = data.get("access_token")
                            expires_in = int(data.get("expires_in", 3600))
                            auth_acc.access_token = new_access_token
                            auth_acc.token_expiry = datetime.now(timezone.utc)
                            await db.commit()
                            return new_access_token, None
                except Exception as ex:
                    logger.error(f"[GOOGLE_SHEETS_ERROR] Token refresh error: {str(ex)}")

        return auth_acc.access_token, None

    @classmethod
    async def resolve_sheet_metadata(
        cls,
        spreadsheet_id: str,
        sheet_name: str,
        access_token: str,
    ) -> Tuple[Optional[int], Optional[str], int, int]:
        """
        Fetches spreadsheet metadata from Google Sheets API v4.
        Returns: (sheetId_int, canonical_sheet_name, max_row, max_column)
        """
        url = f"{cls.GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}?fields=sheets.properties"
        headers = {"Authorization": f"Bearer {access_token}"}

        logger.info(f"[GOOGLE_SHEETS] Resolving sheet metadata for '{sheet_name}' in {spreadsheet_id}")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"[GOOGLE_SHEETS_ERROR] Failed to fetch metadata: HTTP {resp.status_code} {resp.text}")
                return None, None, 1000, 26

            data = resp.json()
            sheets = data.get("sheets", [])

            # 1. Exact match
            for s in sheets:
                prop = s.get("properties", {})
                title = prop.get("title", "")
                if title == sheet_name:
                    gp = prop.get("gridProperties", {})
                    return prop.get("sheetId", 0), title, gp.get("rowCount", 1000), gp.get("columnCount", 26)

            # 2. Case-insensitive / normalized match
            target_norm = sheet_name.strip().lower()
            for s in sheets:
                prop = s.get("properties", {})
                title = prop.get("title", "")
                if title.strip().lower() == target_norm:
                    gp = prop.get("gridProperties", {})
                    return prop.get("sheetId", 0), title, gp.get("rowCount", 1000), gp.get("columnCount", 26)

            # 3. Fallback to first sheet if only 1 exists
            if sheets:
                first_prop = sheets[0].get("properties", {})
                gp = first_prop.get("gridProperties", {})
                return first_prop.get("sheetId", 0), first_prop.get("title", "Sheet1"), gp.get("rowCount", 1000), gp.get("columnCount", 26)

        return 0, sheet_name, 1000, 26

    @classmethod
    async def get_cell_backgrounds(
        cls,
        spreadsheet_id: str,
        sheet_name: str,
        cell_addresses: List[str],
        access_token: str,
    ) -> Dict[str, Optional[Dict[str, float]]]:
        """
        Reads existing background colors of specific cells before formatting.
        Returns: { 'O36': { 'red': 1.0, ... } or None }
        """
        results: Dict[str, Optional[Dict[str, float]]] = {}
        if not cell_addresses:
            return results

        ranges = [f"'{sheet_name}'!{addr}" for addr in cell_addresses[:50]]
        ranges_query = "&".join(f"ranges={quote(r)}" for r in ranges)
        url = f"{cls.GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}?{ranges_query}&fields=sheets(data(rowData(values(userEnteredFormat(backgroundColor,backgroundColorStyle)))))"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    sheets_data = data.get("sheets", [])
                    idx = 0
                    for s in sheets_data:
                        for d in s.get("data", []):
                            for r in d.get("rowData", []):
                                for v in r.get("values", []):
                                    if idx < len(cell_addresses):
                                        addr = cell_addresses[idx]
                                        bg = v.get("userEnteredFormat", {}).get("backgroundColor")
                                        results[addr] = bg
                                        idx += 1
        except Exception as ex:
            logger.warning(f"[GOOGLE_SHEETS_WARN] Could not fetch previous cell formats: {str(ex)}")

        return results

    @classmethod
    async def highlight_cells(
        cls,
        spreadsheet_id: str,
        sheet_name: str,
        cell_addresses: List[str],
        color_hex: str = "#FEF08A",
        access_token: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes real Google Sheets API batchUpdate with repeatCell.
        Verifies formatting by reading back cell properties.
        """
        logger.info(f"[GOOGLE_SHEETS] highlight_cells started for spreadsheetId={spreadsheet_id}, sheet={sheet_name}, cells={cell_addresses}, color={color_hex}")

        if not access_token:
            logger.error("[GOOGLE_SHEETS_ERROR] Missing access token")
            return {
                "success": False,
                "synced_to_google_sheets": False,
                "verified_on_google_sheets": False,
                "error": "Ứng dụng hiện chưa có quyền chỉnh sửa Google Sheets. Vui lòng cấp quyền để đồng bộ đánh dấu.",
            }

        sheet_id, canonical_name, max_rows, max_cols = await cls.resolve_sheet_metadata(
            spreadsheet_id, sheet_name, access_token
        )
        if sheet_id is None:
            sheet_id = 0
            canonical_name = sheet_name

        rgb = hex_to_google_rgb(color_hex)
        resolved_cells: List[Dict[str, Any]] = []
        batch_requests: List[Dict[str, Any]] = []

        # Read previous formatting before update
        prev_formats = await cls.get_cell_backgrounds(spreadsheet_id, canonical_name or sheet_name, cell_addresses, access_token)
        cache_key = f"{spreadsheet_id}:{canonical_name or sheet_name}"
        if cache_key not in cls._original_formats_cache:
            cls._original_formats_cache[cache_key] = {}
        for addr, prev_bg in prev_formats.items():
            if addr not in cls._original_formats_cache[cache_key]:
                cls._original_formats_cache[cache_key][addr] = prev_bg

        for addr in cell_addresses:
            grid_range = cls.parse_a1_range_to_grid(sheet_id, addr, max_cols=max_cols)
            if not grid_range:
                continue

            r_idx, c_idx = cls.parse_a1_coordinate(addr) if not addr.isdigit() else (int(addr) - 1, 0)
            col_letter = index_to_col_letter(grid_range["startColumnIndex"])
            row_num = grid_range["startRowIndex"] + 1

            resolved_cells.append({
                "sheetName": canonical_name or sheet_name,
                "sheetId": sheet_id,
                "row": row_num,
                "column": col_letter,
                "cell": addr,
                "a1Range": f"'{canonical_name or sheet_name}'!{addr}",
                "startRowIndex": grid_range["startRowIndex"],
                "endRowIndex": grid_range["endRowIndex"],
                "startColumnIndex": grid_range["startColumnIndex"],
                "endColumnIndex": grid_range["endColumnIndex"],
            })

            batch_requests.append({
                "repeatCell": {
                    "range": grid_range,
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": rgb,
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor",
                }
            })

            logger.info(
                f"[GOOGLE_SHEETS] spreadsheetId={spreadsheet_id} sheetName={canonical_name} "
                f"sheetId={sheet_id} a1Range='{canonical_name}'!{addr} "
                f"startRowIndex={grid_range['startRowIndex']} endRowIndex={grid_range['endRowIndex']} "
                f"startColumnIndex={grid_range['startColumnIndex']} endColumnIndex={grid_range['endColumnIndex']}"
            )

        if not batch_requests:
            return {
                "success": False,
                "synced_to_google_sheets": False,
                "verified_on_google_sheets": False,
                "error": "Không có ô hợp lệ để đánh dấu.",
            }

        # Execute batchUpdate
        url = f"{cls.GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        body = {"requests": batch_requests}

        logger.info(f"[GOOGLE_SHEETS] batchUpdate started ({len(batch_requests)} requests)")
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code != 200:
                    err_msg = resp.text
                    logger.error(f"[GOOGLE_SHEETS_ERROR] batchUpdate failed: HTTP {resp.status_code} {err_msg}")
                    return {
                        "success": False,
                        "synced_to_google_sheets": False,
                        "verified_on_google_sheets": False,
                        "error": f"Lỗi Google Sheets API (HTTP {resp.status_code}): {err_msg}",
                        "status_code": resp.status_code,
                    }

                logger.info("[GOOGLE_SHEETS] batchUpdate success")

                # Verification step
                logger.info("[GOOGLE_SHEETS] verification started")
                verified_formats = await cls.get_cell_backgrounds(
                    spreadsheet_id, canonical_name or sheet_name, cell_addresses[:5], access_token
                )
                is_verified = True
                for addr in cell_addresses[:5]:
                    got_bg = verified_formats.get(addr)
                    if got_bg:
                        diff = (
                            abs(got_bg.get("red", 0) - rgb["red"])
                            + abs(got_bg.get("green", 0) - rgb["green"])
                            + abs(got_bg.get("blue", 0) - rgb["blue"])
                        )
                        if diff > 0.15:
                            is_verified = False
                            break

                logger.info(f"[GOOGLE_SHEETS] verification {'success' if is_verified else 'mismatch'}")

                # Save undo entry
                sid = session_id or "default"
                cls._undo_stacks.setdefault(sid, []).append({
                    "spreadsheet_id": spreadsheet_id,
                    "sheet_id": sheet_id,
                    "sheet_name": canonical_name or sheet_name,
                    "cell_addresses": cell_addresses,
                    "prev_formats": prev_formats,
                })

                return {
                    "success": True,
                    "synced_to_google_sheets": True,
                    "verified_on_google_sheets": is_verified,
                    "spreadsheet_id": spreadsheet_id,
                    "sheet_id": sheet_id,
                    "sheet_name": canonical_name or sheet_name,
                    "highlighted_count": len(cell_addresses),
                    "cells": resolved_cells,
                    "color_hex": color_hex,
                    "rgb": rgb,
                }

        except Exception as ex:
            logger.error(f"[GOOGLE_SHEETS_ERROR] Exception during batchUpdate: {str(ex)}")
            return {
                "success": False,
                "synced_to_google_sheets": False,
                "verified_on_google_sheets": False,
                "error": f"Lỗi kết nối Google Sheets: {str(ex)}",
            }

    @classmethod
    async def undo_highlight(
        cls,
        session_id: str = "default",
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reverts the last formatting action on Google Sheets by restoring previous cell colors.
        """
        stack = cls._undo_stacks.get(session_id, [])
        if not stack:
            return {"ok": False, "message": "Không có thao tác Google Sheets nào để hoàn tác."}

        last_item = stack.pop()
        spreadsheet_id = last_item["spreadsheet_id"]
        sheet_id = last_item["sheet_id"]
        canonical_name = last_item["sheet_name"]
        prev_formats = last_item.get("prev_formats", {})

        if not access_token:
            return {"ok": False, "message": "Thiếu token để hoàn tác trên Google Sheets."}

        batch_requests = []
        for addr, prev_bg in prev_formats.items():
            grid_range = cls.parse_a1_range_to_grid(sheet_id, addr)
            if not grid_range:
                continue

            if prev_bg:
                batch_requests.append({
                    "repeatCell": {
                        "range": grid_range,
                        "cell": {"userEnteredFormat": {"backgroundColor": prev_bg}},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                })
            else:
                # Clear background formatting field
                batch_requests.append({
                    "repeatCell": {
                        "range": grid_range,
                        "cell": {},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                })

        if not batch_requests:
            return {"ok": True, "restored_count": 0}

        url = f"{cls.GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json={"requests": batch_requests})
            if resp.status_code == 200:
                logger.info(f"[GOOGLE_SHEETS] Undo restored {len(batch_requests)} cells on {spreadsheet_id}")
                return {
                    "ok": True,
                    "restored_count": len(batch_requests),
                    "sheet": canonical_name,
                    "spreadsheet_id": spreadsheet_id,
                }
            return {"ok": False, "error": f"Google Sheets undo error: {resp.text}"}

    @classmethod
    async def clear_all_highlights(
        cls,
        spreadsheet_id: str,
        sheet_name: str,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clears all highlight layers by restoring the original baseline formats recorded in cache.
        """
        if not access_token:
            return {"ok": False, "message": "Thiếu token để xóa màu trên Google Sheets."}

        sheet_id, canonical_name, max_rows, max_cols = await cls.resolve_sheet_metadata(
            spreadsheet_id, sheet_name, access_token
        )
        cache_key = f"{spreadsheet_id}:{canonical_name or sheet_name}"
        orig_map = cls._original_formats_cache.get(cache_key, {})

        batch_requests = []
        for addr, orig_bg in orig_map.items():
            grid_range = cls.parse_a1_range_to_grid(sheet_id or 0, addr)
            if not grid_range:
                continue

            if orig_bg:
                batch_requests.append({
                    "repeatCell": {
                        "range": grid_range,
                        "cell": {"userEnteredFormat": {"backgroundColor": orig_bg}},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                })
            else:
                batch_requests.append({
                    "repeatCell": {
                        "range": grid_range,
                        "cell": {},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                })

        if not batch_requests:
            return {"ok": True, "cleared_count": 0}

        url = f"{cls.GOOGLE_SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json={"requests": batch_requests})
            if resp.status_code == 200:
                cls._original_formats_cache.pop(cache_key, None)
                return {"ok": True, "cleared_count": len(batch_requests)}
            return {"ok": False, "error": f"Clear highlights error: {resp.text}"}


google_sheets_service = GoogleSheetsService()
