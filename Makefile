# 変数定義
ENTRY_POINT = main.py
OUTPUT_PARENT = build
OUTPUT_NAME = SnackingOthello

.PHONY: run build-windows build-macos clean

# 通常起動
run:
	uv run $(ENTRY_POINT)

# Windows用ビルド
build-windows:
	uv run nuitka \
		--onefile \
		--follow-imports \
		--output-dir=$(OUTPUT_PARENT) \
		--output-filename=$(OUTPUT_NAME).exe \
		--windows-icon-from-ico=icon.ico \
		--include-data-dir=assets=assets \
		--include-data-files=config.yaml=config.yaml \
		$(ENTRY_POINT)

# macOS用ビルド
build-macos:
	uv run nuitka \
		--mode=app \
		--follow-imports \
		--output-dir=$(OUTPUT_PARENT) \
		--output-filename=$(OUTPUT_NAME) \
		--macos-app-icon=icon.icns \
		--include-data-dir=assets=assets \
		--include-data-files=config.yaml=config.yaml \
		$(ENTRY_POINT)

# ビルド成果物を削除
clean:
	@if [ -d "$(OUTPUT_PARENT)" ]; then rm -rf "$(OUTPUT_PARENT)"; echo "Removed $(OUTPUT_PARENT) folder"; fi
	@if [ -d "main.build" ]; then rm -rf "main.build"; echo "Removed main.build"; fi
	@if [ -d "main.onefile-build" ]; then rm -rf "main.onefile-build"; echo "Removed main.onefile-build"; fi
	@if [ -d "main.dist" ]; then rm -rf "main.dist"; echo "Removed main.dist"; fi