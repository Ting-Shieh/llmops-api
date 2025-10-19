# Changelog

## [0.1.0] - 2025-10-19

### Added
- 帳號/OAuth 登入認證系統
- 應用管理功能（建立/查詢/更新/刪除）
- 資料集/文件/分段管理
- 會話服務（摘要、命名、建議問題）
- API 工具管理
- Agent 核心架構（FunctionCall Agent、佇列管理器）

### Fixed
- 修復 internal.model 循環導入問題
- 修復 internal.service 循環導入問題
- 修正 SQLAlchemy UUID 類型使用錯誤

### Changed
- 重構 HTTP 啟動與路由註冊
