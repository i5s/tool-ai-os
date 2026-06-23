-- Sprint X-3.5: Agent Runtime Bridge

-- Store execution results on tasks
ALTER TABLE tasks ADD COLUMN result TEXT;
ALTER TABLE tasks ADD COLUMN result_metadata TEXT;
