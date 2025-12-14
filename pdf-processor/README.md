# PDF处理引擎

基于 Rust 的高性能 PDF 处理引擎，负责PDF文件的解析、验证和拆分操作。

## 技术栈

- Rust 1.70+
- lopdf (PDF处理库)
- serde (序列化)
- tokio (异步运行时)
- clap (命令行参数解析)

## 开发环境

```bash
# 构建项目
cargo build

# 运行测试
cargo test

# 构建发布版本
cargo build --release

# 代码检查
cargo clippy

# 格式化代码
cargo fmt
```

## 项目结构

```
pdf-processor/
├── src/
│   ├── lib.rs          # 库入口
│   ├── main.rs         # 可执行文件入口
│   ├── pdf/            # PDF处理模块
│   ├── splitter/       # 拆分逻辑
│   ├── validator/      # 文件验证
│   └── ffi/           # FFI接口
├── tests/             # 测试文件
└── benches/          # 性能测试
```

## FFI接口

该引擎提供C兼容的FFI接口，供Go后端调用：

```rust
// 拆分PDF文件
pub extern "C" fn split_pdf_chapters(
    input_path: *const c_char,
    chapters: *const ChapterDefinition,
    chapter_count: usize,
    output_dir: *const c_char,
) -> ProcessResult;
```

## 使用方式

### 作为库使用

```rust
use pdf_processor::{PdfSplitter, ChapterDefinition};

let splitter = PdfSplitter::new();
let chapters = vec![
    ChapterDefinition {
        title: "第一章".to_string(),
        start_page: 1,
        end_page: 10,
    }
];

splitter.split_pdf("input.pdf", &chapters, "output/")?;
```

### 作为命令行工具使用

```bash
./pdf-processor split --input input.pdf --chapters chapters.json --output output/
```