-- Notebook source content persistence — Sprint 5C fix
-- Adds content column to notebook_sources so uploaded text is stored locally.

ALTER TABLE notebook_sources ADD COLUMN content TEXT NOT NULL DEFAULT '';
