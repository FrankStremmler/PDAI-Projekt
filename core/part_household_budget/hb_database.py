import os
import shutil
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from .hb_model_db import Base, Status, Category, SubCategory, DbSync
from standards_and_constants.hb_prompts_constants import DB_NAME, DB_PATH, TEMP_DB_PATH, DRIVE_FOLDER_NAME
from standards_and_constants.hb_prompts_constants import RECEIPTS_FOLDER, STATEMENTS_FOLDER
from sqlalchemy import text


class DatabaseController:
    def __init__(self, use_temp: bool = False, drive_service=None):
        self.use_temp = use_temp
        self.drive_service = drive_service
        self.use_drive = drive_service is not None
        self.master_db_path = str(DB_PATH)
        self.working_db_path = TEMP_DB_PATH if (use_temp or self.use_drive) else self.master_db_path
        self.db_uri = f"sqlite:///{self.working_db_path}"
        self._engine = None
        self._session = None
        self._drive_folder_id = None
        self._drive_file_id = None
        self._drive_db_exists = False

    def _ensure_drive_folder(self):
        if self._drive_folder_id:
            return
        try:
            results = self.drive_service.files().list(
                q=f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name)"
            ).execute()
            files = results.get("files", [])
            if files:
                self._drive_folder_id = files[0]["id"]
                print(f"[DB] Drive-Ordner '{DRIVE_FOLDER_NAME}' gefunden (ID: {self._drive_folder_id})")
            else:
                folder = self.drive_service.files().create(
                    body={
                        "name": DRIVE_FOLDER_NAME,
                        "mimeType": "application/vnd.google-apps.folder"
                    },
                    fields="id"
                ).execute()
                self._drive_folder_id = folder["id"]
                print(f"[DB] Drive-Ordner '{DRIVE_FOLDER_NAME}' angelegt (ID: {self._drive_folder_id})")
        except Exception as e:
            print(f"[DB] Fehler beim Zugriff auf Drive-Ordner: {e}")
            raise

    def _ensure_drive_db_file(self):
        if self._drive_folder_id is None:
            return False
        try:
            results = self.drive_service.files().list(
                q=f"name='{DB_NAME}' and '{self._drive_folder_id}' in parents and trashed=false",
                fields="files(id, name)"
            ).execute()
            files = results.get("files", [])
            if files:
                self._drive_file_id = files[0]["id"]
                self._drive_db_exists = True
                print(f"[DB] Drive-DB gefunden (ID: {self._drive_file_id})")
                return True
            else:
                self._drive_db_exists = False
                print("[DB] Keine DB auf Drive gefunden.")
                return False
        except Exception as e:
            print(f"[DB] Fehler bei Drive-DB-Suche: {e}")
            return False

    def _download_from_drive(self):
        if not self._drive_file_id:
            return
        try:
            from googleapiclient.http import MediaIoBaseDownload
            if os.path.exists(self.working_db_path):
                os.remove(self.working_db_path)
            request = self.drive_service.files().get_media(fileId=self._drive_file_id)
            with open(self.working_db_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            print(f"[DB] DB von Drive heruntergeladen nach: {self.working_db_path}")
        except Exception as e:
            print(f"[DB] Fehler beim Download von Drive: {e}")
            raise

    def _upload_to_drive(self):
        if not self._drive_folder_id:
            return
        if not os.path.exists(self.working_db_path):
            return
        from googleapiclient.http import MediaFileUpload
        try:
            old_name = f"{DB_NAME}.old"
            old_results = self.drive_service.files().list(
                q=f"name='{old_name}' and '{self._drive_folder_id}' in parents and trashed=false",
                fields="files(id, name)"
            ).execute()
            for f in old_results.get("files", []):
                self.drive_service.files().delete(fileId=f["id"]).execute()
                print(f"[DB] Alte .old-Datei gelöscht (ID: {f['id']})")

            if self._drive_file_id:
                self.drive_service.files().update(
                    fileId=self._drive_file_id,
                    body={"name": old_name}
                ).execute()
                print(f"[DB] Vorherige DB umbenannt in: {old_name}")

            media = MediaFileUpload(self.working_db_path, resumable=True)
            uploaded = self.drive_service.files().create(
                body={
                    "name": DB_NAME,
                    "parents": [self._drive_folder_id]
                },
                media_body=media,
                fields="id"
            ).execute()
            self._drive_file_id = uploaded["id"]
            self._drive_db_exists = True
            print(f"[DB] DB hochgeladen zu Drive (ID: {self._drive_file_id})")
        except Exception as e:
            print(f"[DB] Fehler beim Upload zu Drive: {e}")

    def _read_last_update(self, db_path: str):
        if not os.path.exists(db_path):
            return None
        engine = None
        try:
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                row = conn.execute(text("SELECT last_update FROM db_sync WHERE id = 1")).fetchone()
                if row:
                    return row[0]
                return None
        except Exception:
            return None
        finally:
            if engine:
                engine.dispose()

    def update_last_update(self):
        with Session(self.get_engine()) as session:
            sync = session.query(DbSync).first()
            if sync:
                sync.last_update = datetime.utcnow()
            else:
                session.add(DbSync(id=1, last_update=datetime.utcnow()))
            session.commit()

    def prepare_working_directory(self):
        if self.use_drive:
            try:
                self._ensure_drive_folder()
                exists_on_drive = self._ensure_drive_db_file()

                if exists_on_drive:
                    print("[DB] Lade DB von Google Drive in Temp-Verzeichnis...")
                    self._download_from_drive()

                drive_ts = self._read_last_update(self.working_db_path) if exists_on_drive else None
                local_ts = self._read_last_update(self.master_db_path)

                if drive_ts is not None and (local_ts is None or drive_ts > local_ts):
                    print("[DB] Drive-DB ist aktueller, überschreibe lokale Master-DB")
                    shutil.copy2(self.working_db_path, self.master_db_path)
                elif local_ts is not None and (drive_ts is None or local_ts >= drive_ts):
                    print("[DB] Lokale DB ist aktueller, kopiere in Temp")
                    if os.path.exists(self.working_db_path):
                        os.remove(self.working_db_path)
                    shutil.copy2(self.master_db_path, self.working_db_path)
                else:
                    if os.path.exists(self.working_db_path):
                        os.remove(self.working_db_path)
                    print("[DB] Keine DB vorhanden. Lege neue an.")
            except Exception as e:
                print(f"[DB] Drive-Fehler, verwende lokale DB: {e}")
                self.use_drive = False
                self.drive_service = None
                self.working_db_path = self.master_db_path
                self.db_uri = f"sqlite:///{self.working_db_path}"
                if self.use_temp and os.path.exists(self.master_db_path):
                    shutil.copy2(self.master_db_path, self.working_db_path)
        elif self.use_temp:
            if os.path.exists(self.master_db_path):
                print(f"[DB] Kopiere DB in Temp: {self.working_db_path}")
                shutil.copy2(self.master_db_path, self.working_db_path)
            else:
                print("[DB] Keine Master-DB gefunden. Lege neue an.")

    def create_db(self):
        self.prepare_working_directory()
        self._engine = create_engine(self.db_uri, echo=False)
        Base.metadata.create_all(self._engine)
        self._run_migrations()
        self._seed_defaults()
        self._ensure_directories()
        print(f"[DB] Datenbank initialisiert: {self.working_db_path}")

    def _run_migrations(self):
        inspector = inspect(self._engine)
        tables = inspector.get_table_names()

        with self._engine.connect() as conn:
            if "receipt" in tables:
                cols = {c["name"]: c["type"] for c in inspector.get_columns("receipt")}
                if "merchant" not in cols:
                    print("[DB] Migration: füge receipt.merchant hinzu")
                    conn.execute(text("ALTER TABLE receipt ADD COLUMN merchant VARCHAR(100) NOT NULL DEFAULT ''"))
                    conn.commit()
                if "datum" in cols and str(cols["datum"]).upper() == "DATE":
                    print("[DB] Migration: receipt.datum DATE -> DATETIME")
                    conn.execute(text("SAVEPOINT receipt_datum_migration"))
                    conn.execute(text(
                        "CREATE TABLE receipt_new ("
                        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                        "  merchant VARCHAR(100) NOT NULL,"
                        "  datum DATETIME NOT NULL,"
                        "  total_sum NUMERIC(10,2) NOT NULL,"
                        "  payment_method INTEGER NOT NULL DEFAULT 0,"
                        "  status_id INTEGER NOT NULL REFERENCES status(id),"
                        "  sync_id INTEGER REFERENCES sync_status(id)"
                        ")"
                    ))
                    old_cols = [c["name"] for c in inspector.get_columns("receipt")]
                    col_list = ", ".join(f'"{c}"' for c in old_cols if c != "id")
                    conn.execute(text(
                        f"INSERT INTO receipt_new (id, {col_list}) "
                        f"SELECT id, {col_list} FROM receipt"
                    ))
                    conn.execute(text("DROP TABLE receipt"))
                    conn.execute(text("ALTER TABLE receipt_new RENAME TO receipt"))
                    conn.execute(text("RELEASE receipt_datum_migration"))
                    conn.commit()

        with self._engine.connect() as conn:
            if "sync_status" in tables:
                cols = [c["name"] for c in inspector.get_columns("sync_status")]
                if "source_name" in cols:
                    try:
                        conn.execute(text("DROP TABLE IF EXISTS sync_status_old"))
                        conn.execute(text("ALTER TABLE sync_status RENAME TO sync_status_old"))
                        conn.commit()
                        print("[DB] Migration: sync_status umbenannt")
                    except Exception as e:
                        print(f"[DB] Migrationswarnung: {e}")

            renames = {
                "bankaccount": "bank_account",
                "bankstatement": "bank_statement",
                "statementposition": "bank_statement_position",
                "salestype": "salestype_old",
                "allocationprofile": "allocation_profile",
            }
            for old, new in renames.items():
                if old in tables and new not in tables:
                    try:
                        conn.execute(text(f"ALTER TABLE {old} RENAME TO {new}"))
                        conn.commit()
                        print(f"[DB] Migration: {old} -> {new}")
                    except Exception as e:
                        print(f"[DB] Migrationswarnung ({old}): {e}")

    def _seed_defaults(self):
        with Session(self._engine) as session:
            for name in ["pending", "booked", "suspicious"]:
                existing = session.query(Status).filter(Status.name == name).first()
                if not existing:
                    session.add(Status(name=name))
            sync = session.query(DbSync).first()
            if not sync:
                session.add(DbSync(id=1, last_update=datetime.utcnow()))
            session.commit()

    def _ensure_directories(self):
        for d in [RECEIPTS_FOLDER, STATEMENTS_FOLDER]:
            if not os.path.exists(d):
                try:
                    os.makedirs(d)
                except OSError:
                    pass

    def get_engine(self):
        if self._engine is None:
            self.create_db()
        return self._engine

    def get_session(self) -> Session:
        return Session(self.get_engine())

    def save_and_sync_back(self):
        if (self.use_drive or self.use_temp) and os.path.exists(self.working_db_path):
            print(f"[DB] Sync zurück zur Master-DB: {self.master_db_path}")
            shutil.copy2(self.working_db_path, self.master_db_path)

    def save_to_drive(self):
        if not self.use_drive:
            return
        self.save_and_sync_back()
        self._upload_to_drive()

    def close_session(self):
        if self._session:
            self._session.close()
            self._session = None

    def dispose(self):
        if self._engine:
            self._engine.dispose()
            self._engine = None


def ensure_database(use_temp: bool = False, drive_service=None) -> DatabaseController:
    controller = DatabaseController(use_temp=use_temp, drive_service=drive_service)
    controller.create_db()
    return controller


def get_database_path() -> str:
    return str(DB_PATH)


def get_temp_database_path() -> str:
    return TEMP_DB_PATH
