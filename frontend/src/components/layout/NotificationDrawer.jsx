import React from 'react';
import { X, Bell, Trash2, AlertTriangle, UserCheck, ShieldAlert } from 'lucide-react';
import useWorkflowStore from '../../store/workflowStore';

export default function NotificationDrawer({ isOpen, onClose }) {
  const { notifications, markNotificationRead, clearNotifications } = useWorkflowStore();

  if (!isOpen) return null;

  const getIcon = (type) => {
    switch (type) {
      case 'escalation': return <ShieldAlert className="text-red-500" size={18} />;
      case 'task_assigned': return <UserCheck className="text-purple-500" size={18} />;
      case 'error': return <AlertTriangle className="text-orange-500" size={18} />;
      default: return <Bell className="text-blue-500" size={18} />;
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[200]" 
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 w-[400px] bg-[#FFFFFF] border-l border-[#E2E8F0] z-[201] shadow-2xl flex flex-col animate-slide-in-right">
        <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between bg-[#FFFFFF]">
          <div className="flex items-center gap-2">
            <Bell size={18} className="text-[#2563EB]" />
            <h2 className="font-mono text-sm font-bold text-[#0F172A]">SYSTEM NOTIFICATIONS</h2>
            <span className="bg-[#E2E8F0] text-[#475569] text-[10px] px-2 py-0.5 rounded-full">
              {notifications.filter(n => !n.read).length} NEW
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={clearNotifications}
              className="p-1.5 hover:bg-red-500/10 text-[#475569] hover:text-red-500 rounded-md transition-colors"
              title="Clear all"
            >
              <Trash2 size={16} />
            </button>
            <button 
              onClick={onClose}
              className="p-1.5 hover:bg-[#E2E8F0] text-[#475569] hover:text-[#0F172A] rounded-md transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
          {notifications.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-[#475569] opacity-50 space-y-4">
              <Bell size={48} strokeWidth={1} />
              <p className="font-mono text-xs uppercase tracking-widest">No active notifications</p>
            </div>
          ) : (
            notifications.map((n) => (
              <div 
                key={n.id}
                onClick={() => markNotificationRead(n.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer group ${
                  n.read 
                    ? 'bg-transparent border-[#E2E8F0] opacity-60' 
                    : 'bg-[#EFF6FF] border-[#2563EB]/40 shadow-sm'
                }`}
              >
                <div className="flex gap-3">
                  <div className={`p-2 rounded-lg ${n.read ? 'bg-[#E2E8F0]' : 'bg-[#2563EB]/10'}`}>
                    {getIcon(n.type)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold font-mono text-[#2563EB] uppercase tracking-tighter">
                        {n.agent || 'SYSTEM'}
                      </span>
                      <span className="text-[9px] text-[#475569]">
                        {new Date(n.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-xs text-[#0F172A] leading-relaxed">
                      {n.message}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        
        <div className="p-4 border-t border-[#E2E8F0] bg-[#FFFFFF]">
          <div className="text-[9px] font-mono text-[#475569] text-center">
            NEXUS // AUTONOMOUS NOTIFICATION ENGINE V1.0
          </div>
        </div>
      </div>
    </>
  );
}
