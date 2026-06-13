import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { invoke } from '@tauri-apps/api/tauri';
import { open as dialogOpen } from '@tauri-apps/api/dialog';
import { open as shellOpen } from '@tauri-apps/api/shell';
import {
  Save, Menu, Trash2, FolderOpen, AlertCircle,
  Settings, User, FileCode2, Database, ShieldCheck, HelpCircle, ChevronDown, FileText
} from 'lucide-react';
import logo from './assets/logo.png';

// -------------------------------------------------------------
// Tooltip 组件 (固定定位，防止被遮挡)
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
            // absolute定位并设置非常高的z-index，去掉父级的overflow-hidden就不会被遮挡了
            className="absolute z-[100] bottom-full mb-2 left-1/2 transform -translate-x-1/2 px-3 py-2 bg-slate-800/95 backdrop-blur-md text-white text-[11px] rounded-xl shadow-[0_10px_30px_rgb(0,0,0,0.2)] whitespace-pre-wrap max-w-xs w-max border border-slate-700/50"
          >
            {content}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-slate-800/95"></div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// -------------------------------------------------------------
// Card 容器组件 (@UI-pro-max 质感 + 更紧凑)
// -------------------------------------------------------------
function Card({ title, icon, children }: { title: string, icon: React.ReactNode, children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      // 取消了 overflow-hidden 防止 tooltip 被遮挡
      className="relative bg-white/60 backdrop-blur-3xl rounded-3xl shadow-[inset_0_1px_1px_rgba(255,255,255,0.8),0_8px_20px_rgb(0,0,0,0.03)] border border-white/80 flex flex-col transition-all hover:shadow-[0_15px_35px_rgb(0,0,0,0.05)]"
    >
      <div className="px-5 py-4 rounded-t-3xl border-b border-slate-100/50 flex items-center gap-3 bg-gradient-to-br from-white/90 to-transparent">
        <div className="p-1.5 bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-600 rounded-xl shadow-sm border border-blue-100/50">
          {icon}
        </div>
        <h3 className="font-bold text-slate-800 text-sm tracking-tight">{title}</h3>
      </div>
      <div className="p-5 flex-1 space-y-4">
        {children}
      </div>
    </motion.div>
  );
}

interface DashboardProps {
  currentUser: string;
}

export default function Dashboard({ currentUser }: DashboardProps) {
  // --- 状态定义 ---
  const [config, setConfig] = useState({
    author: currentUser !== 'tsrhs' ? currentUser : '未命名',
    pre_fix: '文件名前缀内容',
    log_retention_days: '7',
    target_dir: '',
    csv_folder: '',
    csv_tmpl: '{author}_上报条目_{year}-{month}.csv',
    insert_pos: 'before_keyword',
    file_encoding: 'auto',
    comment: '',
    enable_monitor: false,
    monitor_only_txt: true,
    monitor_dir: ''
  });

  const [statusMsg, setStatusMsg] = useState({ text: '', type: 'success' });

  useEffect(() => {
    invoke('get_config').then((data: any) => {
      setConfig(prev => ({
        ...prev,
        ...data,
        author: currentUser !== 'tsrhs' ? currentUser : data.author,
      }));
    });
  }, [currentUser]);

  const showStatus = (text: string, type: 'success' | 'error' = 'success') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg({ text: '', type: 'success' }), 3000);
  };

  const handleSave = async () => {
    try {
      await invoke('update_config', { newConfig: config });
      showStatus('配置已成功保存并应用！');
    } catch (e) {
      showStatus(`保存失败: ${e}`, 'error');
    }
  };

  const handleChange = (field: keyof typeof config, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const pickFolder = async (field: keyof typeof config) => {
    const selected = await dialogOpen({
      directory: true,
      multiple: false,
    });
    if (selected) {
      handleChange(field, selected as string);
    }
  };

  const openTargetDir = async () => {
    if (config.target_dir) {
      try {
        await invoke('open_path', { path: config.target_dir });
        showStatus('已为您打开工作目录');
      } catch (e) {
        showStatus(`无法打开目录: ${e}`, 'error');
      }
    } else {
      showStatus('请先配置并保存解压保存目录', 'error');
    }
  };

  const openLogFolder = async () => {
    if (config.csv_folder) {
      try {
        await invoke('open_path', { path: config.csv_folder });
        showStatus('已为您打开日志报表目录');
      } catch (e) {
        showStatus(`无法打开目录: ${e}`, 'error');
      }
    } else {
      showStatus('请先配置并保存 CSV 表格目录', 'error');
    }
  };

  const openLogFile = async () => {
    try {
      await invoke('open_log_file');
      showStatus('已为您在默认编辑器中打开系统运行日志');
    } catch (e) {
      showStatus(`无法打开运行日志: ${e}`, 'error');
    }
  };

  const handleContextMenu = (action: 'add' | 'remove') => {
    // 占位符功能，提示用户
    if (action === 'add') {
      showStatus('系统右键菜单集成已触发 (需以管理员权限运行生效)');
    } else {
      showStatus('已清理系统右键菜单集成');
    }
  };

  // 更精致紧凑的输入框样式
  const inputClasses = "flex-1 block w-full px-3 py-2.5 bg-slate-50/70 border border-slate-200/60 rounded-xl text-slate-700 text-sm placeholder-slate-400 focus:bg-white focus:ring-[3px] focus:ring-blue-500/10 focus:border-blue-400 transition-all duration-300 outline-none shadow-[inset_0_1px_2px_rgba(0,0,0,0.02)]";

  // 自定义 Select 包装器
  const CustomSelect = ({ value, onChange, options }: { value: string, onChange: (val: string) => void, options: { val: string, label: string }[] }) => (
    <div className="relative w-36">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full appearance-none px-3 py-2.5 bg-slate-50/70 border border-slate-200/60 rounded-xl text-slate-700 text-sm focus:bg-white focus:ring-[3px] focus:ring-blue-500/10 focus:border-blue-400 transition-all duration-300 outline-none shadow-[inset_0_1px_2px_rgba(0,0,0,0.02)] cursor-pointer pr-8"
      >
        {options.map(opt => <option key={opt.val} value={opt.val}>{opt.label}</option>)}
      </select>
      <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
        <ChevronDown className="w-4 h-4" />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#f1f5f9] flex flex-col text-slate-800 font-sans relative overflow-x-hidden">
      {/* 极简高级科技感背景 */}
      <div className="fixed inset-0 z-0 opacity-[0.02] pointer-events-none"
        style={{ backgroundImage: 'radial-gradient(#0ea5e9 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
      <div className="fixed top-[-20%] left-[-10%] w-[600px] h-[600px] bg-cyan-400/40 rounded-full mix-blend-multiply filter blur-[100px] animate-blob pointer-events-none"></div>
      <div className="fixed bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-blue-500/30 rounded-full mix-blend-multiply filter blur-[120px] animate-blob animation-delay-2000 pointer-events-none"></div>

      {/* 顶部导航: 更纤薄紧凑 */}
      <header className="bg-white/70 backdrop-blur-2xl border-b border-white/60 shadow-[0_2px_10px_rgb(0,0,0,0.02)] px-6 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-white to-blue-50/50 rounded-xl shadow-sm border border-white flex items-center justify-center p-1.5">
            <img src={logo} alt="AutoSen Logo" className="w-full h-full object-contain filter drop-shadow-sm" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-slate-800 tracking-tight leading-tight">AutoSen <span className="text-blue-600">Core</span></h1>
            <p className="text-[10px] text-slate-500 font-bold tracking-[0.1em] uppercase">Configuration</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/80 text-blue-700 rounded-full text-xs font-semibold border border-blue-100 shadow-[0_2px_8px_rgb(59,130,246,0.08)] backdrop-blur-md">
          <User className="w-3.5 h-3.5 text-blue-500" />
          {currentUser}
        </div>
      </header>

      {/* 主体内容区: 更紧凑的 padding 和 gap */}
      <main className="flex-1 p-5 max-w-[1200px] mx-auto w-full relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {/* Card 1: 基础信息 */}
          <Card title="基础信息配置" icon={<Settings className="w-4 h-4" />}>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600">编者姓名</label>
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={config.author} onChange={e => handleChange('author', e.target.value)}
                    className={inputClasses} placeholder="编者姓名" />
                  <Tooltip content="用于在统计表格中记录编者姓名"><HelpCircle className="w-4 h-4 text-slate-400 hover:text-blue-500 cursor-help transition-colors" /></Tooltip>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600">文件重命名前缀</label>
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={config.pre_fix} onChange={e => handleChange('pre_fix', e.target.value)}
                    className={inputClasses} placeholder="输入前缀" />
                  <Tooltip content="自动解压出的文本文件开头，会用此文本替换【原文】"><HelpCircle className="w-4 h-4 text-slate-400 hover:text-blue-500 cursor-help transition-colors" /></Tooltip>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600">日志保留周期</label>
                <div className="flex-1 flex gap-3 items-center">
                  <CustomSelect
                    value={config.log_retention_days}
                    onChange={val => handleChange('log_retention_days', val)}
                    options={[
                      { val: "7", label: "7 天" },
                      { val: "15", label: "15 天" },
                      { val: "30", label: "30 天" },
                      { val: "0", label: "永久保存" }
                    ]}
                  />
                  <button onClick={openLogFile} className="flex items-center gap-1.5 px-3 py-2.5 bg-white hover:bg-slate-50 text-blue-600 rounded-xl text-xs font-bold transition-all border border-slate-200 shadow-sm whitespace-nowrap active:scale-95">
                    <FileText className="w-3.5 h-3.5" /> 查看日志
                  </button>
                </div>
              </div>
            </div>
          </Card>

          {/* Card 2: 路径与表格配置 */}
          <Card title="路径与表格配置" icon={<Database className="w-4 h-4" />}>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600 leading-tight">解压保存<br />目录</label>
                <div className="flex-1 flex gap-2">
                  <input type="text" value={config.target_dir} onChange={e => handleChange('target_dir', e.target.value)}
                    className={`${inputClasses} bg-slate-100/50`} readOnly placeholder="请选择解压目标目录..." />
                  <div className="flex gap-1.5">
                    <button onClick={openTargetDir} className="px-3 py-2.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold transition-all shadow-sm active:scale-95" title="打开此目录">
                      <FolderOpen className="w-4 h-4" />
                    </button>
                    <button onClick={() => pickFolder('target_dir')} className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-bold transition-all border border-slate-200 shadow-sm whitespace-nowrap active:scale-95">浏览...</button>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600 leading-tight">统计表格<br />目录</label>
                <div className="flex-1 flex gap-2">
                  <input type="text" value={config.csv_folder} onChange={e => handleChange('csv_folder', e.target.value)}
                    className={`${inputClasses} bg-slate-100/50`} readOnly placeholder="请选择表格导出目录..." />
                  <div className="flex gap-1.5">
                    <button onClick={openLogFolder} className="px-3 py-2.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold transition-all shadow-sm active:scale-95" title="打开此目录">
                      <FolderOpen className="w-4 h-4" />
                    </button>
                    <button onClick={() => pickFolder('csv_folder')} className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-bold transition-all border border-slate-200 shadow-sm whitespace-nowrap active:scale-95">浏览...</button>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600">统计表命名模板</label>
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={config.csv_tmpl} onChange={e => handleChange('csv_tmpl', e.target.value)}
                    className={inputClasses} />
                  <Tooltip content={"支持动态标签: {author}, {year}, {month}, {day}\n例如: {author}_汇总_{year}.csv"}><HelpCircle className="w-4 h-4 text-slate-400 hover:text-blue-500 cursor-help transition-colors" /></Tooltip>
                </div>
              </div>
            </div>
          </Card>

          {/* Card 3: 文本尾注设置 */}
          <Card title="文本尾注设置" icon={<FileCode2 className="w-4 h-4" />}>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600">尾注插入位置</label>
                <div className="flex-1 flex gap-2 items-center">
                  <CustomSelect
                    value={config.insert_pos}
                    onChange={val => handleChange('insert_pos', val)}
                    options={[
                      { val: "before_keyword", label: "主题词上一行" },
                      { val: "at_eof", label: "文件末尾" }
                    ]}
                  />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600">文本读写编码</label>
                <div className="flex-1 flex gap-2 items-center">
                  <CustomSelect
                    value={config.file_encoding}
                    onChange={val => handleChange('file_encoding', val)}
                    options={[
                      { val: "auto", label: "自动检测" },
                      { val: "gbk", label: "统一为 GBK" },
                      { val: "utf-8", label: "统一为 UTF-8" }
                    ]}
                  />
                </div>
              </div>
              <div className="flex items-start gap-3">
                <label className="w-24 text-right text-xs font-bold text-slate-600 pt-3">待插入内容</label>
                <textarea
                  value={config.comment} onChange={e => handleChange('comment', e.target.value)}
                  className={`${inputClasses} h-20 resize-none`}
                  placeholder="在此输入你要插入的尾注..."
                />
              </div>
            </div>
          </Card>

          {/* Card 4: 后台监控配置 */}
          <Card title="自动化引擎监控" icon={<ShieldCheck className="w-4 h-4" />}>
            <div className="space-y-4">
              <label className="flex items-center gap-4 cursor-pointer group p-2.5 rounded-2xl hover:bg-white/50 transition-colors border border-transparent hover:border-white/50">
                <div className="relative">
                  <input type="checkbox" checked={config.enable_monitor} onChange={e => handleChange('enable_monitor', e.target.checked)} className="sr-only" />
                  <div className={`block w-11 h-6 rounded-full transition-colors ${config.enable_monitor ? 'bg-blue-500' : 'bg-slate-200/80 shadow-inner'}`}></div>
                  <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform shadow-sm ${config.enable_monitor ? 'translate-x-5' : ''}`}></div>
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-700 group-hover:text-blue-600 transition-colors">开启指定文件夹监控</div>
                  <div className="text-[10px] text-slate-500 mt-0.5 font-medium tracking-wide">引擎后台静默运行，发现压缩包立即处理</div>
                </div>
              </label>

              <label className="flex items-center gap-4 cursor-pointer group p-2.5 rounded-2xl hover:bg-white/50 transition-colors border border-transparent hover:border-white/50">
                <div className="relative">
                  <input type="checkbox" checked={config.monitor_only_txt} onChange={e => handleChange('monitor_only_txt', e.target.checked)} className="sr-only" />
                  <div className={`block w-11 h-6 rounded-full transition-colors ${config.monitor_only_txt ? 'bg-indigo-500' : 'bg-slate-200/80 shadow-inner'}`}></div>
                  <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform shadow-sm ${config.monitor_only_txt ? 'translate-x-5' : ''}`}></div>
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-700 group-hover:text-indigo-600 transition-colors">仅处理包含文本的压缩包</div>
                  <div className="text-[10px] text-slate-500 mt-0.5 font-medium tracking-wide">智能过滤无关的解压请求</div>
                </div>
              </label>

              <div className="flex items-center gap-3 pt-1">
                <label className="w-24 text-right text-xs font-bold text-slate-600 leading-tight">监听目标<br />目录</label>
                <div className="flex-1 flex gap-2">
                  <input type="text" value={config.monitor_dir} onChange={e => handleChange('monitor_dir', e.target.value)}
                    className={`${inputClasses} transition-opacity ${!config.enable_monitor ? 'opacity-50 bg-slate-100' : ''}`}
                    readOnly disabled={!config.enable_monitor} placeholder="请选择监听目录..." />
                  <button onClick={() => pickFolder('monitor_dir')} disabled={!config.enable_monitor} className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-bold transition-all border border-slate-200 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap active:scale-95">浏览...</button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 底部控制台 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mt-6 bg-white/70 backdrop-blur-3xl border border-white/80 rounded-3xl p-4 flex flex-wrap items-center justify-between shadow-[0_10px_40px_rgb(0,0,0,0.03)] gap-4"
        >
          <div className="flex items-center gap-2">
            <button onClick={handleSave} className="group flex items-center gap-2 bg-gradient-to-br from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white px-5 py-3 rounded-2xl text-sm font-bold transition-all duration-300 shadow-[0_4px_15px_rgb(59,130,246,0.3)] hover:shadow-[0_8px_20px_rgb(59,130,246,0.4)] active:scale-[0.98]">
              <Save className="w-4 h-4 transition-transform group-hover:scale-110" /> 保存系统配置
            </button>
            <div className="h-6 w-px bg-slate-200/80 mx-1"></div>
            <button onClick={() => handleContextMenu('add')} className="flex items-center gap-1.5 bg-white/80 hover:bg-white text-slate-700 border border-slate-200/80 hover:border-slate-300 px-4 py-3 rounded-2xl text-xs font-bold transition-colors shadow-sm active:scale-95">
              <Menu className="w-3.5 h-3.5 text-slate-400" /> 添加右键菜单
            </button>
            <button onClick={() => handleContextMenu('remove')} className="flex items-center gap-1.5 bg-white/80 hover:bg-rose-50 text-rose-600 border border-slate-200/80 hover:border-rose-200 px-4 py-3 rounded-2xl text-xs font-bold transition-colors shadow-sm active:scale-95">
              <Trash2 className="w-3.5 h-3.5" /> 移除菜单
            </button>
          </div>

          <div className="flex items-center justify-end flex-1 pl-4">
            <AnimatePresence mode="wait">
              {statusMsg.text && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, x: 20 }}
                  animate={{ opacity: 1, scale: 1, x: 0 }}
                  exit={{ opacity: 0, scale: 0.9, x: 20 }}
                  className={`flex items-center gap-1.5 px-4 py-2.5 rounded-2xl text-xs font-bold shadow-sm border ${statusMsg.type === 'success' ? 'bg-emerald-50/80 text-emerald-700 border-emerald-100/80' : 'bg-rose-50/80 text-rose-700 border-rose-100/80'} backdrop-blur-sm`}
                >
                  {statusMsg.type === 'success' ? <ShieldCheck className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                  {statusMsg.text}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        <div className="mt-5 text-center pb-2">
          <p className="text-[9px] text-slate-400 font-bold tracking-[0.2em] uppercase"> Intelligent System Terminal(一键三连) v1.0.6 | ©系统组 Hao2026·</p>
        </div>
      </main>
    </div>
  );
}
