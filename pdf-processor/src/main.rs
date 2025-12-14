//! PDF处理引擎命令行工具
//! 
//! 提供PDF文件拆分的命令行接口

use clap::{Arg, Command};
use pdf_processor::{PdfSplitter, ChapterDefinition, ProcessResult};
use serde_json;
use std::fs;
use std::path::Path;
use tracing::{info, error, Level};
use tracing_subscriber;

fn main() -> anyhow::Result<()> {
    // 初始化日志
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();

    // 解析命令行参数
    let matches = Command::new("pdf-processor")
        .version("1.0.0")
        .author("PDF Chapter Splitter Team")
        .about("高性能PDF处理引擎")
        .subcommand(
            Command::new("split")
                .about("拆分PDF文件为章节")
                .arg(
                    Arg::new("input")
                        .short('i')
                        .long("input")
                        .value_name("FILE")
                        .help("输入PDF文件路径")
                        .required(true)
                )
                .arg(
                    Arg::new("chapters")
                        .short('c')
                        .long("chapters")
                        .value_name("FILE")
                        .help("章节定义JSON文件路径")
                        .required(true)
                )
                .arg(
                    Arg::new("output")
                        .short('o')
                        .long("output")
                        .value_name("DIR")
                        .help("输出目录路径")
                        .required(true)
                )
        )
        .subcommand(
            Command::new("validate")
                .about("验证PDF文件")
                .arg(
                    Arg::new("input")
                        .short('i')
                        .long("input")
                        .value_name("FILE")
                        .help("输入PDF文件路径")
                        .required(true)
                )
        )
        .get_matches();

    match matches.subcommand() {
        Some(("split", sub_matches)) => {
            let input_path = sub_matches.get_one::<String>("input").unwrap();
            let chapters_path = sub_matches.get_one::<String>("chapters").unwrap();
            let output_dir = sub_matches.get_one::<String>("output").unwrap();

            info!("开始拆分PDF文件: {}", input_path);
            
            // 读取章节定义
            let chapters = load_chapters_from_file(chapters_path)?;
            
            // 创建输出目录
            fs::create_dir_all(output_dir)?;
            
            // 执行拆分
            let splitter = PdfSplitter::new();
            match splitter.split_pdf(input_path, &chapters, output_dir) {
                Ok(result) => {
                    if result.success {
                        info!("PDF拆分成功完成！");
                        info!("处理文件数: {}", result.files_processed);
                        info!("总页数: {}", result.total_pages);
                    } else {
                        error!("PDF拆分失败: {:?}", result.error_message);
                        std::process::exit(1);
                    }
                }
                Err(e) => {
                    error!("PDF拆分过程中发生错误: {}", e);
                    std::process::exit(1);
                }
            }
        }
        Some(("validate", sub_matches)) => {
            let input_path = sub_matches.get_one::<String>("input").unwrap();
            
            info!("验证PDF文件: {}", input_path);
            
            // 这里将在后续任务中实现PDF验证逻辑
            if Path::new(input_path).exists() {
                info!("PDF文件存在且可访问");
            } else {
                error!("PDF文件不存在或无法访问");
                std::process::exit(1);
            }
        }
        _ => {
            eprintln!("请指定一个子命令。使用 --help 查看帮助信息。");
            std::process::exit(1);
        }
    }

    Ok(())
}

/// 从JSON文件加载章节定义
fn load_chapters_from_file(path: &str) -> anyhow::Result<Vec<ChapterDefinition>> {
    let content = fs::read_to_string(path)?;
    let chapters: Vec<ChapterDefinition> = serde_json::from_str(&content)?;
    
    info!("从文件加载了 {} 个章节定义", chapters.len());
    
    // 验证章节定义
    for (i, chapter) in chapters.iter().enumerate() {
        if chapter.start_page == 0 || chapter.end_page == 0 {
            return Err(anyhow::anyhow!("章节 {} 的页码无效", i + 1));
        }
        if chapter.start_page > chapter.end_page {
            return Err(anyhow::anyhow!("章节 {} 的起始页码大于结束页码", i + 1));
        }
        if chapter.title.trim().is_empty() {
            return Err(anyhow::anyhow!("章节 {} 的标题为空", i + 1));
        }
    }
    
    Ok(chapters)
}