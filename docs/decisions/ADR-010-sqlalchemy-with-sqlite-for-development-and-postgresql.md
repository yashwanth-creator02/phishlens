# ADR-010: SQLAlchemy with SQLite for development and PostgreSQL (Supabase) for production

**Status:** accepted (v0.1)

## Context
Tests and local work should not need a database server; production needs Supabase.

## Decision
One ORM layer, URL-switchable. JSON columns work on both. SQL migration with RLS provided for Supabase.

## Consequences
Postgres path untested here. Add Alembic before real data.
