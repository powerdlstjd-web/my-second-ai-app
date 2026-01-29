
import React, { useState, useEffect, useRef } from 'react';
import { User, UserStatus, ChatMessage, StatusOption } from './types';
import { INITIAL_USERS, STATUS_OPTIONS } from './constants';
import { getTeamStatusSummary } from './geminiService';

// --- Sub-components ---

interface StatusCardProps {
  user: User;
  onAdminAction?: (type: 'SUPPORT' | 'INFO' | 'DELEGATE', target: User) => void;
  isAdmin: boolean;
}

const StatusCard: React.FC<StatusCardProps> = ({ user, onAdminAction, isAdmin }) => {
  const statusConfig = STATUS_OPTIONS.find(s => s.value === user.status);
  const isOnline = user.isLoggedIn;
  
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-4 transition-all hover:shadow-md hover:border-blue-200 relative group ${!isOnline ? 'opacity-60 grayscale-[0.5]' : ''}`}>
      <div className="flex items-center space-x-3">
        <div className="relative">
          <img src={user.avatar} alt={user.name} className="w-12 h-12 rounded-full border-2 border-slate-100 object-cover" />
          <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${isOnline ? (statusConfig?.color || 'bg-gray-400') : 'bg-gray-300'}`}></div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-semibold text-slate-800 truncate">{user.name}</h3>
            {user.role === 'ADMIN' && <span className="bg-indigo-100 text-indigo-700 text-[10px] px-1.5 py-0.5 rounded font-bold">ADMIN</span>}
          </div>
          <p className="text-xs text-slate-500 truncate">{user.position}</p>
        </div>
      </div>
      
      <div className="mt-4">
        <div className={`inline-flex items-center space-x-1.5 px-2 py-1 rounded-md ${isOnline ? (statusConfig?.color.replace('bg-', 'bg-opacity-10 text-').replace('-500', '-600') || 'bg-slate-100 text-slate-600') : 'bg-slate-100 text-slate-400'} text-[11px] font-medium`}>
          <i className={`fas ${statusConfig?.icon || 'fa-question'} text-[10px]`}></i>
          <span>{isOnline ? user.status : '부재중'}</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-2">마지막 업데이트: {user.lastUpdated}</p>
      </div>

      {isAdmin && isOnline && (
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
          {user.role !== 'ADMIN' && (
            <>
              <button onClick={() => onAdminAction?.('SUPPORT', user)} className="p-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors" title="상황 지원 요청"><i className="fas fa-bullhorn text-xs"></i></button>
              <button onClick={() => onAdminAction?.('INFO', user)} className="p-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors" title="내용 전달 요청"><i className="fas fa-file-export text-xs"></i></button>
              <button onClick={() => onAdminAction?.('DELEGATE', user)} className="p-1.5 bg-amber-50 text-amber-600 rounded-lg hover:bg-amber-100 transition-colors" title="관리자 권한 위임"><i className="fas fa-shield-alt text-xs"></i></button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [team, setTeam] = useState<User[]>(INITIAL_USERS);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [aiSummary, setAiSummary] = useState<string>('팀 상태를 분석 중입니다...');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isVoiceChatting, setIsVoiceChatting] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => scrollToBottom(), [messages]);

  const fetchSummary = async () => {
    setIsRefreshing(true);
    setAiSummary('팀 상태를 새로 분석 중입니다...');
    try {
      const activeTeam = team.filter(u => u.isLoggedIn);
      const summary = await getTeamStatusSummary(activeTeam.length > 0 ? activeTeam : team);
      setAiSummary(summary);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleLogin = (name: string) => {
    const user = team.find(u => u.name === name);
    if (user) {
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      const loggedInUser = { ...user, isLoggedIn: true, status: UserStatus.OFFICE, lastUpdated: timeStr };
      setTeam(prev => prev.map(u => u.id === user.id ? loggedInUser : u));
      setCurrentUser(loggedInUser);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        senderId: 'system',
        senderName: '시스템',
        content: `${name}님이 접속했습니다.`,
        timestamp: timeStr,
        type: 'TEXT'
      }]);
    } else {
      alert("등록되지 않은 팀원입니다.");
    }
  };

  const handleStatusChange = (newStatus: UserStatus) => {
    if (!currentUser) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    setTeam(prev => prev.map(u => u.id === currentUser.id ? { ...u, status: newStatus, lastUpdated: timeStr } : u));
    setCurrentUser(prev => prev ? ({ ...prev, status: newStatus, lastUpdated: timeStr }) : null);
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      senderId: 'system',
      senderName: '시스템',
      content: `${currentUser.name}님이 상태를 [${newStatus}]로 변경했습니다.`,
      timestamp: timeStr,
      type: 'TEXT'
    }]);
  };

  const sendMessage = (content: string, type: 'TEXT' | 'IMAGE' = 'TEXT', imageUrl?: string) => {
    if (!currentUser) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      senderId: currentUser.id,
      senderName: currentUser.name,
      content,
      timestamp: timeStr,
      type,
      imageUrl
    }]);
    setInputMessage('');
  };

  const handleAdminAction = (type: 'SUPPORT' | 'INFO' | 'DELEGATE', target: User) => {
    if (!currentUser) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    if (type === 'DELEGATE') {
      if (window.confirm(`${target.name}님에게 관리자 권한을 이양하시겠습니까?`)) {
        const newTeam = team.map(u => {
          if (u.id === currentUser.id) return { ...u, role: 'MEMBER' as const };
          if (u.id === target.id) return { ...u, role: 'ADMIN' as const };
          return u;
        });
        setTeam(newTeam);
        const updatedMe = newTeam.find(u => u.id === currentUser.id);
        if (updatedMe) setCurrentUser(updatedMe);
        setMessages(prev => [...prev, { id: Date.now().toString(), senderId: 'system', senderName: '시스템', content: `관리자 권한이 ${currentUser.name}님에서 ${target.name}님으로 이양되었습니다.`, timestamp: timeStr, type: 'TEXT' }]);
      }
      return;
    }
    const content = type === 'SUPPORT' ? `🚨 [상황 지원 요청] ${target.name}님, 즉시 해당 구역 지원 바랍니다.` : `📝 [내용 전달 요청] ${target.name}님, 진행 상황 보고 부탁드립니다.`;
    setMessages(prev => [...prev, { id: Date.now().toString(), senderId: currentUser.id, senderName: `${currentUser.name} (관리자)`, content, timestamp: timeStr, type: type === 'SUPPORT' ? 'ADMIN_REQUEST' : 'INFO_REQUEST', targetId: target.id }]);
  };

  const toggleCamera = async () => {
    if (!showCamera) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        setShowCamera(true);
        setTimeout(() => { if (videoRef.current) videoRef.current.srcObject = stream; }, 100);
      } catch (e) { alert("카메라 접근 권한이 필요합니다."); }
    } else {
      const stream = videoRef.current?.srcObject as MediaStream;
      stream?.getTracks().forEach(track => track.stop());
      setShowCamera(false);
    }
  };

  const takePhoto = () => {
    const canvas = document.createElement('canvas');
    if (videoRef.current) {
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0);
      const dataUrl = canvas.toDataURL('image/png');
      sendMessage("현장 사진을 전송했습니다.", "IMAGE", dataUrl);
      toggleCamera();
    }
  };

  const toggleVoiceChat = async () => {
    if (!isVoiceChatting) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsVoiceChatting(true);
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        setMessages(prev => [...prev, { id: Date.now().toString(), senderId: 'system', senderName: '시스템', content: `${currentUser?.name}님이 팀 보이스 채널에 입장했습니다.`, timestamp: timeStr, type: 'TEXT' }]);
      } catch (e) { alert("마이크 접근 권한이 필요합니다."); }
    } else {
      setIsVoiceChatting(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) sendMessage(`파일 업로드: ${file.name}`, "IMAGE", event.target.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  if (!currentUser) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-slate-900 px-6">
        <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl p-8 animate-in fade-in zoom-in duration-300">
          <div className="text-center mb-10">
            <div className="w-20 h-20 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <i className="fas fa-users-gear text-white text-3xl"></i>
            </div>
            <h1 className="text-2xl font-black text-slate-800">TeamSync Pro</h1>
            <p className="text-sm text-slate-500 mt-1">팀 메신저에 오신 것을 환영합니다</p>
          </div>
          <div className="space-y-4">
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">팀원 이름 선택</label>
            <div className="grid grid-cols-2 gap-3">
              {team.map(u => (
                <button 
                  key={u.id} 
                  onClick={() => handleLogin(u.name)}
                  className="flex items-center space-x-3 p-3 border border-slate-100 rounded-xl hover:border-indigo-600 hover:bg-indigo-50 transition-all text-left group"
                >
                  <img src={u.avatar} className="w-8 h-8 rounded-full border border-slate-200" alt="" />
                  <span className="text-xs font-bold text-slate-700 group-hover:text-indigo-700">{u.name}</span>
                </button>
              ))}
            </div>
          </div>
          <p className="mt-8 text-center text-[10px] text-slate-400 italic">로그인하지 않은 팀원은 '부재중'으로 표시됩니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row h-screen w-full bg-slate-50 overflow-hidden">
      <div className="w-full lg:w-72 bg-white border-b lg:border-r border-slate-200 flex flex-col shrink-0">
        <div className="p-6 border-b border-slate-100 bg-gradient-to-br from-indigo-600 to-blue-700 text-white">
          <div className="flex items-center space-x-3 mb-6">
            <img src={currentUser.avatar} alt="Me" className="w-12 h-12 rounded-full ring-2 ring-white/30 object-cover" />
            <div className="min-w-0">
              <p className="text-sm font-bold truncate">{currentUser.name}</p>
              <p className="text-[10px] text-blue-100 uppercase tracking-wider">{currentUser.role === 'ADMIN' ? 'Administrator' : 'Team Member'}</p>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] text-blue-100 mb-2 font-medium opacity-80">내 상태 변경</p>
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-2">
              {STATUS_OPTIONS.filter(o => o.value !== UserStatus.ABSENT).map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleStatusChange(opt.value)}
                  className={`flex items-center space-x-3 w-full p-2.5 rounded-lg text-[11px] font-medium transition-all ${
                    currentUser.status === opt.value ? 'bg-white text-blue-700 shadow-sm' : 'bg-white/10 hover:bg-white/20 text-white'
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full ${opt.color} ${currentUser.status === opt.value ? 'animate-pulse' : ''}`}></div>
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">오늘의 팀 브리핑 (AI)</h4>
            <button onClick={fetchSummary} disabled={isRefreshing} className={`text-slate-400 hover:text-blue-600 transition-all ${isRefreshing ? 'animate-spin' : ''}`}><i className="fas fa-sync-alt text-[10px]"></i></button>
          </div>
          <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100/50">
            <p className="text-xs text-slate-600 leading-relaxed italic">"{aiSummary}"</p>
          </div>
          {isVoiceChatting && (
            <div className="mt-6 p-4 bg-green-50 rounded-xl border border-green-200 animate-pulse">
              <div className="flex items-center space-x-2 text-green-700">
                <i className="fas fa-headset text-sm"></i>
                <span className="text-[11px] font-bold">팀 보이스 채팅 중...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
          <h1 className="text-lg font-bold text-slate-800">TeamSync <span className="text-blue-600 font-normal">Pro</span></h1>
          <div className="flex items-center space-x-4">
            <button onClick={() => setCurrentUser(null)} className="text-xs text-red-500 font-bold hover:underline">로그아웃</button>
            <div className="h-4 w-px bg-slate-200"></div>
            <div className="flex -space-x-2">
              {team.filter(u => u.isLoggedIn).map(u => <img key={u.id} src={u.avatar} className="w-6 h-6 rounded-full border-2 border-white object-cover" alt="" />)}
            </div>
          </div>
        </header>

        <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
            <h2 className="text-sm font-bold text-slate-800 mb-4">실시간 팀원 현황</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {team.map(user => <StatusCard key={user.id} user={user} isAdmin={currentUser.role === 'ADMIN'} onAdminAction={handleAdminAction} />)}
            </div>
          </div>

          <div className="w-full lg:w-96 bg-white border-l border-slate-200 flex flex-col shrink-0 relative">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">상황 공유 채팅</h3>
              <span className="bg-green-100 text-green-700 text-[10px] px-2 py-0.5 rounded-full font-bold">LIVE</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-50/30">
              {messages.map((msg) => {
                const isMe = msg.senderId === currentUser.id;
                const isSystem = msg.senderId === 'system';
                if (isSystem) return <div key={msg.id} className="flex justify-center"><span className="bg-slate-200 text-slate-500 text-[9px] px-3 py-1 rounded-full">{msg.content}</span></div>;
                return (
                  <div key={msg.id} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
                    <div className="flex items-center space-x-2 mb-1 px-1">
                      {!isMe && <span className="text-[10px] font-bold text-slate-600">{msg.senderName}</span>}
                      <span className="text-[9px] text-slate-400">{msg.timestamp}</span>
                    </div>
                    {msg.imageUrl && <img src={msg.imageUrl} className="max-w-[80%] rounded-lg mb-2 shadow-sm border border-slate-200" alt="uploaded" />}
                    <div className={`max-w-[90%] p-3 rounded-2xl text-xs leading-relaxed shadow-sm ${msg.type.includes('REQUEST') ? 'bg-red-600 text-white font-bold animate-pulse' : isMe ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white text-slate-700 border border-slate-200 rounded-tl-none'}`}>{msg.content}</div>
                  </div>
                );
              })}
              <div ref={chatEndRef} />
            </div>

            <div className="p-4 bg-white border-t border-slate-100">
              <form onSubmit={(e) => { e.preventDefault(); sendMessage(inputMessage); }} className="relative mb-3">
                <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} placeholder="상황 공유 메시지 입력..." className="w-full bg-slate-100 border-none rounded-2xl px-4 py-3 pr-12 text-sm focus:ring-2 focus:ring-blue-500 transition-all outline-none" />
                <button type="submit" disabled={!inputMessage.trim()} className="absolute right-2 top-1.5 w-9 h-9 bg-blue-600 text-white rounded-xl flex items-center justify-center disabled:bg-slate-300"><i className="fas fa-paper-plane text-sm"></i></button>
              </form>
              <div className="flex items-center space-x-5 px-1">
                <button onClick={toggleCamera} className={`text-lg transition-colors ${showCamera ? 'text-red-500' : 'text-slate-400 hover:text-blue-600'}`} title="카메라 연동"><i className="fas fa-camera"></i></button>
                <button onClick={toggleVoiceChat} className={`text-lg transition-colors ${isVoiceChatting ? 'text-green-500' : 'text-slate-400 hover:text-blue-600'}`} title="팀 보이스"><i className="fas fa-microphone"></i></button>
                <button onClick={() => fileInputRef.current?.click()} className="text-lg text-slate-400 hover:text-blue-600 transition-colors" title="사진 업로드"><i className="fas fa-image"></i></button>
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*" className="hidden" />
              </div>
            </div>

            {showCamera && (
              <div className="absolute inset-0 bg-black/90 z-20 flex flex-col items-center justify-center p-6">
                <video ref={videoRef} autoPlay playsInline className="w-full max-h-[70%] rounded-2xl shadow-2xl bg-slate-800 object-cover" />
                <div className="mt-8 flex space-x-6">
                  <button onClick={takePhoto} className="w-16 h-16 bg-white rounded-full border-4 border-slate-300 active:scale-95 transition-transform" />
                  <button onClick={toggleCamera} className="w-16 h-16 bg-red-500 text-white rounded-full flex items-center justify-center"><i className="fas fa-times text-2xl"></i></button>
                </div>
                <p className="mt-4 text-white/50 text-xs">사진을 찍어 현장 상황을 공유하세요</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
