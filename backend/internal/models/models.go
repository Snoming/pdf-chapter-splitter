package models

import (
	"time"
)

// FileInfo 文件信息结构
type FileInfo struct {
	FileID     string    `json:"file_id"`
	Filename   string    `json:"filename"`
	FileSize   int64     `json:"file_size"`
	FilePath   string    `json:"file_path"`
	UploadTime time.Time `json:"upload_time"`
	Status     string    `json:"status"` // uploaded, analyzed, split, error
}

// ChapterInfo 章节信息结构
type ChapterInfo struct {
	Title     string `json:"title"`
	StartPage int    `json:"start_page"`
	EndPage   int    `json:"end_page"`
	PageCount int    `json:"page_count"`
}

// PDFMetadata PDF元数据结构
type PDFMetadata struct {
	FileID     string        `json:"file_id"`
	Filename   string        `json:"filename"`
	TotalPages int           `json:"total_pages"`
	FileSize   int64         `json:"file_size"`
	Chapters   []ChapterInfo `json:"chapters"`
	CreatedAt  time.Time     `json:"created_at"`
	Status     string        `json:"status"`
}

// SplitTask 拆分任务结构
type SplitTask struct {
	TaskID       string        `json:"task_id"`
	FileID       string        `json:"file_id"`
	Chapters     []ChapterInfo `json:"chapters"`
	Status       string        `json:"status"` // pending, processing, completed, failed
	Progress     int           `json:"progress"` // 0-100
	ErrorMessage *string       `json:"error_message,omitempty"`
	CreatedAt    time.Time     `json:"created_at"`
	CompletedAt  *time.Time    `json:"completed_at,omitempty"`
}

// UploadResponse 上传响应结构
type UploadResponse struct {
	FileID   string `json:"file_id"`
	Filename string `json:"filename"`
	FileSize int64  `json:"file_size"`
	Message  string `json:"message"`
}

// AnalyzeRequest 分析请求结构
type AnalyzeRequest struct {
	FileID string `json:"file_id" binding:"required"`
}

// AnalyzeResponse 分析响应结构
type AnalyzeResponse struct {
	Chapters   []ChapterInfo `json:"chapters"`
	TotalPages int           `json:"total_pages"`
}

// SplitRequest 拆分请求结构
type SplitRequest struct {
	FileID   string        `json:"file_id" binding:"required"`
	Chapters []ChapterInfo `json:"chapters" binding:"required"`
}

// SplitResponse 拆分响应结构
type SplitResponse struct {
	TaskID        string   `json:"task_id"`
	Status        string   `json:"status"`
	DownloadLinks []string `json:"download_links,omitempty"`
}

// ErrorResponse 错误响应结构
type ErrorResponse struct {
	Error   string      `json:"error"`
	Message string      `json:"message"`
	Details interface{} `json:"details,omitempty"`
}