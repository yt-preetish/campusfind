import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "campusfind.db")


def get_db():
    """Get database connection with row factory and foreign keys enabled."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    """Initialize database with all required tables and indexes."""
    con = get_db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('lost','found')),
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        location TEXT NOT NULL,
        date_time TEXT NOT NULL,
        image TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        created_at TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        building TEXT,
        color TEXT,
        brand TEXT,
        visual_features TEXT,
        -- AI Features
        image_embedding BLOB,
        text_embedding BLOB,
        ocr_text TEXT,
        ocr_masked TEXT,
        item_fingerprint TEXT,
        ai_model_version TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        claimant_id INTEGER NOT NULL,
        answer TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE,
        FOREIGN KEY(claimant_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        link TEXT,
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        notification_type TEXT DEFAULT 'info',
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS ai_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL UNIQUE,
        suggested_category TEXT,
        suggested_color TEXT,
        suggested_brand TEXT,
        visual_characteristics TEXT,
        item_fingerprint TEXT,
        confidence_score REAL,
        analysis_method TEXT DEFAULT 'local',
        model_version TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS handover_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        claim_id INTEGER NOT NULL,
        handover_id TEXT UNIQUE NOT NULL,
        handover_token TEXT NOT NULL,
        finder_confirmed INTEGER DEFAULT 0,
        claimant_confirmed INTEGER DEFAULT 0,
        finder_confirmed_at TEXT,
        claimant_confirmed_at TEXT,
        completed_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE,
        FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS item_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lost_item_id INTEGER NOT NULL,
        found_item_id INTEGER NOT NULL,
        overall_score REAL NOT NULL,
        confidence_score REAL,
        text_similarity REAL,
        image_similarity REAL,
        ocr_similarity REAL,
        location_similarity REAL,
        date_similarity REAL,
        category_match REAL,
        visual_similarity REAL,
        explanation TEXT,
        evidence TEXT,
        uncertainties TEXT,
        model_version TEXT,
        created_at TEXT NOT NULL,
        human_feedback TEXT DEFAULT 'pending',
        human_feedback_at TEXT,
        FOREIGN KEY(lost_item_id) REFERENCES items(id) ON DELETE CASCADE,
        FOREIGN KEY(found_item_id) REFERENCES items(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS admin_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        claim_id INTEGER,
        flag_type TEXT NOT NULL,
        reason TEXT,
        risk_score REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        resolved_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE,
        FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE
    );
    """)
    
    # Add indexes for performance
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_type ON items(type)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_status ON items(status)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_item_matches_score ON item_matches(overall_score)")
    
    con.commit()
    con.close()
