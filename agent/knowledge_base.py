"""
Knowledge Base for ServiceNow Ticket Agent.
Stores and retrieves learned patterns, best practices, and historical data.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from logging_config import get_main_logger


class KnowledgeBase:
    """Centralized knowledge base for storing and retrieving learned information."""
    
    def __init__(self, db_path: str = "database/knowledge.db"):
        self.db_path = db_path
        self.logger = get_main_logger()
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure database and tables exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS response_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_key TEXT UNIQUE NOT NULL,
                    response_data TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    input_pattern TEXT NOT NULL,
                    response_data TEXT NOT NULL,
                    feedback_data TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS best_practices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    practice_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ticket_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT UNIQUE NOT NULL,
                    template_data TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pattern_key ON response_patterns(pattern_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON learning_history(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON best_practices(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_category ON ticket_templates(category)")
            
            conn.commit()
    
    def store_response_pattern(self, pattern_key: str, response_data: Dict[str, Any], 
                             success_rate: float = 0.5) -> bool:
        """Store a response pattern in the knowledge base."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if pattern already exists
                cursor = conn.execute(
                    "SELECT id, success_rate, usage_count FROM response_patterns WHERE pattern_key = ?",
                    (pattern_key,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing pattern
                    new_success_rate = (existing[1] + success_rate) / 2
                    new_usage_count = existing[2] + 1
                    
                    conn.execute("""
                        UPDATE response_patterns 
                        SET response_data = ?, success_rate = ?, usage_count = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (json.dumps(response_data), new_success_rate, new_usage_count, existing[0]))
                else:
                    # Insert new pattern
                    conn.execute("""
                        INSERT INTO response_patterns (pattern_key, response_data, success_rate)
                        VALUES (?, ?, ?)
                    """, (pattern_key, json.dumps(response_data), success_rate))
                
                conn.commit()
                self.logger.info(f"Stored response pattern: {pattern_key}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store response pattern: {e}")
            return False
    
    def retrieve_response_pattern(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a response pattern from the knowledge base."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT response_data, success_rate, usage_count FROM response_patterns WHERE pattern_key = ?",
                    (pattern_key,)
                )
                result = cursor.fetchone()
                
                if result:
                    response_data = json.loads(result[0])
                    return {
                        "response": response_data,
                        "success_rate": result[1],
                        "usage_count": result[2]
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve response pattern: {e}")
            return None
    
    def search_response_patterns(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for response patterns based on query."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT pattern_key, response_data, success_rate, usage_count
                    FROM response_patterns 
                    WHERE pattern_key LIKE ? OR response_data LIKE ?
                    ORDER BY success_rate DESC, usage_count DESC
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "pattern_key": row[0],
                        "response": json.loads(row[1]),
                        "success_rate": row[2],
                        "usage_count": row[3]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to search response patterns: {e}")
            return []
    
    def store_learning_history(self, agent_id: str, input_pattern: str, 
                              response_data: Dict[str, Any], 
                              feedback_data: Optional[Dict[str, Any]] = None,
                              success: bool = True) -> bool:
        """Store learning history entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO learning_history (agent_id, input_pattern, response_data, feedback_data, success)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    agent_id, 
                    input_pattern, 
                    json.dumps(response_data),
                    json.dumps(feedback_data) if feedback_data else None,
                    success
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store learning history: {e}")
            return False
    
    def get_learning_history(self, agent_id: Optional[str] = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve learning history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if agent_id:
                    cursor = conn.execute("""
                        SELECT * FROM learning_history 
                        WHERE agent_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (agent_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM learning_history 
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "agent_id": row[1],
                        "input_pattern": row[2],
                        "response_data": json.loads(row[3]),
                        "feedback_data": json.loads(row[4]) if row[4] else None,
                        "success": bool(row[5]),
                        "timestamp": row[6]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve learning history: {e}")
            return []
    
    def store_best_practice(self, category: str, practice_name: str, 
                           description: str, effectiveness_score: float = 0.5) -> bool:
        """Store a best practice in the knowledge base."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO best_practices 
                    (category, practice_name, description, effectiveness_score, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (category, practice_name, description, effectiveness_score))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store best practice: {e}")
            return False
    
    def get_best_practices(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve best practices."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if category:
                    cursor = conn.execute("""
                        SELECT * FROM best_practices 
                        WHERE category = ?
                        ORDER BY effectiveness_score DESC
                    """, (category,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM best_practices 
                        ORDER BY effectiveness_score DESC
                    """)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "category": row[1],
                        "practice_name": row[2],
                        "description": row[3],
                        "effectiveness_score": row[4],
                        "usage_count": row[5],
                        "created_at": row[6],
                        "updated_at": row[7]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve best practices: {e}")
            return []
    
    def store_ticket_template(self, template_name: str, template_data: Dict[str, Any],
                            category: str, priority: str) -> bool:
        """Store a ticket template."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO ticket_templates 
                    (template_name, template_data, category, priority, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (template_name, json.dumps(template_data), category, priority))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store ticket template: {e}")
            return False
    
    def get_ticket_templates(self, category: Optional[str] = None, 
                           priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve ticket templates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM ticket_templates WHERE 1=1"
                params = []
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                if priority:
                    query += " AND priority = ?"
                    params.append(priority)
                
                query += " ORDER BY success_rate DESC"
                
                cursor = conn.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "template_name": row[1],
                        "template_data": json.loads(row[2]),
                        "category": row[3],
                        "priority": row[4],
                        "success_rate": row[5],
                        "created_at": row[6],
                        "updated_at": row[7]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve ticket templates: {e}")
            return []
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Count patterns
                cursor = conn.execute("SELECT COUNT(*) FROM response_patterns")
                stats["total_patterns"] = cursor.fetchone()[0]
                
                # Count learning history
                cursor = conn.execute("SELECT COUNT(*) FROM learning_history")
                stats["total_learning_entries"] = cursor.fetchone()[0]
                
                # Count best practices
                cursor = conn.execute("SELECT COUNT(*) FROM best_practices")
                stats["total_best_practices"] = cursor.fetchone()[0]
                
                # Count templates
                cursor = conn.execute("SELECT COUNT(*) FROM ticket_templates")
                stats["total_templates"] = cursor.fetchone()[0]
                
                # Average success rates
                cursor = conn.execute("SELECT AVG(success_rate) FROM response_patterns")
                stats["avg_pattern_success_rate"] = cursor.fetchone()[0] or 0.0
                
                # Recent activity
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM learning_history 
                    WHERE timestamp > ?
                """, (cutoff_time.isoformat(),))
                stats["recent_learning_activity"] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get knowledge stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to prevent database bloat."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                # Clean old learning history
                conn.execute("""
                    DELETE FROM learning_history 
                    WHERE timestamp < ?
                """, (cutoff_time.isoformat(),))
                
                # Clean old patterns with low success rates
                conn.execute("""
                    DELETE FROM response_patterns 
                    WHERE success_rate < 0.3 AND usage_count < 5
                """)
                
                conn.commit()
                
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def export_knowledge(self, export_path: str) -> bool:
        """Export knowledge base to file."""
        try:
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "response_patterns": self.get_all_response_patterns(),
                "best_practices": self.get_best_practices(),
                "ticket_templates": self.get_ticket_templates(),
                "learning_history": self.get_learning_history(limit=1000)
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Knowledge base exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export knowledge base: {e}")
            return False
    
    def get_all_response_patterns(self) -> List[Dict[str, Any]]:
        """Get all response patterns."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM response_patterns")
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "pattern_key": row[1],
                        "response_data": json.loads(row[2]),
                        "success_rate": row[3],
                        "usage_count": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get all response patterns: {e}")
            return []
