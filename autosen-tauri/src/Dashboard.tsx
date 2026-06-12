import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Save, Menu, Trash2, FileText, FolderOpen, AlertCircle, 
  Settings, User, FileCode2, Database, ShieldCheck, HelpCircle
} from 'lucide-react';

// -------------------------------------------------------------
// Tooltip 组件 (悬浮气泡提示)
// -------------------------------------------------------------
function Tooltip({ children, content }: { children: React.ReactNode, content: string }) {
  const [show, setShow] = useState(false);
  return (
    <div 
      className="relative flex items-center" 
      onMouseEnter={() => setShow(true)} 
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <AnimatePresence>
        {show && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute z-50 bottom-full mb-2 left-1/2 transform -translate-x-1/2 px-3 py-2 bg-gray-800 text-white text-xs rounded shadow-lg whitespace-pre-wrap max-w-xs w-max"
          >
            {content}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// -------------------------------------------------------------
// Card 容器组件
// -------------------------------------------------------------
function Card({ title, icon, children }: { title: string, icon: React.ReactNode, children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col transition-shadow hover:shadow-md">
      <div className="px-5 py-4 border-b border-gray-50 flex items-center gap-2 bg-gray-50/50">
        <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
          {icon}
        </div>
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="p-5 flex-1 space-y-4">
        {children}
      </div>
    </div>
  );
}

interface DashboardProps {
  currentUser: string;
}

export default function Dashboard({ currentUser }: DashboardProps) {
  // --- 状态定义 (模拟配置项) ---
  const [config, setConfig] = useState({
    author: currentUser !== 'tsrhs' ? currentUser : '未命名',
    preFix: '（文件前缀名）',
    logRetentionDays: '7',
    targetDir: '',
    csvFolder: '',
    csvTmpl: '{author}_上报条目_{year}-{month}.csv',
    insertPos: 'before_keyword',
    fileEncoding: 'auto',
    comment: '',
    enableMonitor: false,
    monitorOnlyTxt: true,
    monitorDir: ''
  });

  const [statusMsg, setStatusMsg] = useState({ text: '', type: 'success' });

  // 模拟保存和处理函数
  const showStatus = (text: string, type: 'success' | 'error' = 'success') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg({ text: '', type: 'success' }), 3000);
  };

  const handleSave = () => {
    // 实际将调用 Tauri Rust API 写入 config.json
    showStatus('✅ 配置已成功保存！');
  };

  const handleChange = (field: keyof typeof config, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col text-gray-800 font-sans">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl shadow-sm flex items-center justify-center">
            <Settings className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">自动化解压处理工具</h1>
            <p className="text-xs text-gray-500 font-medium">系统全局配置中心</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm font-medium border border-blue-100">
          <User className="w-4 h-4" />
          {currentUser}
        </div>
      </header>

      {/* 主体内容区 */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card 1: 基础信息 */}
          <Card title="基础信息" icon={<User className="w-5 h-5" />}>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="w-28 text-right text-sm font-medium text-gray-600">编者:</label>
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={config.author} onChange={e => handleChange('author', e.target.value)}
                         className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                  <Tooltip content="用于在统计表格中记录编者姓名"><HelpCircle className="w-4 h-4 text-gray-400 cursor-help" /></Tooltip>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="w-28 text-right text-sm font-medium text-gray-600">重命名前缀:</label>
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={config.preFix} onChange={e => handleChange('preFix', e.target.value)}
                         className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                  <Tooltip content="自动解压出的文本文件开头，会用此文本替换【原文】"><HelpCircle className="w-4 h-4 text-gray-400 cursor-help" /></Tooltip>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="w-28 text-right text-sm font-medium text-gray-600">日志保留周期:</label>
                <div className="flex-1 flex gap-2 items-center">
                  <select value={config.logRetentionDays} onChange={e => handleChange('logRetentionDays', e.target.value)}
                          className="w-32 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="7">7 天</option>
                    <option value="15">15 天</option>
                    <option value="30">30 天</option>
                    <option value="0">永久 (0)</option>
                  </select>
                </div>
              </div>
            </div>
          </Card>

          {/* Card 2: 路径与表格配置 */}
          <Card title="路径与表格配置" icon={<Database className="w-5 h-5" />}>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="w-32 text-right text-sm font-medium text-gray-600">解压保存文件夹:</label>
                <div className="flex-1 flex gap-2">
                  <input type="text" value={config.targetDir} onChange={e => handleChange('targetDir', e.target.value)}
                         className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-gray-50" readOnly placeholder="请选择目录..." />
                  <button className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors border border-gray-200">浏览...</button>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="w-32 text-right text-sm font-medium text-gray-600">CSV 表格目录:</label>
                <div className="flex-1 flex gap-2">
                  <input type="text" value={config.csvFolder} onChange={e => handleChange('csvFolder', e.target.value)}
                         className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-gray-50" readOnly placeholder="请选择目录..." />
                  <button className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors border border-gray-200">浏览...</button>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="w-32 text-right text-sm font-medium text-gray-600">CSV 命名模板:</label>
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={config.csvTmpl} onChange={e => handleChange('csvTmpl', e.target.value)}
                         className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                  <Tooltip content={"支持动态标签: {author}, {year}, {month}, {day}\n例如: {author}_汇总_{year}.csv"}><HelpCircle className="w-4 h-4 text-gray-400 cursor-help" /></Tooltip>
                </div>
              </div>
            </div>
          </Card>

          {/* Card 3: 文本尾注设置 */}
          <Card title="文本尾注设置" icon={<FileCode2 className="w-5 h-5" />}>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="w-28 text-right text-sm font-medium text-gray-600">尾注插入位置:</label>
                <div className="flex-1 flex gap-2 items-center">
                  <select value={config.insertPos} onChange={e => handleChange('insertPos', e.target.value)}
                          className="w-40 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="before_keyword">主题词上一行</option>
                    <option value="at_eof">文件末尾</option>
                  </select>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="w-28 text-right text-sm font-medium text-gray-600">文本读写编码:</label>
                <div className="flex-1 flex gap-2 items-center">
                  <select value={config.fileEncoding} onChange={e => handleChange('fileEncoding', e.target.value)}
                          className="w-40 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="auto">自动检测</option>
                    <option value="gbk">统当为 GBK</option>
                    <option value="utf-8">统当为 UTF-8</option>
                  </select>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <label className="w-28 text-right text-sm font-medium text-gray-600 mt-2">待插入尾注内容:</label>
                <textarea 
                  value={config.comment} onChange={e => handleChange('comment', e.target.value)}
                  className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none h-24 resize-none" 
                  placeholder="在此输入你要插入的尾注..."
                />
              </div>
            </div>
          </Card>

          {/* Card 4: 后台文件夹监控 */}
          <Card title="后台文件夹监控" icon={<ShieldCheck className="w-5 h-5" />}>
            <div className="space-y-5">
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" checked={config.enableMonitor} onChange={e => handleChange('enableMonitor', e.target.checked)} className="sr-only" />
                  <div className={`block w-10 h-6 rounded-full transition-colors ${config.enableMonitor ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
                  <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${config.enableMonitor ? 'translate-x-4' : ''}`}></div>
                </div>
                <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600 transition-colors">开启指定文件夹监控 (发现新压缩包自动处理)</span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" checked={config.monitorOnlyTxt} onChange={e => handleChange('monitorOnlyTxt', e.target.checked)} className="sr-only" />
                  <div className={`block w-10 h-6 rounded-full transition-colors ${config.monitorOnlyTxt ? 'bg-indigo-500' : 'bg-gray-300'}`}></div>
                  <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${config.monitorOnlyTxt ? 'translate-x-4' : ''}`}></div>
                </div>
                <span className="text-sm font-medium text-gray-700 group-hover:text-indigo-600 transition-colors">仅当压缩包内包含 TXT 文件时才处理</span>
              </label>

              <div className="flex items-center gap-4 pt-2">
                <label className="w-24 text-right text-sm font-medium text-gray-600">监控文件夹:</label>
                <div className="flex-1 flex gap-2">
                  <input type="text" value={config.monitorDir} onChange={e => handleChange('monitorDir', e.target.value)}
                         className={`flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none transition-colors ${!config.enableMonitor ? 'bg-gray-100 text-gray-400' : 'bg-gray-50 focus:ring-2 focus:ring-blue-500'}`} 
                         readOnly disabled={!config.enableMonitor} placeholder="请选择目录..." />
                  <button disabled={!config.enableMonitor} className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors border border-gray-200 disabled:opacity-50">浏览...</button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 底部按钮栏 */}
        <div className="mt-8 bg-white border border-gray-200 rounded-2xl p-4 flex flex-wrap items-center justify-between shadow-sm gap-4">
          <div className="flex items-center gap-3">
            <button onClick={handleSave} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm active:scale-95">
              <Save className="w-4 h-4" /> 保存所有配置
            </button>
            <button className="flex items-center gap-2 bg-gray-800 hover:bg-gray-900 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm active:scale-95">
              <Menu className="w-4 h-4" /> 添加到右键菜单
            </button>
            <button className="flex items-center gap-2 bg-white hover:bg-red-50 text-red-600 border border-red-200 px-5 py-2.5 rounded-xl font-medium transition-colors active:scale-95">
              <Trash2 className="w-4 h-4" /> 移除右键菜单
            </button>
          </div>

          <div className="flex items-center gap-4">
            <AnimatePresence mode="wait">
              {statusMsg.text && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${statusMsg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}
                >
                  <AlertCircle className="w-4 h-4" /> {statusMsg.text}
                </motion.div>
              )}
            </AnimatePresence>
            <button className="flex items-center gap-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 px-5 py-2.5 rounded-xl font-medium transition-colors active:scale-95">
              <FolderOpen className="w-4 h-4 text-gray-500" /> 查看运行日志
            </button>
          </div>
        </div>
        
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-400 font-medium">AutoHao v1.0.5 | 系统组 · Copyright © 2026 All Rights Reserved</p>
        </div>
      </main>
    </div>
  );
}
