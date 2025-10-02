"""
Database Manager
Handles storage and retrieval of review data to track which reviews have been seen.
"""

import sqlite3
import hashlib
from typing import List, Dict, Optional
from datetime import datetime


class DatabaseManager:
    """Manages the SQLite database for storing review history."""
    
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Create the reviews table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_hash TEXT UNIQUE NOT NULL,
                reviewer_name TEXT,
                star_rating INTEGER,
                review_text TEXT,
                review_date TEXT,
                review_url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified BOOLEAN DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_review_hash(self, reviewer_name: str, review_text: str, review_date: str) -> str:
        """
        Generate a unique hash for a review based on its content.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text content of the review
            review_date: Date the review was posted
        
        Returns:
            SHA256 hash string
        """
        content = f"{reviewer_name}|{review_text}|{review_date}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def review_exists(self, reviewer_name: str, review_text: str, review_date: str) -> bool:
        """
        Check if a review already exists in the database.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text content of the review
            review_date: Date the review was posted
        
        Returns:
            True if the review exists, False otherwise
        """
        review_hash = self._generate_review_hash(reviewer_name, review_text, review_date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE review_hash = ?", (review_hash,))
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count > 0
    
    def review_exists_by_text(self, text_snippet: str) -> bool:
        """
        Quick check if a review exists based on text snippet (for early exit during scraping).
        
        Args:
            text_snippet: Beginning of the review text (first ~100 chars)
        
        Returns:
            True if a review with this text snippet exists, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Use LIKE to match the beginning of review_text
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE review_text LIKE ?", (text_snippet + '%',))
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count > 0
    
    def add_review(self, review_data: Dict) -> bool:
        """
        Add a new review to the database.
        
        Args:
            review_data: Dictionary containing review information
                Required keys: reviewer_name, star_rating, review_text, review_date, review_url
        
        Returns:
            True if the review was added, False if it already exists
        """
        review_hash = self._generate_review_hash(
            review_data['reviewer_name'],
            review_data['review_text'],
            review_data['review_date']
        )
        
        # Check if it already exists
        if self.review_exists(review_data['reviewer_name'], review_data['review_text'], review_data['review_date']):
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO reviews (review_hash, reviewer_name, star_rating, review_text, review_date, review_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                review_hash,
                review_data['reviewer_name'],
                review_data['star_rating'],
                review_data['review_text'],
                review_data['review_date'],
                review_data['review_url']
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def mark_as_notified(self, reviewer_name: str, review_text: str, review_date: str):
        """
        Mark a review as having been notified.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text content of the review
            review_date: Date the review was posted
        """
        review_hash = self._generate_review_hash(reviewer_name, review_text, review_date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE reviews SET notified = 1 WHERE review_hash = ?", (review_hash,))
        
        conn.commit()
        conn.close()
    
    def get_all_reviews(self) -> List[Dict]:
        """
        Retrieve all reviews from the database.
        
        Returns:
            List of dictionaries, each representing a review
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reviews ORDER BY scraped_at DESC")
        rows = cursor.fetchall()
        
        reviews = [dict(row) for row in rows]
        
        conn.close()
        
        return reviews
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the stored reviews.
        
        Returns:
            Dictionary with stats (total_reviews, one_star_reviews, notified_count)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE star_rating = 1")
        one_star = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE notified = 1")
        notified = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_reviews': total,
            'one_star_reviews': one_star,
            'notified_count': notified
        }
