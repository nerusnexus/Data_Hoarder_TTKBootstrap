import sqlite3
import instaloader
import time
import traceback
from pathlib import Path
from datetime import datetime
from config import BASE_DIR
from services.db.db_manager import DatabaseManager


class InstaService:
    def __init__(self, settings_service=None):
        self.settings = settings_service  # Save the reference
        self.ig_dir = BASE_DIR / "Data" / "Instagram"
        self.ig_dir.mkdir(parents=True, exist_ok=True)

        self.L = instaloader.Instaloader(
            dirname_pattern=str(self.ig_dir / "{profile}"),
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=True,
            download_geotags=True,
            download_comments=True,
            save_metadata=True,
            compress_json=False
        )

        self._authenticate()  # Log in when the service starts!

    def _authenticate(self):
        if not self.settings: return
        user = self.settings.get_ig_username()
        pwd = self.settings.get_ig_password()

        if user and pwd:
            try:
                # Try to load a saved session file to avoid re-logging in every time
                self.L.load_session_from_file(user)
            except FileNotFoundError:
                try:
                    # If no session file, do a full login and save the session
                    self.L.login(user, pwd)
                    self.L.save_session_to_file()
                except Exception as e:
                    print(f"Instagram Login Failed: {e}")

    @staticmethod
    def get_connection():
        conn = DatabaseManager.get_connection()
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_accounts(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM ig_accounts").fetchall()
            return [dict(row) for row in rows]

    def add_account(self, username: str):
        username = username.strip().replace("@", "")

        try:
            profile = instaloader.Profile.from_username(self.L.context, username)

            account_dir = self.ig_dir / profile.username
            account_dir.mkdir(parents=True, exist_ok=True)

            # Download profile picture
            self.L.download_profilepic(profile)
            pfp_path = str(account_dir / f"{profile.username}_profile_pic.jpg")

            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO ig_accounts (username, full_name, user_id, biography, followers, following, profile_pic_path, is_private, last_sync_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (profile.username, profile.full_name, str(profile.userid), profile.biography,
                      profile.followers, profile.followees, pfp_path, int(profile.is_private), "Never"))
                conn.commit()

            return True, f"Successfully added @{profile.username}"
        except instaloader.exceptions.ProfileNotExistsException:
            return False, "Profile does not exist."
        except sqlite3.IntegrityError:
            return False, "Account is already in the database."
        except Exception as e:
            return False, f"Error: {e}"

    def delete_account(self, username: str):
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("DELETE FROM ig_accounts WHERE username = ?", (username,))
            conn.commit()

    def sync_account(self, username: str, log_callback=None):
        try:
            if log_callback: log_callback(f"Connecting to Instagram to fetch @{username}...")

            profile = instaloader.Profile.from_username(self.L.context, username)

            with self.get_connection() as conn:
                account_row = conn.execute("SELECT id FROM ig_accounts WHERE username = ?", (username,)).fetchone()
                if not account_row: return False, "Account not in DB"
                account_id = account_row["id"]

                # Update basic profile stats
                now_str = datetime.now().isoformat()
                conn.execute("""
                    UPDATE ig_accounts SET full_name=?, biography=?, followers=?, following=?, is_private=?, last_sync_date=?
                    WHERE id=?
                """, (profile.full_name, profile.biography, profile.followers, profile.followees,
                      int(profile.is_private), now_str, account_id))
                conn.commit()

            if profile.is_private:
                if log_callback: log_callback("Account is private and you are not logged in. Cannot fetch posts.")
                return False, "Account is private."

            # Fetch Stories & Highlights (These process as a batch, Instaloader handles its own minor delays here)
            if log_callback: log_callback("Checking for Stories and Highlights...")
            try:
                self.L.download_stories(userids=[profile.userid], filename_target=f"{profile.username}/Stories")
                self.L.download_highlights(user=profile)
            except Exception as e:
                if log_callback: log_callback(f"Could not fetch stories (Login likely required): {e}")

            # Fetch Posts with EXTREME SAFETY (30-second delay)
            if log_callback: log_callback("Fetching posts list...")

            post_count = 0
            for post in profile.get_posts():
                with self.get_connection() as conn:
                    # Check if we already downloaded this post
                    exists = conn.execute("SELECT id FROM ig_posts WHERE shortcode = ?", (post.shortcode,)).fetchone()

                if not exists:
                    if log_callback: log_callback(f"Downloading new post: {post.shortcode} ({post.typename})")

                    # Command Instaloader to download this single post
                    success = self.L.download_post(post, target=profile.username)

                    if success:
                        with self.get_connection() as conn:
                            conn.execute("""
                                INSERT INTO ig_posts (account_id, shortcode, type, text, timestamp, likes, comments, is_downloaded)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                            """, (account_id, post.shortcode, post.typename, post.caption, str(post.date_utc),
                                  post.likes, post.comments))
                            conn.commit()

                        post_count += 1
                        if log_callback: log_callback(
                            f"Post {post.shortcode} saved. Sleeping for 30 seconds for safety...")

                        # EXTREME SAFETY DELAY
                        time.sleep(30)
                else:
                    # If it already exists in DB, we skip it and don't trigger the 30-second delay.
                    pass

            if log_callback: log_callback(f"Sync complete. Downloaded {post_count} new posts.")
            return True, f"Successfully synced @{username}"

        except Exception as e:
            err_trace = traceback.format_exc()
            if log_callback: log_callback(f"CRITICAL ERROR: {e}\n{err_trace}")
            return False, f"Sync failed: {e}"