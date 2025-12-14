package api

import (
	"pdf-chapter-splitter-backend/internal/config"
	"pdf-chapter-splitter-backend/internal/service"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// SetupRouter 设置路由
func SetupRouter(cfg *config.Config, fileService *service.FileService, pdfService *service.PDFService) *gin.Engine {
	router := gin.Default()

	// CORS配置
	corsConfig := cors.DefaultConfig()
	corsConfig.AllowOrigins = []string{"http://localhost:3000", "http://127.0.0.1:3000"}
	corsConfig.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	corsConfig.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization", "X-Requested-With"}
	corsConfig.AllowCredentials = true
	router.Use(cors.New(corsConfig))

	// 创建处理器
	handlers := NewHandlers(cfg, fileService, pdfService)

	// API路由组
	api := router.Group("/api")
	{
		// 文件上传
		api.POST("/upload", handlers.UploadFile)
		
		// 章节分析
		api.POST("/analyze", handlers.AnalyzeChapters)
		
		// PDF拆分
		api.POST("/split", handlers.SplitPDF)
		
		// 文件下载
		api.GET("/download/:file_id", handlers.DownloadFile)
		
		// 任务状态查询
		api.GET("/task/:task_id", handlers.GetTaskStatus)
		
		// 健康检查
		api.GET("/health", handlers.HealthCheck)
	}

	return router
}