.PHONY: install run push push-both push-autodesk push-github help

install:
	pip3 install -r requirements.txt

run:
	python3 final_weekly_digest_system.py

push:
	git push autodesk main

push-both:
	./push_both.sh

push-autodesk:
	git push autodesk main

push-github:
	git push origin main

help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  run           - Run the weekly digest system"
	@echo "  push          - Push to Autodesk Git Enterprise (primary)"
	@echo "  push-both     - Push to Autodesk (primary) and GitHub (mirror)"
	@echo "  push-autodesk - Push to Autodesk Git Enterprise only"
	@echo "  push-github   - Push to GitHub mirror only"
	@echo "  help          - Show this help"
