import { useState } from 'react';
import { Lock, User, LogIn, AlertCircle, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import logo from './assets/logo.png';

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
    <div className="min-h-screen flex items-center justify-center bg-[#f8fafc] p-4 relative overflow-hidden font-sans">
      {/* 科技感网格与环境光背景 */}
      <div className="absolute inset-0 z-0 opacity-[0.03]"
        style={{ backgroundImage: 'radial-gradient(#3b82f6 1px, transparent 1px)', backgroundSize: '32px 32px' }}></div>
      <div className="absolute top-[-20%] left-[-10%] w-[800px] h-[800px] bg-cyan-300 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-blob"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[800px] h-[800px] bg-blue-300 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-blob animation-delay-2000"></div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md bg-white/70 backdrop-blur-2xl rounded-3xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.05)] border border-white/60 p-10 relative z-10"
      >
        <div className="flex flex-col items-center mb-10">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 2 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-white to-blue-50/50 shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-white flex items-center justify-center p-3"
          >
            <img src={logo} alt="AutoSen Logo" className="w-full h-full object-contain filter drop-shadow-sm" />
          </motion.div>
          <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight">AutoHao</h2>
          <p className="text-sm text-slate-500 mt-2 font-medium tracking-wide">智能化业务处理终端</p>
        </div>

        <form onSubmit={attemptLogin} className="space-y-6">
          <div className="space-y-5">
            <div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors group-focus-within:text-blue-500 text-slate-400">
                  <User className="h-5 w-5" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-12 pr-4 py-3.5 bg-slate-50/50 border border-slate-200/80 rounded-2xl text-slate-700 placeholder-slate-400 focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all duration-300 outline-none shadow-sm"
                  placeholder="用户账号"
                />
              </div>
            </div>

            <div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors group-focus-within:text-blue-500 text-slate-400">
                  <Lock className="h-5 w-5" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={handlePasswordChange}
                  style={{ imeMode: 'disabled' }}
                  className="block w-full pl-12 pr-4 py-3.5 bg-slate-50/50 border border-slate-200/80 rounded-2xl text-slate-700 placeholder-slate-400 focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all duration-300 outline-none shadow-sm"
                  placeholder="认证密钥"
                />
              </div>
            </div>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3.5 text-sm text-rose-600 bg-rose-50/80 border border-rose-100 rounded-2xl"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="font-medium">{error}</span>
            </motion.div>
          )}

          <button
            type="submit"
            className="group w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-semibold py-4 px-4 rounded-2xl shadow-[0_8px_20px_rgb(59,130,246,0.3)] hover:shadow-[0_12px_25px_rgb(59,130,246,0.4)] transition-all duration-300 active:scale-[0.98]"
          >
            <ShieldCheck className="w-5 h-5 transition-transform group-hover:scale-110" />
            <span className="tracking-widest">登录</span>
          </button>
        </form>

        <div className="mt-10 text-center">
          <p className="text-[11px] text-slate-400 font-medium tracking-wider">智能化业务处理终端 v1.0.5| ©系统组@2026</p>
        </div>
      </motion.div>
    </div>
  );
}
