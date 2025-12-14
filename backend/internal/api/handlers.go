package api

import (
	"net/http"
	"path/filepath"

	"pdf-chapter-splitter-backend/internal/config"
	"pdf-chapter-splitter-backend/internal/models"
	"pdf-chapter-splitter-backend/internal/service"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// Handlers API处理器结构
type Handlers struct {
	config      *config.Config
	fileService *service.FileService
	pdfService  *service.PDFService
}

// NewHandlers 创建新的处理器实例
func NewHandlers(cfg *config.Config, fileService *service.FileService, pdfService *service.PDFService) *Handlers {
	return &Handlers{
		config:      cfg,
		fileService: fileService,
		pdfService:  pdfService,
	}
}

// UploadFile 处理文件上传
func (h *Handlers) UploadFile(c *gin.Context) {
	// 获取上传的文件
	file, err := c.FormFile("file")
	if err != nil {
		logrus.WithError(err).Error("获取上传文件失败")
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "INVALID_FILE",
			Message: "无效的文件上传",
		})
		return
	}

	// 验证文件大小
	if file.Size > h.config.MaxFileSize {
		logrus.WithField("size", file.Size).Error("文件大小超过限制")
		c.JSON(http.StatusRequestEntityTooLarge, models.ErrorResponse{
			Error:   "FILE_TOO_LARGE",
			Message: "文件大小超过50MB限制",
		})
		return
	}

	// 验证文件格式
	if filepath.Ext(file.Filename) != ".pdf" {
		logrus.WithField("filename", file.Filename).Error("文件格式不支持")
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "INVALID_FORMAT",
			Message: "仅支持PDF文件格式",
		})
		return
	}

	// 保存文件
	fileInfo, err := h.fileService.SaveUploadedFile(file)
	if err != nil {
		logrus.WithError(err).Error("保存文件失败")
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "SAVE_FAILED",
			Message: "文件保存失败",
		})
		return
	}

	logrus.WithField("file_id", fileInfo.FileID).Info("文件上传成功")

	c.JSON(http.StatusOK, models.UploadResponse{
		FileID:   fileInfo.FileID,
		Filename: fileInfo.Filename,
		FileSize: fileInfo.FileSize,
		Message:  "文件上传成功",
	})
}

// AnalyzeChapters 处理章节分析
func (h *Handlers) AnalyzeChapters(c *gin.Context) {
	var req models.AnalyzeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "INVALID_REQUEST",
			Message: "请求参数无效",
		})
		return
	}

	// 调用PDF服务进行章节分析
	chapters, totalPages, err := h.pdfService.AnalyzeChapters(req.FileID)
	if err != nil {
		logrus.WithError(err).WithField("file_id", req.FileID).Error("章节分析失败")
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "ANALYSIS_FAILED",
			Message: "章节分析失败",
		})
		return
	}

	logrus.WithField("file_id", req.FileID).WithField("chapters", len(chapters)).Info("章节分析完成")

	c.JSON(http.StatusOK, models.AnalyzeResponse{
		Chapters:   chapters,
		TotalPages: totalPages,
	})
}

// SplitPDF 处理PDF拆分
func (h *Handlers) SplitPDF(c *gin.Context) {
	var req models.SplitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "INVALID_REQUEST",
			Message: "请求参数无效",
		})
		return
	}

	// 创建拆分任务
	task, err := h.pdfService.CreateSplitTask(req.FileID, req.Chapters)
	if err != nil {
		logrus.WithError(err).WithField("file_id", req.FileID).Error("创建拆分任务失败")
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "TASK_CREATION_FAILED",
			Message: "创建拆分任务失败",
		})
		return
	}

	logrus.WithField("task_id", task.TaskID).Info("拆分任务创建成功")

	c.JSON(http.StatusOK, models.SplitResponse{
		TaskID: task.TaskID,
		Status: task.Status,
	})
}

// DownloadFile 处理文件下载
func (h *Handlers) DownloadFile(c *gin.Context) {
	fileID := c.Param("file_id")
	if fileID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "INVALID_FILE_ID",
			Message: "文件ID无效",
		})
		return
	}

	// 获取文件路径
	filePath, filename, err := h.fileService.GetDownloadPath(fileID)
	if err != nil {
		logrus.WithError(err).WithField("file_id", fileID).Error("获取下载文件失败")
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "FILE_NOT_FOUND",
			Message: "文件不存在",
		})
		return
	}

	logrus.WithField("file_id", fileID).Info("开始文件下载")

	// 设置下载头
	c.Header("Content-Disposition", "attachment; filename="+filename)
	c.Header("Content-Type", "application/pdf")
	
	// 发送文件
	c.File(filePath)
}

// GetTaskStatus 获取任务状态
func (h *Handlers) GetTaskStatus(c *gin.Context) {
	taskID := c.Param("task_id")
	if taskID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "INVALID_TASK_ID",
			Message: "任务ID无效",
		})
		return
	}

	// 获取任务状态
	task, err := h.pdfService.GetTaskStatus(taskID)
	if err != nil {
		logrus.WithError(err).WithField("task_id", taskID).Error("获取任务状态失败")
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "TASK_NOT_FOUND",
			Message: "任务不存在",
		})
		return
	}

	c.JSON(http.StatusOK, task)
}

// HealthCheck 健康检查
func (h *Handlers) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "pdf-chapter-splitter-backend",
		"version": "1.0.0",
	})
}