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
        """Create the dealerships and reviews tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create dealerships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dealerships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                google_url TEXT UNIQUE NOT NULL,
                active BOOLEAN DEFAULT 1,
                last_scraped TIMESTAMP,
                total_reviews INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create reviews table with dealership relationship
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dealership_id INTEGER,
                review_hash TEXT NOT NULL,
                reviewer_name TEXT,
                star_rating INTEGER,
                review_text TEXT,
                review_date TEXT,
                review_url TEXT,
                ai_category TEXT,
                ai_reasoning TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified BOOLEAN DEFAULT 0,
                reported BOOLEAN DEFAULT 0,
                UNIQUE(dealership_id, review_hash),
                FOREIGN KEY (dealership_id) REFERENCES dealerships(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_dealership(self, name: str, google_url: str) -> int:
        """
        Add a new dealership to track.
        
        Args:
            name: Dealership name
            google_url: Google Maps URL
        
        Returns:
            Dealership ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO dealerships (name, google_url)
                VALUES (?, ?)
            """, (name, google_url))
            
            dealership_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return dealership_id
        except sqlite3.IntegrityError:
            # Dealership already exists, get its ID
            cursor.execute("SELECT id FROM dealerships WHERE google_url = ?", (google_url,))
            dealership_id = cursor.fetchone()[0]
            conn.close()
            return dealership_id
    
    def get_dealership_by_url(self, google_url: str) -> Optional[Dict]:
        """Get dealership info by URL."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM dealerships WHERE google_url = ?", (google_url,))
        row = cursor.fetchone()
        
        conn.close()
        
        return dict(row) if row else None
    
    def update_dealership_last_scraped(self, dealership_id: int):
        """Update last scraped timestamp for a dealership."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE dealerships 
            SET last_scraped = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (dealership_id,))
        
        conn.commit()
        conn.close()
    
    def _generate_review_hash(self, reviewer_name: str, review_text: str, review_date: str) -> str:
        """
        Generate a unique hash for a review based on its content.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text content of the review
            review_date: Date the review was posted (NOT used in hash - Google uses relative dates that change)
        
        Returns:
            SHA256 hash string
        """
        # NOTE: We don't include review_date because Google returns relative dates like
        # "7 months ago" which change to "8 months ago" the next day, causing false duplicates.
        # Reviewer name + text is unique enough.
        content = f"{reviewer_name}|{review_text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def review_exists(self, reviewer_name: str, review_text: str, review_date: str, dealership_id: int = None) -> bool:
        """
        Check if a review already exists in the database.
        
        Args:
            reviewer_name: Name of the reviewer
            review_text: Text content of the review
            review_date: Date the review was posted
            dealership_id: Optional dealership ID to check within specific dealership
        
        Returns:
            True if the review exists, False otherwise
        """
        review_hash = self._generate_review_hash(reviewer_name, review_text, review_date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if dealership_id:
            cursor.execute("""
                SELECT COUNT(*) FROM reviews 
                WHERE review_hash = ? AND dealership_id = ?
            """, (review_hash, dealership_id))
        else:
            # Backward compatibility: check without dealership filter
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
    
    def add_review(self, review_data: Dict, dealership_id: int = None, ai_analysis: Dict = None) -> bool:
        """
        Add a new review to the database.
        
        Args:
            review_data: Dictionary containing review information
            dealership_id: ID of the dealership (optional for backward compatibility)
            ai_analysis: AI analysis results (optional)
        
        Returns:
            True if the review was added, False if it already exists
        """
        review_hash = self._generate_review_hash(
            review_data['reviewer_name'],
            review_data['review_text'],
            review_data['review_date']
        )
        
        # Check if it already exists for this dealership
        if dealership_id and self.review_exists(review_data['reviewer_name'], review_data['review_text'], review_data['review_date'], dealership_id):
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            ai_category = ai_analysis.get('category') if ai_analysis else None
            ai_reasoning = ai_analysis.get('reasoning') if ai_analysis else None
            
            cursor.execute("""
                INSERT INTO reviews (
                    dealership_id, review_hash, reviewer_name, star_rating, 
                    review_text, review_date, review_url, ai_category, ai_reasoning
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dealership_id,
                review_hash,
                review_data['reviewer_name'],
                review_data['star_rating'],
                review_data['review_text'],
                review_data['review_date'],
                review_data['review_url'],
                ai_category,
                ai_reasoning
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
    
    def get_stats(self, dealership_id: int = None) -> Dict:
        """
        Get statistics about the stored reviews.
        
        Args:
            dealership_id: Optional dealership ID to filter stats. If None, returns global stats.
        
        Returns:
            Dictionary with stats (total_reviews, one_star_reviews, notified_count)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if dealership_id:
            cursor.execute("SELECT COUNT(*) FROM reviews WHERE dealership_id = ?", (dealership_id,))
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM reviews WHERE dealership_id = ? AND star_rating = 1", (dealership_id,))
            one_star = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM reviews WHERE dealership_id = ? AND notified = 1", (dealership_id,))
            notified = cursor.fetchone()[0]
        else:
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
