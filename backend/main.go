package main

import (
	"log"
	"os"

	"pdf-chapter-splitter-backend/internal/api"
	"pdf-chapter-splitter-backend/internal/config"
	"pdf-chapter-splitter-backend/internal/service"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

func main() {
	// 初始化配置
	cfg := config.Load()

	// 设置日志级别
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
		logrus.SetLevel(logrus.InfoLevel)
	} else {
		logrus.SetLevel(logrus.DebugLevel)
	}

	// 创建上传目录
	if err := os.MkdirAll(cfg.UploadDir, 0755); err != nil {
		log.Fatalf("创建上传目录失败: %v", err)
	}

	if err := os.MkdirAll(cfg.TempDir, 0755); err != nil {
		log.Fatalf("创建临时目录失败: %v", err)
	}

	// 初始化服务
	fileService := service.NewFileService(cfg)
	pdfService := service.NewPDFService(cfg)

	// 初始化API路由
	router := api.SetupRouter(cfg, fileService, pdfService)

	// 启动服务器
	logrus.Infof("服务器启动在端口 %s", cfg.Port)
	if err := router.Run(":" + cfg.Port); err != nil {
		log.Fatalf("服务器启动失败: %v", err)
	}
}