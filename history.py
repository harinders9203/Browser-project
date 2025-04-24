import os
import json
import time
from datetime import datetime
from urllib.parse import urlparse


class BrowserHistoryProcessor:
    def __init__(self, storage_path):
        """
        Initialize the history processor with specified storage path.
        
        Args:
            storage_path: Path where history data will be stored
        """
        self.storage_path = storage_path
        self.history = []
        self.initialize()
        
    def initialize(self):
        """Initialize history storage file if it doesn't exist."""
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(self.storage_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Create history file if it doesn't exist
            if not os.path.exists(self.storage_path):
                with open(self.storage_path, 'w') as f:
                    json.dump([], f)
            else:
                # Load existing history
                with open(self.storage_path, 'r') as f:
                    self.history = json.load(f)
                    
            print(f"History initialized at {self.storage_path}")
        except Exception as e:
            print(f"Error initializing history storage: {e}")
    
    def record_visit(self, current_url, title, timestamp=None):
        """
        Record a website visit in history.
        
        Args:
            current_url: URL of the visited website
            title: Title of the page
            timestamp: Time of visit (current time if None)
            
        Returns:
            bool: Success or failure
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        try:
            # Check if URL already exists in history
            existing_entry = None
            existing_index = -1
            
            for i, entry in enumerate(self.history):
                if entry['url'] == current_url:
                    existing_entry = entry
                    existing_index = i
                    break
            
            if existing_entry:
                # URL exists, update entry
                self.history[existing_index]['visit_count'] += 1
                self.history[existing_index]['timestamp'] = timestamp
                self.history[existing_index]['title'] = title  # Update title in case it changed
            else:
                # New URL, create new entry
                self.history.append({
                    'url': current_url,
                    'title': title,
                    'timestamp': timestamp,
                    'visit_count': 1
                })
            
            # Save changes to file
            self.save_history()
            return True
        except Exception as e:
            print(f"Error recording visit: {e}")
            return False
    
    def save_history(self):
        """Save history data to storage file."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False
    
    def get_frequent_sites(self, limit=10):
        """
        Get most frequently visited sites.
        
        Args:
            limit: Maximum number of sites to return
            
        Returns:
            list: Most frequently visited sites
        """
        # Sort by visit count (descending)
        return sorted(
            self.history,
            key=lambda x: x['visit_count'],
            reverse=True
        )[:limit]
    
    def get_recent_sites(self, limit=10):
        """
        Get most recently visited sites.
        
        Args:
            limit: Maximum number of sites to return
            
        Returns:
            list: Most recently visited sites
        """
        # Sort by timestamp (most recent first)
        return sorted(
            self.history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]
    
    def get_top_sites(self, limit=10):
        """
        Get top sites based on frequency and recency.
        
        Args:
            limit: Maximum number of sites to return
            
        Returns:
            list: Top sites
        """
        # Calculate a score based on visit count and recency
        current_time = time.time()
        scored_sites = []
        
        for item in self.history:
            try:
                # Convert ISO timestamp to Unix timestamp
                item_time = datetime.fromisoformat(item['timestamp']).timestamp()
                # Calculate recency score (1.0 is most recent, decreases with age)
                recency_score = item_time / current_time
                # Calculate combined score
                score = item['visit_count'] * recency_score
                
                scored_sites.append({**item, 'score': score})
            except (ValueError, TypeError):
                # Handle invalid timestamps
                scored_sites.append({**item, 'score': 0})
        
        return sorted(scored_sites, key=lambda x: x['score'], reverse=True)[:limit]
    
    def search_history(self, query, limit=20):
        """
        Search history by URL or title.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            list: Matching history entries
        """
        query = query.lower()
        matches = [
            item for item in self.history
            if query in item['url'].lower() or query in item['title'].lower()
        ]
        
        # Sort by visit count
        return sorted(matches, key=lambda x: x['visit_count'], reverse=True)[:limit]
    
    def clear_history(self, options=None):
        """
        Clear history based on options.
        
        Args:
            options: Dictionary with optional keys:
                    - before: Clear entries before this timestamp
                    - after: Clear entries after this timestamp
                    - domain: Clear entries matching this domain
                    
        Returns:
            bool: Success or failure
        """
        if options is None:
            options = {}
            
        try:
            before = options.get('before')
            after = options.get('after')
            domain = options.get('domain')
            
            if not before and not after and not domain:
                # Clear all history
                self.history = []
            else:
                # Apply filters
                filtered_history = []
                
                for item in self.history:
                    should_keep = True
                    
                    # Check date conditions
                    if before or after:
                        try:
                            item_date = datetime.fromisoformat(item['timestamp'])
                            
                            if before and item_date > datetime.fromisoformat(before):
                                should_keep = True
                            elif after and item_date < datetime.fromisoformat(after):
                                should_keep = True
                            else:
                                should_keep = False
                        except (ValueError, TypeError):
                            # Keep entries with invalid timestamps
                            should_keep = True
                    
                    # Check domain condition
                    if domain and should_keep:
                        try:
                            item_domain = urlparse(item['url']).netloc
                            if domain in item_domain:
                                should_keep = False
                        except Exception:
                            # Keep entries with invalid URLs
                            should_keep = True
                    
                    if should_keep:
                        filtered_history.append(item)
                
                self.history = filtered_history
            
            self.save_history()
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize history processor
    history_processor = BrowserHistoryProcessor("./browser_data/history.json")
    
    # Record some visits
    history_processor.record_visit(
        "https://example.com",
        "Example Domain"
    )
    
    # Record another visit
    history_processor.record_visit(
        "https://python.org",
        "Python Programming Language"
    )
    
    # Get frequent sites
    print("Frequently visited sites:")
    print(history_processor.get_frequent_sites(5))
    
    # Get recent sites
    print("Recently visited sites:")
    print(history_processor.get_recent_sites(5))
    
    # Search history
    print("Search results for 'example':")
    print(history_processor.search_history("example"))