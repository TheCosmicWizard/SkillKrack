from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import logging
from functools import wraps
import hashlib
import secrets
from werkzeug.exceptions import BadRequest
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['DATABASE_PATH'] = os.environ.get('DB_PATH', os.path.join("database", "results.db"))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure database directory exists
os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """Initialize the database with required tables."""
    try:
        with get_db_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    confidence_score INTEGER NOT NULL CHECK(confidence_score >= 0 AND confidence_score <= 100),
                    knowledge_score INTEGER NOT NULL CHECK(knowledge_score >= 0 AND knowledge_score <= 100),
                    final_score INTEGER NOT NULL CHECK(final_score >= 0 AND final_score <= 100),
                    feedback TEXT,
                    question_answered TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_results_username ON results(username);
                CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);
            ''')
            conn.commit()
        app.logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        app.logger.error(f"Database initialization error: {e}")
        raise

def validate_json_data(required_fields):
    """Decorator to validate JSON data and required fields."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    "error": "Missing required fields",
                    "missing_fields": missing_fields
                }), 400
            
            return f(data, *args, **kwargs)
        return decorated_function
    return decorator

def generate_session_id():
    """Generate a unique session ID."""
    return hashlib.sha256(f"{datetime.utcnow().isoformat()}{secrets.token_hex(16)}".encode()).hexdigest()

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(BadRequest)
def bad_request_error(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@app.route("/", methods=["GET"])
def index():
    """Health check endpoint."""
    return jsonify({
        "message": "Interview Prep API is running",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/create-session", methods=["POST"])
@validate_json_data(["username"])
def create_session(data):
    """Create a new user session."""
    username = data.get("username", "").strip()
    
    if not username or len(username) < 2:
        return jsonify({"error": "Username must be at least 2 characters long"}), 400
    
    if len(username) > 50:
        return jsonify({"error": "Username must be less than 50 characters"}), 400
    
    session_id = generate_session_id()
    
    try:
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO user_sessions (session_id, username)
                VALUES (?, ?)
            ''', (session_id, username))
            conn.commit()
        
        app.logger.info(f"Session created for user: {username}")
        return jsonify({
            "message": "Session created successfully",
            "session_id": session_id,
            "username": username
        }), 201
        
    except sqlite3.Error as e:
        app.logger.error(f"Error creating session: {e}")
        return jsonify({"error": "Failed to create session"}), 500

@app.route("/save-result", methods=["POST"])
@validate_json_data(["confidence_score", "knowledge_score"])
def save_result(data):
    """Save interview result with improved validation."""
    try:
        # Extract and validate data
        username = data.get("username", "Anonymous").strip()
        confidence = int(data.get("confidence_score"))
        knowledge = int(data.get("knowledge_score"))
        feedback_list = data.get("feedback", [])
        question_answered = data.get("question_answered", "")
        session_id = data.get("session_id")
        
        # Validation
        if not (0 <= confidence <= 100):
            return jsonify({"error": "Confidence score must be between 0 and 100"}), 400
        
        if not (0 <= knowledge <= 100):
            return jsonify({"error": "Knowledge score must be between 0 and 100"}), 400
        
        if len(username) > 50:
            return jsonify({"error": "Username too long"}), 400
        
        # Calculate final score
        final_score = int((confidence + knowledge) / 2)
        
        # Process feedback
        if isinstance(feedback_list, list):
            feedback = ", ".join(str(item) for item in feedback_list if item)
        else:
            feedback = str(feedback_list) if feedback_list else ""
        
        # Save to database
        with get_db_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO results 
                (username, confidence_score, knowledge_score, final_score, feedback, question_answered, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, confidence, knowledge, final_score, feedback, question_answered, session_id))
            
            result_id = cursor.lastrowid
            conn.commit()
        
        app.logger.info(f"Result saved for user {username} with final score {final_score}")
        
        return jsonify({
            "message": "Result saved successfully",
            "result_id": result_id,
            "final_score": final_score,
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        }), 201
        
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except sqlite3.Error as e:
        app.logger.error(f"Database error saving result: {e}")
        return jsonify({"error": "Failed to save result"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error saving result: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/get-results", methods=["GET"])
def get_results():
    """Get results with pagination and filtering options."""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)  # Max 100 results per page
        username = request.args.get('username', '').strip()
        days = request.args.get('days', type=int)
        
        # Pagination validation
        if page < 1:
            return jsonify({"error": "Page must be >= 1"}), 400
        if per_page < 1:
            return jsonify({"error": "Per page must be >= 1"}), 400
        
        # Build query
        query = '''
            SELECT id, username, confidence_score, knowledge_score, final_score, 
                   feedback, question_answered, session_id, created_at
            FROM results
        '''
        params = []
        conditions = []
        
        # Add filters
        if username:
            conditions.append("username LIKE ?")
            params.append(f"%{username}%")
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            conditions.append("created_at >= ?")
            params.append(cutoff_date.isoformat())
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        # Add pagination
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        # Execute query
        with get_db_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM results"
            if conditions:
                count_query += " WHERE " + " AND ".join(conditions)
            
            total_count = conn.execute(count_query, params[:-2] if days else params).fetchone()[0]
        
        # Format results
        results = []
        for row in rows:
            result = {
                "id": row["id"],
                "username": row["username"],
                "confidence_score": row["confidence_score"],
                "knowledge_score": row["knowledge_score"],
                "final_score": row["final_score"],
                "feedback": row["feedback"],
                "question_answered": row["question_answered"],
                "session_id": row["session_id"],
                "created_at": row["created_at"]
            }
            results.append(result)
        
        # Pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        response = {
            "results": results,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_results": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except sqlite3.Error as e:
        app.logger.error(f"Database error getting results: {e}")
        return jsonify({"error": "Failed to retrieve results"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error getting results: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/get-user-stats/<username>", methods=["GET"])
def get_user_stats(username):
    """Get statistics for a specific user."""
    if not username or len(username) > 50:
        return jsonify({"error": "Invalid username"}), 400
    
    try:
        with get_db_connection() as conn:
            # Get user statistics
            stats_query = '''
                SELECT 
                    COUNT(*) as total_attempts,
                    AVG(confidence_score) as avg_confidence,
                    AVG(knowledge_score) as avg_knowledge,
                    AVG(final_score) as avg_final_score,
                    MAX(final_score) as best_score,
                    MIN(final_score) as worst_score,
                    MAX(created_at) as last_attempt
                FROM results 
                WHERE username = ?
            '''
            
            stats = conn.execute(stats_query, (username,)).fetchone()
            
            if stats["total_attempts"] == 0:
                return jsonify({"error": "No results found for this user"}), 404
            
            # Get recent results
            recent_query = '''
                SELECT confidence_score, knowledge_score, final_score, created_at
                FROM results 
                WHERE username = ? 
                ORDER BY created_at DESC 
                LIMIT 5
            '''
            recent_results = conn.execute(recent_query, (username,)).fetchall()
            
            response = {
                "username": username,
                "statistics": {
                    "total_attempts": stats["total_attempts"],
                    "average_confidence": round(stats["avg_confidence"], 2) if stats["avg_confidence"] else 0,
                    "average_knowledge": round(stats["avg_knowledge"], 2) if stats["avg_knowledge"] else 0,
                    "average_final_score": round(stats["avg_final_score"], 2) if stats["avg_final_score"] else 0,
                    "best_score": stats["best_score"],
                    "worst_score": stats["worst_score"],
                    "last_attempt": stats["last_attempt"]
                },
                "recent_results": [
                    {
                        "confidence_score": row["confidence_score"],
                        "knowledge_score": row["knowledge_score"],
                        "final_score": row["final_score"],
                        "created_at": row["created_at"]
                    }
                    for row in recent_results
                ]
            }
            
            return jsonify(response)
            
    except sqlite3.Error as e:
        app.logger.error(f"Database error getting user stats: {e}")
        return jsonify({"error": "Failed to retrieve user statistics"}), 500

@app.route("/delete-result/<int:result_id>", methods=["DELETE"])
def delete_result(result_id):
    """Delete a specific result (for cleanup purposes)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM results WHERE id = ?", (result_id,))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Result not found"}), 404
            
            conn.commit()
        
        app.logger.info(f"Result {result_id} deleted")
        return jsonify({"message": "Result deleted successfully"}), 200
        
    except sqlite3.Error as e:
        app.logger.error(f"Database error deleting result: {e}")
        return jsonify({"error": "Failed to delete result"}), 500

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f"Starting Interview Prep API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)