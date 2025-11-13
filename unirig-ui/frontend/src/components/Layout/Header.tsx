import React from 'react';

interface HeaderProps {
  currentView: 'upload' | 'jobs' | 'settings';
  onNavigate: (view: 'upload' | 'jobs' | 'settings') => void;
}

/**
 * Application header with navigation
 */
export const Header: React.FC<HeaderProps> = ({ currentView, onNavigate }) => {
  const navItems = [
    { id: 'upload' as const, label: 'Upload', icon: '📤' },
    { id: 'jobs' as const, label: 'Jobs', icon: '📋' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
  ];

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="text-3xl">🦴</div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">UniRig</h1>
              <p className="text-xs text-gray-500">Automatic 3D Model Rigging</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`
                  px-4 py-2 rounded-md transition-colors font-medium text-sm
                  flex items-center gap-2
                  ${
                    currentView === item.id
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-gray-700 hover:bg-gray-100'
                  }
                `}
                aria-current={currentView === item.id ? 'page' : undefined}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};
