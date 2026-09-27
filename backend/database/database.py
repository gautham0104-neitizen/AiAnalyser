from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Optional


class Database:
    def __init__(self, db_path: str = "data/programmer_analyzer.db"):
        self.db_path = Path(db_path)

        # Make sure the data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)

        # Makes rows behave like dictionaries
        self.connection.row_factory = sqlite3.Row

        self.create_tables()

    # ---------------------------------------------------------
    # CREATE TABLES
    # ---------------------------------------------------------

    def create_tables(self) -> None:
        cursor = self.connection.cursor()

        # Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---------------------------------------------------------
        # MIGRATE EXISTING USERS TABLE
        # ---------------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(users)"
        )

        columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "password_hash" not in columns:

            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN password_hash TEXT
                """
            )

        # Code submissions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                problem_name TEXT,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)

        # Analysis results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                loc INTEGER,
                blank_lines INTEGER,
                comment_lines INTEGER,
                num_functions INTEGER,
                num_classes INTEGER,
                num_imports INTEGER,
                num_variables INTEGER,
                num_constants INTEGER,
                if_statements INTEGER,
                for_loops INTEGER,
                while_loops INTEGER,
                total_loops INTEGER,
                nested_loops INTEGER,
                max_loop_nesting_depth INTEGER,
                try_except_blocks INTEGER,
                conditional_expressions INTEGER,
                comprehensions INTEGER,
                avg_function_length REAL,
                max_function_length INTEGER,
                avg_function_args REAL,
                total_return_statements INTEGER,
                recursive_functions INTEGER,
                cyclomatic_complexity REAL,
                maximum_cyclomatic_complexity INTEGER,
                maintainability_index REAL,
                patterns TEXT,
                data_structures TEXT,
                -- ML results
                cluster INTEGER,
                cluster_memberships TEXT,
                optimization_score REAL,
                code_quality_score REAL,
                algorithm_diversity REAL,
                data_structure_diversity REAL,
                problem_solving_diversity REAL,
                brute_force_tendency REAL,
                nested_loop_percentage REAL,
                recursion_percentage REAL,
                improvement_score REAL,
                FOREIGN KEY (submission_id)
                    REFERENCES submissions(id)
            )
        """)

        # ---------------------------------------------------------
        # MIGRATE CODE FEATURES TABLE
        # ---------------------------------------------------------
        cursor.execute(
            "PRAGMA table_info(code_features)"
        )

        feature_columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        ml_columns = {
            "cluster": "INTEGER",
            "cluster_memberships": "TEXT",
            "optimization_score": "REAL",
            "code_quality_score": "REAL",
            "algorithm_diversity": "REAL",
            "data_structure_diversity": "REAL",
            "problem_solving_diversity": "REAL",
            "brute_force_tendency": "REAL",
            "nested_loop_percentage": "REAL",
            "recursion_percentage": "REAL",
            "improvement_score": "REAL"
        }

        for column_name, column_type in ml_columns.items():
            if column_name not in feature_columns:
                cursor.execute(
                    f"""
                    ALTER TABLE code_features
                    ADD COLUMN {column_name} {column_type}
                    """
                )

        self.connection.commit()

    # ---------------------------------------------------------
    # USER METHODS
    # ---------------------------------------------------------

    def create_user(self, username: str) -> int:
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (username)
            VALUES (?)
            """,
            (username,)
        )

        self.connection.commit()

        return cursor.lastrowid

    def get_user(self, username: str) -> Optional[sqlite3.Row]:
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        return cursor.fetchone()

    # ---------------------------------------------------------
    # SUBMISSION METHODS
    # ---------------------------------------------------------

    def save_submission(
        self,
        user_id: int,
        problem_name: str,
        language: str,
        code: str
    ) -> int:

        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO submissions
            (user_id, problem_name, language, code)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                problem_name,
                language,
                code
            )
        )

        self.connection.commit()

        return cursor.lastrowid

    # ---------------------------------------------------------
    # FEATURE METHODS
    # ---------------------------------------------------------

    def save_features(
        self,
        submission_id: int,
        features: dict,
        complexity: dict,
        ml_results: dict | None = None
    ) -> None:
        if ml_results is None:
            ml_results = {}

        values = (
            submission_id,
            features.get("loc", 0),
            features.get("blank_lines", 0),
            features.get("comment_lines", 0),
            features.get("num_functions", 0),
            features.get("num_classes", 0),
            features.get("num_imports", 0),
            features.get("num_variables", 0),
            features.get("num_constants", 0),
            features.get("if_statements", 0),
            features.get("for_loops", 0),
            features.get("while_loops", 0),
            features.get("total_loops", 0),
            features.get("nested_loops", 0),
            features.get("max_loop_nesting_depth", 0),
            features.get("try_except_blocks", 0),
            features.get("conditional_expressions", 0),
            features.get("comprehensions", 0),
            features.get("avg_function_length", 0),
            features.get("max_function_length", 0),
            features.get("avg_function_args", 0),
            features.get("total_return_statements", 0),
            features.get("recursive_functions", 0),
            complexity.get(
                "cyclomatic_complexity",
                {}
            ).get("average", 0),
            complexity.get(
                "cyclomatic_complexity",
                {}
            ).get("maximum", 0),
            complexity.get(
                "maintainability_index",
                0
            ),
            json.dumps(features.get("patterns", [])),
            json.dumps(features.get("data_structures", {})),
            ml_results.get("cluster"),
            json.dumps(
                ml_results.get(
                    "cluster_memberships",
                    []
                )
            ),
            ml_results.get(
                "optimization_score",
                0
            ),
            ml_results.get(
                "code_quality_score",
                0
            ),
            ml_results.get(
                "algorithm_diversity",
                0
            ),
            ml_results.get(
                "data_structure_diversity",
                0
            ),
            ml_results.get(
                "problem_solving_diversity",
                0
            ),
            ml_results.get(
                "brute_force_tendency",
                0
            ),
            ml_results.get(
                "nested_loop_percentage",
                0
            ),
            ml_results.get(
                "recursion_percentage",
                0
            ),
            ml_results.get(
                "improvement_score",
                0
            )
        )

        placeholders = ", ".join(["?"] * len(values))

        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            INSERT INTO code_features (
                submission_id,
                loc,
                blank_lines,
                comment_lines,
                num_functions,
                num_classes,
                num_imports,
                num_variables,
                num_constants,
                if_statements,
                for_loops,
                while_loops,
                total_loops,
                nested_loops,
                max_loop_nesting_depth,
                try_except_blocks,
                conditional_expressions,
                comprehensions,
                avg_function_length,
                max_function_length,
                avg_function_args,
                total_return_statements,
                recursive_functions,
                cyclomatic_complexity,
                maximum_cyclomatic_complexity,
                maintainability_index,
                patterns,
                data_structures,
                cluster,
                cluster_memberships,
                optimization_score,
                code_quality_score,
                algorithm_diversity,
                data_structure_diversity,
                problem_solving_diversity,
                brute_force_tendency,
                nested_loop_percentage,
                recursion_percentage,
                improvement_score
            )
            VALUES ({placeholders})
            """,
            values
        )
        self.connection.commit()

    # ---------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------

    def get_user_submissions(self, user_id: int):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                submissions.*,
                code_features.*
            FROM submissions

            LEFT JOIN code_features
                ON submissions.id = code_features.submission_id

            WHERE submissions.user_id = ?

            ORDER BY submissions.submitted_at ASC
            """,
            (user_id,)
        )

        return cursor.fetchall()

    # ---------------------------------------------------------
    # CLOSE DATABASE
    # ---------------------------------------------------------

    def close(self) -> None:
        self.connection.close()