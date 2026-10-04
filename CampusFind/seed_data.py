"""
Demo seed data system for CampusFind AI.
Run this script to populate the database with sample data for testing.
"""

import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import get_db

def seed_users():
    """Seed demo users."""
    con = get_db()
    now = datetime.now().isoformat(timespec="seconds")
    
    users = [
        ("Campus Admin", "admin@campusfind.local", generate_password_hash("admin123"), "admin", now),
        ("Demo Student", "student@campusfind.local", generate_password_hash("student123"), "student", now),
        ("John Smith", "john@campus.edu", generate_password_hash("john123"), "student", now),
        ("Jane Doe", "jane@campus.edu", generate_password_hash("jane123"), "student", now),
        ("Mike Johnson", "mike@campus.edu", generate_password_hash("mike123"), "student", now),
    ]
    
    for name, email, password, role, created_at in users:
        try:
            con.execute(
                "INSERT OR IGNORE INTO users(name, email, password, role, created_at) VALUES(?,?,?,?,?)",
                (name, email, password, role, created_at)
            )
        except Exception as e:
            print(f"Error adding user {name}: {e}")
    
    con.commit()
    print("✓ Users seeded")
    return con

def seed_items(con):
    """Seed demo items."""
    now = datetime.now()
    
    items = [
        # Lost items
        (1, "lost", "Black iPhone 13 Pro", "Electronics", "Black iPhone 13 Pro with cracked screen protector. Last seen near the library entrance.", "Library", (now - timedelta(hours=3)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Apple", "iPhone 13 Pro", "Black", "Cracked screen protector", "Library"),
        (1, "lost", "Blue Nike Backpack", "Bags", "Blue Nike backpack with laptop compartment. Contains textbooks and a water bottle.", "Cafeteria", (now - timedelta(hours=6)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Nike", "Sport Backpack", "Blue", "Laptop compartment", "Cafeteria"),
        (2, "lost", "Student ID Card", "ID Card", "Student ID card with photo. Name: John Smith, ID: 2024001", "Main Block", (now - timedelta(hours=12)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), None, None, None, None, "Main Block"),
        (3, "lost", "Brown Leather Wallet", "Wallet", "Brown leather wallet containing student ID, credit cards, and some cash.", "Parking", (now - timedelta(days=1)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), None, None, "Brown", "Leather texture", "Parking"),
        (4, "lost", "AirPods Pro Case", "Electronics", "White AirPods Pro case with initials 'JD' engraved on back.", "Sports Ground", (now - timedelta(days=2)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Apple", "AirPods Pro", "White", "JD engraved", "Sports Ground"),
        
        # Found items
        (2, "found", "Black iPhone 13 Pro", "Electronics", "Found black iPhone 13 Pro near library entrance. Has a cracked screen protector.", "Library", (now - timedelta(hours=2)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Apple", "iPhone 13 Pro", "Black", "Cracked screen protector", "Library"),
        (3, "found", "Blue Nike Backpack", "Bags", "Found blue Nike backpack in cafeteria. Contains textbooks and water bottle.", "Cafeteria", (now - timedelta(hours=5)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Nike", "Sport Backpack", "Blue", "Laptop compartment", "Cafeteria"),
        (4, "found", "Student ID Card", "ID Card", "Found student ID card in Main Block hallway. Name: John Smith, ID: 2024001", "Main Block", (now - timedelta(hours=10)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), None, None, None, None, "Main Block"),
        (5, "found", "Brown Leather Wallet", "Wallet", "Found brown leather wallet in parking area. Contains ID and cards.", "Parking", (now - timedelta(days=1, hours=20)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), None, None, "Brown", "Leather texture", "Parking"),
        (2, "found", "White AirPods Case", "Electronics", "Found white AirPods case at sports ground. Has initials on back.", "Sports Ground", (now - timedelta(days=2, hours=4)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Apple", "AirPods Pro", "White", "JD engraved", "Sports Ground"),
        
        # Additional items for variety
        (1, "found", "Red Water Bottle", "Accessories", "Red metal water bottle with carabiner clip.", "Library", (now - timedelta(hours=8)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), None, None, "Red", "Carabiner clip", "Library"),
        (3, "lost", "Math Textbook", "Books", "Calculus textbook - Stewart 8th edition. Has handwritten notes.", "Labs", (now - timedelta(days=3)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), None, None, None, "Handwritten notes", "Labs"),
        (4, "found", "Car Keys", "Keys", "Set of car keys with Toyota key fob. Has a small panda keychain.", "Auditorium", (now - timedelta(hours=4)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "Toyota", None, None, "Panda keychain", "Auditorium"),
        (5, "lost", "Gaming Laptop", "Electronics", "ASUS ROG gaming laptop with RGB keyboard. Sticker on lid.", "Hostel", (now - timedelta(days=1, hours=12)).isoformat(timespec="seconds"), None, "open", now.isoformat(timespec="seconds"), "ASUS", "ROG Strix", "Black", "RGB keyboard, sticker", "Hostel"),
    ]
    
    for item in items:
        try:
            con.execute(
                """INSERT OR IGNORE INTO items(user_id, type, title, category, description, location, date_time, image, status, created_at, brand, color, visual_features, building)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                item
            )
        except Exception as e:
            print(f"Error adding item {item[2]}: {e}")
    
    con.commit()
    print("✓ Items seeded")

def seed_notifications(con):
    """Seed demo notifications."""
    now = datetime.now().isoformat(timespec="seconds")
    
    notifications = [
        (2, "Welcome to CampusFind AI! Report lost items or search for found items.", "/dashboard", 1, now, "info"),
        (3, "Welcome to CampusFind AI! Report lost items or search for found items.", "/dashboard", 1, now, "info"),
        (1, "Potential match found for 'Black iPhone 13 Pro' — 85% confidence.", "/items", 0, now, "match"),
        (2, "Potential match found for 'Black iPhone 13 Pro' — 85% confidence.", "/items", 0, now, "match"),
    ]
    
    for user_id, message, link, is_read, created_at, notif_type in notifications:
        try:
            con.execute(
                "INSERT OR IGNORE INTO notifications(user_id, message, link, is_read, created_at, notification_type) VALUES(?,?,?,?,?,?)",
                (user_id, message, link, is_read, created_at, notif_type)
            )
        except Exception as e:
            print(f"Error adding notification: {e}")
    
    con.commit()
    print("✓ Notifications seeded")

def seed_all():
    """Seed all demo data."""
    print("Seeding demo data...")
    con = seed_users()
    seed_items(con)
    seed_notifications(con)
    con.close()
    print("\n✅ Demo data seeded successfully!")
    print("\nDemo accounts:")
    print("  Admin: admin@campusfind.local / admin123")
    print("  Student: student@campusfind.local / student123")
    print("  John: john@campus.edu / john123")
    print("  Jane: jane@campus.edu / jane123")
    print("  Mike: mike@campus.edu / mike123")

if __name__ == "__main__":
    seed_all()
