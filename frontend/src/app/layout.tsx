import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PDF对话助手',
  description: '智能PDF分析与对话平台',
  keywords: ['PDF', '对话', '知识图谱', '智能分析', '在线工具'],
  authors: [{ name: 'PDF对话助手团队' }],
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <main>
            {children}
          </main>
          
          {/* 页脚 */}
          <footer className="bg-white border-t border-gray-200 mt-auto">
            <div className="container mx-auto px-4 py-6">
              <div className="text-center text-sm text-gray-600">
                <p>© 2025 PDF对话助手 - 智能PDF分析与对话平台</p>
                <p className="mt-1">
                  支持最大50MB文件 | 
                  <a href="#" className="text-primary-500 hover:text-primary-600 ml-1">
                    使用帮助
                  </a>
                </p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}