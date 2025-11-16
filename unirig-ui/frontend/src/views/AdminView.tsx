import React from 'react';
import { DatasetStatusPanel } from '../components/Admin';

/**
 * Admin view containing system administration panels
 */
export const AdminView: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Administration</h1>
        <p className="text-gray-600 mt-2">
          Manage system resources and monitor infrastructure status
        </p>
      </div>

      <div className="space-y-6">
        {/* Motion Dataset Status Panel */}
        <DatasetStatusPanel />
      </div>
    </div>
  );
};
