import json
import sqlite3
import re
from pathlib import Path


class AddChannelService:
    def __init__(self, db_path: Path, metadata_path: Path, ytdlp_service):
        self.db_path = db_path
        self.metadata_path = metadata_path
        self.ytdlp = ytdlp_service

    def _extract_all_videos(self, entries):
        """Función auxiliar para encontrar videos en estructuras anidadas."""
        videos = []
        for entry in entries:
            if not entry:
                continue
            # Si es un video (tipo 'url'), lo añadimos
            if entry.get("_type") == "url":
                videos.append(entry)
            # Si es una sub-lista (como 'Videos' o 'Shorts'), buscamos dentro
            elif "entries" in entry:
                videos.extend(self._extract_all_videos(entry["entries"]))
        return videos

    def add_channel(self, group_name: str, url: str):
        if not url:
            raise ValueError("La URL no puede estar vacía")

        # 1. Obtener metadatos completos
        meta = self.ytdlp.fetch_channel_metadata(url)

        # 2. Extraer identificadores según tu nueva convención
        channel_id = meta.get("channel_id") or meta.get("id")
        handle = meta.get("uploader_id") or meta.get("id")
        title = meta.get("title") or meta.get("channel") or "Unknown"

        # Nombre del archivo: channel_id (@handle).json
        filename_base = f"{channel_id} ({handle})" if handle and handle != channel_id else channel_id
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename_base)

        # 3. Guardar el JSON maestro en Data/Metadata/
        json_file = self.metadata_path / f"{safe_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

        # 4. Poblar la base de datos
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insertar o actualizar metadatos del canal
            cursor.execute(
                """INSERT OR REPLACE INTO channels (
                    group_name, name, handle, channel_id, url, 
                    title, follower_count, description, tags, thumbnails
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    group_name,
                    title,
                    handle,
                    channel_id,
                    url,
                    title,
                    meta.get("channel_follower_count"),
                    meta.get("description"),
                    json.dumps(meta.get("tags", [])),
                    json.dumps(meta.get("thumbnails", []))
                )
            )

            # 5. Extraer y guardar todos los videos reales (aplanando la estructura)
            all_videos = self._extract_all_videos(meta.get("entries", []))

            for video in all_videos:
                cursor.execute(
                    """INSERT OR IGNORE INTO videos (
                        channel_name, video_id, title, url, view_count, thumbnails
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        title,
                        video.get("id"),
                        video.get("title"),
                        video.get("url"),
                        video.get("view_count"),
                        json.dumps(video.get("thumbnails", []))
                    )
                )

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Error de base de datos: {e}")
        finally:
            conn.close()

        return title

    def get_channels_by_group(self, group_name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM channels WHERE group_name = ?", (group_name,))
        channels = cursor.fetchall()
        conn.close()
        return [c[0] for c in channels]

    def delete_channel(self, channel_name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channels WHERE name = ?", (channel_name,))
        conn.commit()
        conn.close()