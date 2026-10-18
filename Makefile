.PHONY: up down build test evals clean

up:
	docker compose up --build

down:
	docker compose down

test:
	@echo "=== Running Task 1 Tests ==="
	cd task1-knowledge-brain && pytest tests/ -v
	@echo "=== Running Task 2 Tests ==="
	cd task2-inbox-agent && npm test
	@echo "=== Running Task 3 Tests ==="
	cd task3-meeting-to-scope && pytest tests/ -v

evals:
	@echo "=== Running Task 1 Evals ==="
	cd task1-knowledge-brain && python evals/eval_runner.py
	@echo "=== Running Task 2 Evals ==="
	cd task2-inbox-agent && npm run evals
	@echo "=== Running Task 3 Evals ==="
	cd task3-meeting-to-scope && python evals/eval_runner.py

clean:
	rm -rf task1-knowledge-brain/chroma_db task1-knowledge-brain/task1.db
	rm -rf task2-inbox-agent/.next task2-inbox-agent/data/feedback_history.json
	rm -rf task3-meeting-to-scope/scope.db
