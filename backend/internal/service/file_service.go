package service

import (
	"fmt"
	"mime/multipart"
	"os"
	"path/filepath"
	"time"

	"pdf-chapter-splitter-backend/internal/config"
	"pdf-chapter-splitter-backend/internal/models"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// FileService 文件服务
type FileService struct {
	config *config.Config
}

// NewFileService 创建新的文件服务实例
func NewFileService(cfg *config.Config) *FileService {
	return &FileService{
		config: cfg,
	}
}

// SaveUploadedFile 保存上传的文件
func (fs *FileService) SaveUploadedFile(file *multipart.FileHeader) (*models.FileInfo, error) {
	// 生成唯一文件ID
	fileID := uuid.New().String()
	
	// 创建文件目录
	fileDir := filepath.Join(fs.config.UploadDir, fileID)
	if err := os.MkdirAll(fileDir, 0755); err != nil {
		return nil, fmt.Errorf("创建文件目录失败: %w", err)
	}

	// 构建文件路径
	filePath := filepath.Join(fileDir, "original.pdf")

	// 打开上传的文件
	src, err := file.Open()
	if err != nil {
		return nil, fmt.Errorf("打开上传文件失败: %w", err)
	}
	defer src.Close()

	// 创建目标文件
	dst, err := os.Create(filePath)
	if err != nil {
		return nil, fmt.Errorf("创建目标文件失败: %w", err)
	}
	defer dst.Close()

	// 复制文件内容
	if _, err := dst.ReadFrom(src); err != nil {
		return nil, fmt.Errorf("复制文件内容失败: %w", err)
	}

	// 创建文件信息
	fileInfo := &models.FileInfo{
		FileID:     fileID,
		Filename:   file.Filename,
		FileSize:   file.Size,
		FilePath:   filePath,
		UploadTime: time.Now(),
		Status:     "uploaded",
	}

	// 保存元数据
	if err := fs.saveMetadata(fileInfo); err != nil {
		logrus.WithError(err).Warn("保存文件元数据失败")
	}

	return fileInfo, nil
}

// GetDownloadPath 获取下载文件路径
func (fs *FileService) GetDownloadPath(fileID string) (string, string, error) {
	// 检查原始文件
	originalPath := filepath.Join(fs.config.UploadDir, fileID, "original.pdf")
	if _, err := os.Stat(originalPath); err == nil {
		return originalPath, "original.pdf", nil
	}

	// 检查章节文件目录
	chaptersDir := filepath.Join(fs.config.UploadDir, fileID, "chapters")
	if _, err := os.Stat(chaptersDir); err == nil {
		// 返回第一个章节文件作为示例
		files, err := os.ReadDir(chaptersDir)
		if err == nil && len(files) > 0 {
			firstFile := files[0]
			if !firstFile.IsDir() {
				filePath := filepath.Join(chaptersDir, firstFile.Name())
				return filePath, firstFile.Name(), nil
			}
		}
	}

	return "", "", fmt.Errorf("文件不存在")
}

// GetFileInfo 获取文件信息
func (fs *FileService) GetFileInfo(fileID string) (*models.FileInfo, error) {
	metadataPath := filepath.Join(fs.config.UploadDir, fileID, "metadata.json")
	
	// 这里应该从JSON文件读取元数据
	// 为了简化，暂时返回基本信息
	originalPath := filepath.Join(fs.config.UploadDir, fileID, "original.pdf")
	if _, err := os.Stat(originalPath); err != nil {
		return nil, fmt.Errorf("文件不存在")
	}

	stat, err := os.Stat(originalPath)
	if err != nil {
		return nil, fmt.Errorf("获取文件信息失败: %w", err)
	}

	return &models.FileInfo{
		FileID:     fileID,
		Filename:   "original.pdf",
		FileSize:   stat.Size(),
		FilePath:   originalPath,
		UploadTime: stat.ModTime(),
		Status:     "uploaded",
	}, nil
}

// saveMetadata 保存文件元数据
func (fs *FileService) saveMetadata(fileInfo *models.FileInfo) error {
	// 这里应该将元数据保存到JSON文件
	// 为了简化实现，暂时跳过
	logrus.WithField("file_id", fileInfo.FileID).Debug("元数据保存跳过")
	return nil
}

// CleanupTempFiles 清理临时文件
func (fs *FileService) CleanupTempFiles() error {
	// 清理超过24小时的临时文件
	cutoff := time.Now().Add(-24 * time.Hour)
	
	return filepath.Walk(fs.config.TempDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if !info.IsDir() && info.ModTime().Before(cutoff) {
			logrus.WithField("path", path).Debug("清理临时文件")
			return os.Remove(path)
		}
		
		return nil
	})
}