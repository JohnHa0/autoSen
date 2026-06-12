import { useState } from 'react';
import { Lock, User, LogIn, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

interface LoginProps {
  onLoginSuccess: (user: string) => void;
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // 强制转换为半角字符，防止中文感叹号输入错误
    let val = e.target.value;
    val = val.replace(/！/g, '!');
    setPassword(val);
  };

  const attemptLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const trimmedUser = username.trim();
    const trimmedPass = password.trim();

    if (!trimmedUser || !trimmedPass) {
      setError('请输入账号和密码');
      return;
    }

    // 管理员验证
    if (trimmedUser === 'tsrhs' && trimmedPass === '815008') {
      onLoginSuccess('tsrhs');
      return;
    }

    // 中文实名注册验证
    const chineseRegex = /^[\u4e00-\u9fa5]{2,}$/;
    if (chineseRegex.test(trimmedUser)) {
      if (trimmedPass === '12345!') {
        onLoginSuccess(trimmedUser);
        return;
      } else {
        setError('密码错误！');
        return;
      }
    }

    setError('账号或密码错误！支持纯中文姓名登录或管理员账户');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4 relative overflow-hidden">
      {/* Decorative background circles */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob"></div>
      <div className="absolute top-[20%] right-[-10%] w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
      <div className="absolute bottom-[-20%] left-[20%] w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-4000"></div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md bg-white/80 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-white/20 p-8 relative z-10"
      >
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl shadow-lg flex items-center justify-center">
            <Lock className="w-8 h-8 text-white" />
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-8 tracking-tight">欢迎使用自动化系统</h2>

        <form onSubmit={attemptLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">账 号</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow bg-white/50"
                placeholder="请输入用户名"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">密 码</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="password"
                value={password}
                onChange={handlePasswordChange}
                style={{ imeMode: 'disabled' }}
                className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow bg-white/50"
                placeholder="请输入密码"
              />
            </div>
            <p className="mt-2 text-xs text-gray-500 flex items-center">
              * 密码框强制英文模式，自动转换中文标点
            </p>
          </div>

          {error && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <p>{error}</p>
            </motion.div>
          )}

          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium py-3 px-4 rounded-xl shadow-md transition-all active:scale-[0.98]"
          >
            <LogIn className="w-5 h-5" />
            <span>登 录 进 入 统</span>
          </button>
        </form>

        <div className="mt-8 text-center border-t border-gray-100 pt-6">
          <p className="text-xs text-gray-400 font-medium">AutoHao v1.0.5 | 系统组</p>
          <p className="text-xs text-gray-400 mt-1">Copyright © 2026 All Rights Reserved</p>
        </div>
      </motion.div>
    </div>
  );
}
