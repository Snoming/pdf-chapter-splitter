package config

import (
	"os"
	"strconv"
)

// Config 应用配置结构
type Config struct {
	Port        string // 服务端口
	Environment string // 运行环境
	UploadDir   string // 上传文件目录
	TempDir     string // 临时文件目录
	MaxFileSize int64  // 最大文件大小（字节）
	AIServiceURL string // AI服务URL
}

// Load 加载配置
func Load() *Config {
	cfg := &Config{
		Port:        getEnv("PORT", "8080"),
		Environment: getEnv("ENVIRONMENT", "development"),
		UploadDir:   getEnv("UPLOAD_DIR", "./uploads"),
		TempDir:     getEnv("TEMP_DIR", "./temp"),
		MaxFileSize: getEnvInt64("MAX_FILE_SIZE", 50*1024*1024), // 默认50MB
		AIServiceURL: getEnv("AI_SERVICE_URL", "http://localhost:8000"),
	}

	return cfg
}

// getEnv 获取环境变量，如果不存在则返回默认值
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvInt64 获取int64类型的环境变量
func getEnvInt64(key string, defaultValue int64) int64 {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.ParseInt(value, 10, 64); err == nil {
			return intValue
		}
	}
	return defaultValue
}